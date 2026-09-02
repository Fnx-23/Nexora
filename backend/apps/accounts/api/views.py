"""Authentication and account API views."""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.accounts.api.serializers import (
    AvatarUpdateSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MeSerializer,
    RegisterInputSerializer,
    RegisterResponseSerializer,
)
from apps.accounts.models_security import SecurityEventType
from apps.accounts.services import register_company
from apps.accounts.services_security import (
    create_session_device,
    record_profile_update,
    record_security_event,
    update_session_device,
)
from apps.core.api.context import apply_company_context
from apps.core.api.throttling import LoginThrottle, RefreshThrottle, RegisterThrottle
from apps.core.exceptions import ApplicationError

User = get_user_model()

REGISTRATION_FAILED_DETAIL = "Registration could not be completed with the provided details."


class LoginView(APIView):
    """Obtain a JWT pair plus basic profile data (email + password)."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            valid = serializer.is_valid()
        except AuthenticationFailed:
            email = (request.data.get("email") or "").strip().lower()
            user = User.objects.filter(email__iexact=email).first() or request.user
            record_security_event(
                user,
                SecurityEventType.LOGIN_FAILED,
                request=request,
                metadata={"reason": "invalid_credentials"},
            )
            raise
        if not valid:
            email = (request.data.get("email") or "").strip().lower()
            user = User.objects.filter(email__iexact=email).first() or request.user
            record_security_event(
                user,
                SecurityEventType.LOGIN_FAILED,
                request=request,
                metadata={"reason": "invalid_credentials"},
            )
            raise serializers.ValidationError(serializer.errors)
        data = serializer.validated_data
        create_session_device(serializer.user, request, data["refresh"])
        record_security_event(serializer.user, SecurityEventType.LOGIN, request=request)
        return Response(data)


class RefreshView(TokenRefreshView):
    """Exchange a refresh token for a new token pair.

    When ``ROTATE_REFRESH_TOKENS`` is enabled, the old refresh token is
    blacklisted and a new one is issued.  We update the ``SessionDevice``
    record to track the new refresh token so the session remains visible
    in the sessions UI and can be revoked later.
    """

    throttle_classes = [RefreshThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != 200:
            return response

        new_refresh_str = response.data.get("refresh")
        old_refresh_str = request.data.get("refresh")
        if not new_refresh_str:
            return response

        from apps.accounts.models_session import SessionDevice

        old_jti = None
        if old_refresh_str:
            try:
                old_jti = RefreshToken(old_refresh_str)["jti"]
            except Exception:
                old_jti = None

        if old_jti:
            old_session = SessionDevice.objects.filter(token_id=old_jti).first()
            if old_session:
                update_session_device(old_session, request, new_refresh_str)
                return response

        try:
            user = User.objects.get(pk=RefreshToken(new_refresh_str)["user_id"])
        except Exception:
            user = None
        if user is not None:
            existing = SessionDevice.objects.filter(user=user, is_current=True).first()
            if existing:
                update_session_device(existing, request, new_refresh_str)
            else:
                create_session_device(user, request, new_refresh_str)

        return response


class VerifyView(TokenVerifyView):
    """Verify that an access token is valid."""


class RegisterView(APIView):
    """
    Create a new user together with their own company.

    The caller becomes the company's first ADMIN member and receives a JWT
    session in return. This is the tenant bootstrap endpoint.
    """

    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @extend_schema(
        request=RegisterInputSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    )
    def post(self, request):
        input_serializer = RegisterInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            result = register_company(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                company_name=data["company_name"],
            )
        except ApplicationError:
            return Response(
                {"detail": REGISTRATION_FAILED_DETAIL}, status=status.HTTP_400_BAD_REQUEST
            )

        refresh = RefreshToken.for_user(result.user)
        response_serializer = RegisterResponseSerializer(
            {
                "user": result.user,
                "company": result.company,
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            },
            context={"request": request},
        )

        create_session_device(result.user, request, str(refresh))
        record_security_event(result.user, SecurityEventType.LOGIN, request=request)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MeView(RetrieveUpdateAPIView):
    """
    Profile of the authenticated user within their active company context.

    GET is available to any authenticated user; `active_company` is null when
    the user holds no membership yet. PATCH accepts an avatar upload and
    returns the full updated profile.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get(self, request, *args, **kwargs):
        apply_company_context(request)
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return AvatarUpdateSerializer
        return MeSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        request=AvatarUpdateSerializer,
        responses={200: MeSerializer, 400: OpenApiResponse(description="Validation error")},
    )
    def partial_update(self, request, *args, **kwargs):
        """Avatar-only profile mutation; answers with the full profile shape."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        record_profile_update(instance)
        record_security_event(
            request.user,
            SecurityEventType.PROFILE_UPDATED,
            request=request,
        )

        response_serializer = MeSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)
