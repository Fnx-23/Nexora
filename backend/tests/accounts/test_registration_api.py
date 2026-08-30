"""Tests for the registration (tenant bootstrap) flow."""

import pytest

PASSWORD = "Str0ng-Passw0rd!"


def _payload(**overrides):
    payload = {
        "email": "owner@newco.test",
        "password": PASSWORD,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "company_name": "NewCo",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_register_creates_user_company_and_admin_membership(api_client):
    response = api_client.post("/api/v1/auth/register/", _payload())

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "owner@newco.test"
    assert data["company"]["name"] == "NewCo"
    assert data["company"]["slug"] == "newco"
    assert set(data["tokens"]) == {"access", "refresh"}


@pytest.mark.django_db
def test_register_duplicate_email_rejected(api_client, user_factory):
    user_factory(email="owner@newco.test")

    response = api_client.post("/api/v1/auth/register/", _payload())

    assert response.status_code == 400


@pytest.mark.django_db
def test_register_weak_password_rejected(api_client):
    response = api_client.post("/api/v1/auth/register/", _payload(password="password"))

    assert response.status_code == 400


@pytest.mark.django_db
def test_register_slug_collision_gets_unique_slug(api_client):
    first = api_client.post("/api/v1/auth/register/", _payload())
    second = api_client.post(
        "/api/v1/auth/register/",
        _payload(email="other@newco.test", company_name="NewCo"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["company"]["slug"] != first.json()["company"]["slug"]
