"""Authentication endpoint tests."""

import pytest

from tests.conftest import DEFAULT_PASSWORD

AUTH_URL = "/api/v1/auth/"


@pytest.mark.django_db
def test_login_returns_tokens_and_user(api_client, user_factory):
    user_factory(email="login@acme.test", password=DEFAULT_PASSWORD)

    response = api_client.post(
        f"{AUTH_URL}token/", {"email": "login@acme.test", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access"]
    assert body["refresh"]
    assert body["user"]["email"] == "login@acme.test"


@pytest.mark.django_db
def test_login_wrong_password_rejected(api_client, user_factory):
    user_factory(email="login@acme.test")

    response = api_client.post(
        f"{AUTH_URL}token/", {"email": "login@acme.test", "password": "wrong-pass-123"}
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    response = api_client.get(f"{AUTH_URL}me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_memberships_and_active_company(auth_client, tenant):
    client = auth_client(tenant.admin)

    response = client.get(f"{AUTH_URL}me/")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@acme.test"
    assert body["active_company"]["slug"] == "acme"
    assert len(body["memberships"]) == 1
    assert body["memberships"][0]["role"] == "ADMIN"


@pytest.mark.django_db
def test_refresh_issues_new_access_token(api_client, user_factory):
    user_factory(email="login@acme.test", password=DEFAULT_PASSWORD)
    login = api_client.post(
        f"{AUTH_URL}token/", {"email": "login@acme.test", "password": DEFAULT_PASSWORD}
    )
    refresh = login.json()["refresh"]

    response = api_client.post(f"{AUTH_URL}token/refresh/", {"refresh": refresh})

    assert response.status_code == 200
    assert response.json()["access"]
