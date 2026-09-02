"""Tests for account security endpoints."""

import pytest
from apps.accounts.models_reset import PasswordResetToken
from apps.accounts.models_session import SessionDevice
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status

User = get_user_model()
PASSWORD = "Str0ng-Passw0rd!"
WEAK_PASSWORD = "password"


def test_change_password_success(api_client, user_factory):
    user = user_factory(password=PASSWORD)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": PASSWORD,
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert user.check_password("NewStr0ngPass!")


def test_change_password_wrong_current(api_client, user_factory):
    user = user_factory(password=PASSWORD)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": "wrong",
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_change_password_weak_new(api_client, user_factory):
    user = user_factory(password=PASSWORD)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": PASSWORD,
            "new_password": WEAK_PASSWORD,
            "confirm_password": WEAK_PASSWORD,
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_change_password_mismatch(api_client, user_factory):
    user = user_factory(password=PASSWORD)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": PASSWORD,
            "new_password": "NewPass123!",
            "confirm_password": "Different1!",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_forgot_password_sends_email(api_client, user_factory):
    user = user_factory()
    resp = api_client.post(
        "/api/v1/auth/forgot-password/",
        {"email": user.email},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to


def test_forgot_password_enumeration_safe(api_client):
    resp = api_client.post(
        "/api/v1/auth/forgot-password/",
        {"email": "nobody@example.com"},
    )
    assert resp.status_code == status.HTTP_200_OK
    detail = resp.data.get("detail", "")
    assert "if" in detail.lower() or "sent" in detail.lower()


def test_reset_password_valid_token(api_client, user_factory):
    user = user_factory()
    token, raw = PasswordResetToken.create(user)
    resp = api_client.post(
        f"/api/v1/auth/reset-password/{token.id}/",
        {
            "token_id": str(token.id),
            "token": raw,
            "new_password": "NewResetPass1!",
            "confirm_password": "NewResetPass1!",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    token.user.refresh_from_db()
    assert token.user.check_password("NewResetPass1!")


def test_reset_password_invalid_token(api_client, user_factory):
    user = user_factory()
    resp = api_client.post(
        f"/api/v1/auth/reset-password/{user.id}/",
        {
            "token_id": str(user.id),
            "token": "bad-token",
            "new_password": "NewResetPass1!",
            "confirm_password": "NewResetPass1!",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_reset_password_expired_token(api_client, user_factory, monkeypatch):
    import datetime

    user = user_factory()
    token, raw = PasswordResetToken.create(user)
    token.expires_at = token.created_at - datetime.timedelta(hours=1)
    token.save(update_fields=["expires_at"])
    resp = api_client.post(
        f"/api/v1/auth/reset-password/{token.id}/",
        {
            "token_id": str(token.id),
            "token": raw,
            "new_password": "NewResetPass1!",
            "confirm_password": "NewResetPass1!",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_verify_email(api_client, user_factory):
    user = user_factory(is_email_verified=False)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post("/api/v1/auth/verify-email/")
    assert resp.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.is_email_verified


def test_sessions_list(api_client, user_factory):
    user = user_factory()
    SessionDevice.objects.create(
        user=user,
        token_id=user.id,
        is_current=True,
    )
    SessionDevice.objects.create(user=user, token_id=user.id)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.get("/api/v1/auth/sessions/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data["results"]) == 2


def test_session_revoke(api_client, user_factory):
    user = user_factory()
    s1 = SessionDevice.objects.create(
        user=user,
        token_id=user.id,
        is_current=True,
    )
    s2 = SessionDevice.objects.create(user=user, token_id=user.id)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(f"/api/v1/auth/sessions/{s2.id}/revoke/")
    assert resp.status_code == status.HTTP_200_OK
    assert SessionDevice.objects.filter(id=s2.id).count() == 0
    assert SessionDevice.objects.filter(id=s1.id).count() == 1


def test_session_revoke_others(api_client, user_factory):
    user = user_factory()
    SessionDevice.objects.create(
        user=user,
        token_id=user.id,
        is_current=True,
    )
    SessionDevice.objects.create(user=user, token_id=user.id)
    SessionDevice.objects.create(user=user, token_id=user.id)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post("/api/v1/auth/sessions/revoke-others/")
    assert resp.status_code == status.HTTP_200_OK
    assert SessionDevice.objects.filter(user=user).count() == 1


def test_profile_update_name(api_client, user_factory):
    user = user_factory(first_name="John", last_name="Doe")
    client = api_client
    client.force_authenticate(user=user)
    resp = client.patch(
        "/api/v1/auth/me/",
        {"first_name": "Jane", "last_name": "Smith"},
    )
    assert resp.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"


def test_login_creates_session_device(api_client, user_factory):
    password = "Str0ng-Passw0rd!"
    user = user_factory(email="login@acme.test", password=password)
    resp = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": password},
        HTTP_USER_AGENT="TestBrowser/1.0",
    )
    assert resp.status_code == status.HTTP_200_OK
    session = SessionDevice.objects.filter(user=user).first()
    assert session is not None
    assert session.is_current is True
    assert session.refresh_token
    assert session.token_id is not None


@pytest.mark.django_db
def test_register_creates_session_device(api_client):
    resp = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "new@acme.test",
            "password": "Str0ng-Passw0rd!",
            "first_name": "New",
            "last_name": "User",
            "company_name": "New Co",
        },
        HTTP_USER_AGENT="TestBrowser/1.0",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email="new@acme.test")
    session = SessionDevice.objects.filter(user=user).first()
    assert session is not None
    assert session.refresh_token


def test_session_revoke_blacklists_jwt(api_client, user_factory):
    """Revoking a session must invalidate its refresh token for renewal."""
    from rest_framework_simplejwt.tokens import RefreshToken

    user = user_factory(email="rev@acme.test")
    refresh = RefreshToken.for_user(user)
    session = SessionDevice.objects.create(
        user=user,
        token_id=refresh["jti"],
        refresh_token=str(refresh),
        is_current=True,
    )
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(f"/api/v1/auth/sessions/{session.id}/revoke/")
    assert resp.status_code == status.HTTP_200_OK
    assert SessionDevice.objects.filter(id=session.id).count() == 0
    # The refresh token backing the revoked session must be blacklisted.
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()


def test_change_password_blacklists_all_tokens(api_client, user_factory):
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    from rest_framework_simplejwt.tokens import RefreshToken

    user = user_factory(email="pw@acme.test", password="Str0ng-Passw0rd!")
    r1 = RefreshToken.for_user(user)
    r2 = RefreshToken.for_user(user)
    client = api_client
    client.force_authenticate(user=user)
    resp = client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": "Str0ng-Passw0rd!",
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    # Both outstanding tokens should now be blacklisted.
    for r in (r1, r2):
        assert BlacklistedToken.objects.filter(token__jti=r["jti"]).exists()
    # All SessionDevices removed.
    assert SessionDevice.objects.filter(user=user).count() == 0


def test_reset_password_blacklists_all_tokens(api_client, user_factory):
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    from rest_framework_simplejwt.tokens import RefreshToken

    user = user_factory(email="reset2@acme.test")
    refresh = RefreshToken.for_user(user)
    token, raw = PasswordResetToken.create(user)
    resp = api_client.post(
        f"/api/v1/auth/reset-password/{token.id}/",
        {
            "token_id": str(token.id),
            "token": raw,
            "new_password": "NewResetPass1!",
            "confirm_password": "NewResetPass1!",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()
    assert SessionDevice.objects.filter(user=user).count() == 0
