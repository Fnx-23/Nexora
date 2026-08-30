"""
H-2 hardening tests: scoped auth throttling and anti-enumeration behavior.

Throttle buckets are reset before each test by the autouse `_reset_throttle_counters`
fixture in conftest.py, so these cases are deterministic and independent.
"""

import pytest
from apps.accounts.api.views import REGISTRATION_FAILED_DETAIL
from rest_framework.test import APIClient

from tests.conftest import DEFAULT_PASSWORD

LOGIN_URL = "/api/v1/auth/token/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
REGISTER_URL = "/api/v1/auth/register/"

LOGIN_LIMIT = 10  # AUTH_THROTTLE_LOGIN default
REGISTER_LIMIT = 5  # AUTH_THROTTLE_REGISTER default
REFRESH_LIMIT = 30  # AUTH_THROTTLE_REFRESH default


def _login(client: APIClient, email: str, password: str = DEFAULT_PASSWORD):
    return client.post(LOGIN_URL, {"email": email, "password": password}, format="json")


def _register(client: APIClient, index: int):
    return client.post(
        REGISTER_URL,
        {
            "email": f"owner{index}@throttle.test",
            "password": DEFAULT_PASSWORD,
            "first_name": "Throttle",
            "last_name": str(index),
            "company_name": f"Throttle Co {index}",
        },
        format="json",
    )


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_login_throttled_after_limit(api_client):
    for _ in range(LOGIN_LIMIT):
        response = _login(api_client, "victim@acme.test", "wrong-password")
        assert response.status_code == 401

    blocked = _login(api_client, "victim@acme.test", DEFAULT_PASSWORD)
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_registration_throttled_after_limit(api_client):
    for index in range(REGISTER_LIMIT):
        assert _register(api_client, index).status_code == 201

    blocked = _register(api_client, REGISTER_LIMIT)
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_refresh_throttled_after_limit(api_client):
    garbage = {"refresh": "not-a-real-token"}
    for _ in range(REFRESH_LIMIT):
        response = api_client.post(REFRESH_URL, garbage, format="json")
        assert response.status_code == 401

    blocked = api_client.post(REFRESH_URL, garbage, format="json")
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_legitimate_traffic_within_limits_is_not_throttled(api_client, user_factory):
    user_factory(email="steady@acme.test")

    for _ in range(3):  # far below the login limit
        assert _login(api_client, "steady@acme.test").status_code == 200

    assert _register(api_client, 0).status_code == 201  # below the register limit
    assert _register(api_client, 1).status_code == 201


@pytest.mark.django_db
def test_refresh_chain_and_blacklist_unaffected_by_throttling(api_client, user_factory):
    """Rotation must keep working: each refresh consumes one bucket slot only."""
    user_factory(email="chain@acme.test")
    tokens = _login(api_client, "chain@acme.test").json()

    first = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert first.status_code == 200

    rotated = first.json()["refresh"]
    second = api_client.post(REFRESH_URL, {"refresh": rotated}, format="json")
    assert second.status_code == 200

    reused = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert reused.status_code == 401  # blacklisted after rotation


# ---------------------------------------------------------------------------
# Enumeration resistance
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_wrong_email_and_wrong_password_are_indistinguishable(api_client, user_factory):
    user_factory(email="known@acme.test")

    wrong_email = _login(api_client, "ghost@acme.test", "whatever-123")
    wrong_password = _login(api_client, "known@acme.test", "whatever-123")

    assert wrong_email.status_code == wrong_password.status_code == 401
    assert wrong_email.json() == wrong_password.json()


@pytest.mark.django_db
def test_duplicate_email_response_hides_account_existence(
    api_client, user_factory, django_user_model
):
    user_factory(email="taken@acme.test")

    response = api_client.post(
        REGISTER_URL,
        {
            "email": "taken@acme.test",
            "password": DEFAULT_PASSWORD,
            "first_name": "Dup",
            "last_name": "Probe",
            "company_name": "Probe Industries",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {"detail": REGISTRATION_FAILED_DETAIL}
    lowered = str(response.data).lower()
    assert "exist" not in lowered
    assert "already" not in lowered
    assert "taken" not in lowered
    assert "email" not in lowered

    # No partial state may have been created for the probe.
    assert django_user_model.objects.filter(email__iexact="taken@acme.test").count() == 1
