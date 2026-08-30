"""Authentication and account API views."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
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
from apps.accounts.services import register_company
from apps.core.api.context import apply_company_context
from apps.core.api.throttling import LoginThrottle, RefreshThrottle, RegisterThrottle
from apps.core.exceptions import ApplicationError

# Uniform failure body for registration: never reveals whether an email is
# already taken. Field-level errors for input quality (e.g. weak password)
# still surface normally through serializer validation.
REGISTRATION_FAILED_DETAIL = "Registration could not be completed with the provided details."


class LoginView(APIView):
    """Obtain a JWT pair plus basic profile data (email + password)."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class RefreshView(TokenRefreshView):
    """Exchange a refresh token for a new token pair."""

    throttle_classes = [RefreshThrottle]


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
            # Deliberately uniform: service-level failures (duplicate email,
            # slug races) must not leak which condition occurred.
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
        # Resolve the tenant context even though membership is not required.
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

        response_serializer = MeSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)
