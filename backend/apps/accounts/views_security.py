"""API views for account security operations."""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models_security import SecurityEvent, SecurityEventType
from apps.accounts.models_session import SessionDevice
from apps.accounts.serializers_security import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    SecurityEventSerializer,
    SessionDeviceSerializer,
)
from apps.accounts.services_security import (
    change_password,
    forgot_password,
    record_security_event,
    reset_password,
    revoke_all_other_sessions,
    revoke_session,
    verify_email,
)
from apps.core.api.throttling import LoginThrottle

logger = logging.getLogger("apps.accounts")


class ChangePasswordView(APIView):
    """Authenticated user changes their own password."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: "Password changed"},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            change_password(
                request.user,
                serializer.validated_data["current_password"],
                serializer.validated_data["new_password"],
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        record_security_event(
            request.user,
            SecurityEventType.PASSWORD_CHANGED,
            request=request,
        )
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    """Send a password-reset email (enumeration-safe)."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={200: "Message sent"},
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            _, message = forgot_password(serializer.validated_data["email"])
        except Exception:
            logger.exception("Forgot password error")
            message = "If an account with that email exists, a reset link has been sent."
        return Response({"detail": message}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """Reset password using a one-time token."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: "Password reset"},
    )
    def post(self, request, token_id):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            success = reset_password(data["token_id"], data["token"], data["new_password"])
        except Exception:
            logger.exception("Reset password error")
            success = False
        if not success:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """Mark the current user's email as verified."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: "Email verified"})
    def post(self, request):
        verify_email(request.user)
        record_security_event(
            request.user,
            SecurityEventType.EMAIL_VERIFIED,
            request=request,
        )
        return Response({"detail": "Email verified."}, status=status.HTTP_200_OK)


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """List active sessions for the current user."""

    permission_classes = [IsAuthenticated]
    serializer_class = SessionDeviceSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SessionDevice.objects.none()
        return SessionDevice.objects.filter(user=self.request.user)

    @extend_schema(responses={200: SessionDeviceSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(description="Revoke a single session by ID.")
    def revoke(self, request, pk=None):
        success = revoke_session(request.user, pk)
        if not success:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        record_security_event(
            request.user,
            SecurityEventType.SESSION_REVOKED,
            request=request,
            metadata={"session_id": str(pk)},
        )
        return Response(
            {"detail": "Session revoked."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(description="Logout all other sessions.")
    def revoke_others(self, request):
        count = revoke_all_other_sessions(request.user)
        record_security_event(
            request.user,
            SecurityEventType.SESSIONS_REVOKED_OTHERS,
            request=request,
            metadata={"count": count},
        )
        return Response(
            {"detail": f"Revoked {count} other session(s)."},
            status=status.HTTP_200_OK,
        )


class SecurityEventListView(ListAPIView):
    """List the current user's security events (login / password / session)."""

    permission_classes = [IsAuthenticated]
    serializer_class = SecurityEventSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SecurityEvent.objects.none()
        return SecurityEvent.objects.filter(user=self.request.user)

    @extend_schema(
        responses={200: SecurityEventSerializer(many=True)},
        description="Paginated security activity log for the current user.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
