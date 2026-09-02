"""Services for account security operations."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models_reset import PasswordResetToken
from apps.accounts.models_security import SecurityEvent, SecurityEventType
from apps.accounts.models_session import SessionDevice
from apps.activities.models import ActivityAction
from apps.activities.services import record_activity

logger = logging.getLogger("apps.accounts")
User = get_user_model()


def _get_client_info(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua or None


def record_security_event(user, event_type: SecurityEventType, request=None, metadata=None):
    """Append a user-scoped security event (the Settings > Security log).

    ``request`` is optional; when provided the client's IP and user agent are
    captured for display in the security feed. The log is both append-only and
    write-only through this service — there is no update or delete path.
    """
    ip, ua = _get_client_info(request) if request is not None else (None, None)
    if not isinstance(user, get_user_model()):
        return
    SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip,
        user_agent=ua or "",
        metadata=metadata or {},
    )


def _get_security_company(user):
    """Return the user's first active company for security activity logging.

    Security events (password change, session revoke, …) are user-global but
    the activity log is company-scoped.  We pick the first active company so
    the event appears in the company's audit feed.  Returns ``None`` if the
    user has no membership (caller should skip logging).
    """
    membership = user.memberships.filter(is_active=True, company__is_active=True).first()
    return membership.company if membership else None


def _record_security_activity(action, user, metadata=None):
    """Record a security activity with user's company context."""
    company = _get_security_company(user)
    if company is None:
        logger.debug("No company for user %s; skipping activity %s", user.id, action)
        return None
    return record_activity(
        action=action,
        company=company,
        actor=user,
        entity=user,
        entity_type="user",
        metadata=metadata or {},
    )


def _blacklist_refresh_token_string(raw_token: str) -> bool:
    """Reconstruct a RefreshToken from its serialized form and blacklist it.

    Returns ``True`` if the token was successfully blacklisted.
    """
    try:
        refresh = RefreshToken(raw_token)
        refresh.blacklist()
        return True
    except Exception:
        logger.debug("Could not blacklist refresh token (may already be expired)")
        return False


def _blacklist_all_user_tokens(user) -> int:
    """Blacklist every outstanding refresh token for *user*.

    Returns the number of tokens blacklisted.
    """
    outstanding = OutstandingToken.objects.filter(user=user)
    count = 0
    for token in outstanding:
        try:
            BlacklistedToken.objects.get_or_create(token=token)
            count += 1
        except Exception:
            logger.debug("Could not blacklist token %s", token.jti)
    return count


def create_session_device(user, request, refresh_token: str) -> SessionDevice:
    """Create a SessionDevice record after a successful login/register/refresh.

    ``refresh_token`` is the serialized ``RefreshToken`` string (the raw JWT).
    The ``jti`` claim is extracted and stored for display and lookup purposes.
    """
    ip, ua = _get_client_info(request)
    try:
        payload = RefreshToken(refresh_token)
        token_id = payload["jti"]
    except Exception:
        token_id = None

    SessionDevice.objects.filter(user=user, is_current=True).update(is_current=False)

    return SessionDevice.objects.create(
        user=user,
        token_id=token_id,
        refresh_token=refresh_token,
        ip_address=ip,
        user_agent=ua or "",
        is_current=True,
    )


def update_session_device(session: SessionDevice, request, new_refresh_token: str) -> None:
    """Update a SessionDevice after a token refresh (rotated token)."""
    ip, ua = _get_client_info(request)
    try:
        new_jti = RefreshToken(new_refresh_token)["jti"]
    except Exception:
        new_jti = session.token_id
    session.token_id = new_jti
    session.refresh_token = new_refresh_token
    session.ip_address = ip
    if ua:
        session.user_agent = ua
    session.save(update_fields=["token_id", "refresh_token", "ip_address", "user_agent"])


def _blacklist_session_token(session: SessionDevice) -> bool:
    """Blacklist the refresh token backing a SessionDevice, if stored."""
    if session.refresh_token:
        return _blacklist_refresh_token_string(session.refresh_token)
    return False


def change_password(user, current_password: str, new_password: str) -> None:
    if not user.check_password(current_password):
        raise ValueError("Current password is incorrect.")
    password_validation.validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password"])

    _blacklist_all_user_tokens(user)
    SessionDevice.objects.filter(user=user).delete()

    _record_security_activity(
        ActivityAction.PASSWORD_CHANGED,
        user,
        metadata={"user_id": str(user.id)},
    )


def forgot_password(email: str) -> tuple[PasswordResetToken | None, str]:
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None, "If an account with that email exists, a reset link has been sent."

    token, raw = PasswordResetToken.create(user)
    reset_link = f"{settings.SITE_URL}/reset-password/{token.id}/?token={raw}"
    subject = "Nexora Password Reset"
    html = render_to_string("accounts/email_reset.html", {"reset_link": reset_link})
    plain = strip_tags(html)
    try:
        send_mail(
            subject,
            plain,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html,
        )
        return token, "If an account with that email exists, a reset link has been sent."
    except Exception:
        logger.exception("Failed to send password reset email to %s", user.email)
        return token, "If an account with that email exists, a reset link has been sent."


def reset_password(token_id, raw_token: str, new_password: str) -> bool:
    try:
        uid = str(token_id)
    except (ValueError, TypeError):
        return False
    token = PasswordResetToken.objects.filter(id=uid).first()
    if token is None or not token.is_valid():
        return False
    consumed = PasswordResetToken.consume(token.user, raw_token)
    if consumed is None:
        return False
    password_validation.validate_password(new_password, token.user)
    token.user.set_password(new_password)
    token.user.save(update_fields=["password"])
    token.mark_used()

    _blacklist_all_user_tokens(token.user)
    SessionDevice.objects.filter(user=token.user).delete()

    _record_security_activity(
        ActivityAction.PASSWORD_RESET,
        token.user,
        metadata={"user_id": str(token.user.id)},
    )
    return True


def verify_email(user) -> None:
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])
    _record_security_activity(
        ActivityAction.EMAIL_VERIFIED,
        user,
        metadata={"user_id": str(user.id)},
    )


def record_profile_update(user) -> None:
    """Record a profile update activity (called after MeView PATCH)."""
    _record_security_activity(
        ActivityAction.PROFILE_UPDATED,
        user,
        metadata={"user_id": str(user.id)},
    )


def revoke_session(user, session_id) -> bool:
    try:
        session = SessionDevice.objects.get(id=session_id, user=user)
    except SessionDevice.DoesNotExist:
        return False
    _blacklist_session_token(session)
    session.delete()
    _record_security_activity(
        ActivityAction.SESSION_REVOKED,
        user,
        metadata={"session_id": str(session_id)},
    )
    return True


def revoke_all_other_sessions(user) -> int:
    current = SessionDevice.objects.filter(user=user, is_current=True).first()
    others = SessionDevice.objects.filter(user=user)
    if current:
        others = others.exclude(id=current.id)
    sessions = list(others)
    for session in sessions:
        _blacklist_session_token(session)
    count = len(sessions)
    if count > 0:
        others.delete()
        _record_security_activity(
            ActivityAction.SESSIONS_REVOKED_OTHERS,
            user,
            metadata={"count": count},
        )
    return count
