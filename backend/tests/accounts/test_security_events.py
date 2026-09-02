"""Security activity feed tests for the Settings > Security page.

Covers recording on real auth flows, user ownership isolation, immutability,
and the read-only list endpoint.
"""

import pytest
from apps.accounts.models_security import SecurityEvent, SecurityEventType
from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Str0ng-Passw0rd!"

SECURITY_URL = "/api/v1/auth/security-events/"
ME_URL = "/api/v1/auth/me/"


def _event_types(user):
    return list(
        SecurityEvent.objects.filter(user=user)
        .order_by("created_at")
        .values_list("event_type", flat=True)
    )


@pytest.mark.django_db
def test_login_is_recorded(api_client, user_factory):
    user = user_factory(password=PASSWORD)

    resp = api_client.post(
        "/api/v1/auth/token/", {"email": user.email, "password": PASSWORD}, format="json"
    )
    assert resp.status_code == 200

    events = _event_types(user)
    assert SecurityEventType.LOGIN in events


@pytest.mark.django_db
def test_failed_login_is_recorded_with_reason(api_client, user_factory):
    user = user_factory(password=PASSWORD)

    resp = api_client.post(
        "/api/v1/auth/token/", {"email": user.email, "password": "wrong-password"}, format="json"
    )
    assert resp.status_code == 401

    event = SecurityEvent.objects.filter(
        user=user, event_type=SecurityEventType.LOGIN_FAILED
    ).first()
    assert event is not None
    assert event.metadata.get("reason") == "invalid_credentials"


@pytest.mark.django_db
def test_password_change_is_recorded(api_client, user_factory):
    user = user_factory(password=PASSWORD)
    api_client.force_authenticate(user=user)
    api_client.post(
        "/api/v1/auth/change-password/",
        {
            "current_password": PASSWORD,
            "new_password": "NewStr0ngPass!",
            "confirm_password": "NewStr0ngPass!",
        },
    )

    events = _event_types(user)
    assert SecurityEventType.PASSWORD_CHANGED in events


@pytest.mark.django_db
def test_email_verification_is_recorded(api_client, user_factory):
    user = user_factory(email="verify@acme.test", is_email_verified=False)
    api_client.force_authenticate(user=user)
    resp = api_client.post("/api/v1/auth/verify-email/")
    assert resp.status_code == 200

    events = _event_types(user)
    assert SecurityEventType.EMAIL_VERIFIED in events


@pytest.mark.django_db
def test_session_revoked_others_is_recorded(auth_client, tenant):
    client = auth_client(tenant.employee, tenant.company)
    login = client.post(
        "/api/v1/auth/token/",
        {"email": tenant.employee.email, "password": PASSWORD},
        format="json",
    )
    assert login.status_code == 200
    client.post("/api/v1/auth/sessions/revoke-others/")

    events = _event_types(tenant.employee)
    assert SecurityEventType.SESSIONS_REVOKED_OTHERS in events


@pytest.mark.django_db
def test_security_events_are_owned_by_user(auth_client, tenant, user_factory):
    outsider = user_factory(email="outsider@acme.test")
    SecurityEvent.objects.create(user=outsider, event_type=SecurityEventType.LOGIN)

    client = auth_client(tenant.employee, tenant.company)
    resp = client.get(SECURITY_URL)

    assert resp.status_code == 200
    for event in resp.json()["results"]:
        assert event["user"] == str(tenant.employee.id)


@pytest.mark.django_db
def test_events_are_append_only(auth_client, tenant):
    created = SecurityEvent.objects.create(user=tenant.employee, event_type=SecurityEventType.LOGIN)
    # A loaded (non-new) instance cannot be re-saved (updates forbidden).
    loaded = SecurityEvent.objects.get(pk=created.pk)
    with pytest.raises(ValueError):
        loaded.save()


@pytest.mark.django_db
def test_empty_history_returns_empty_list(auth_client, tenant):
    client = auth_client(tenant.employee, tenant.company)
    resp = client.get(SECURITY_URL)

    assert resp.status_code == 200
    assert resp.json()["results"] == []
    assert resp.json()["count"] == 0


@pytest.mark.django_db
def test_newest_events_first(auth_client, tenant):
    employee = tenant.employee
    SecurityEvent.objects.create(user=employee, event_type=SecurityEventType.LOGIN)
    SecurityEvent.objects.create(user=employee, event_type=SecurityEventType.PROFILE_UPDATED)

    client = auth_client(employee, tenant.company)
    resp = client.get(SECURITY_URL)

    results = resp.json()["results"]
    assert results[0]["event_type"] == SecurityEventType.PROFILE_UPDATED
    assert results[1]["event_type"] == SecurityEventType.LOGIN
