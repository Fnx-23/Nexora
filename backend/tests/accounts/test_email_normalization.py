"""
Email identity normalization tests (audit item M-7).

Nexora treats email addresses as case-insensitive identifiers: every write
path stores them fully lowercased (local part + domain) and authentication
resolves them regardless of casing.
"""

import pytest
from apps.accounts.models import User
from apps.accounts.services import register_company
from apps.core.exceptions import ApplicationError
from django.db import IntegrityError

AUTH_URL = "/api/v1/auth/"
PASSWORD = "Str0ng-Passw0rd!"


def _registration_payload(**overrides):
    payload = {
        "email": "Ada@Example.com",
        "password": PASSWORD,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "company_name": "NewCo",
    }
    payload.update(overrides)
    return payload


# --- Write paths -------------------------------------------------------------


@pytest.mark.django_db
class TestManagerNormalization:
    def test_create_user_lowercases_local_part_and_domain(self):
        user = User.objects.create_user(email="Ada@Example.COM", password=PASSWORD)

        assert user.email == "ada@example.com"
        assert User.objects.get(pk=user.pk).email == "ada@example.com"

    def test_create_user_strips_surrounding_whitespace(self):
        user = User.objects.create_user(email="  ada@example.com  ", password=PASSWORD)

        assert user.email == "ada@example.com"

    def test_create_superuser_is_normalized(self):
        user = User.objects.create_superuser(
            email="Root@Example.com", password=PASSWORD, first_name="R", last_name="L"
        )

        assert user.email == "root@example.com"

    def test_model_save_normalizes_without_manager(self):
        """Direct instantiation (admin form, scripts) cannot persist mixed case."""
        user = User(email="Mixed.Case@Example.com")
        user.set_password(PASSWORD)
        user.save()

        assert user.email == "mixed.case@example.com"


# --- Authentication lookups --------------------------------------------------


@pytest.mark.django_db
class TestCaseInsensitiveLookup:
    def test_get_by_natural_key_ignores_casing(self, user_factory):
        user_factory(email="ada@example.com")

        found = User.objects.get_by_natural_key("ADA@EXAMPLE.COM")

        assert found.email == "ada@example.com"

    def test_natural_key_lookup_misses_unknown_email(self):
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key("nobody@example.com")


# --- Registration API --------------------------------------------------------


@pytest.mark.django_db
class TestRegistrationNormalization:
    def test_register_mixed_case_email_is_stored_lowercase(self, api_client):
        response = api_client.post(f"{AUTH_URL}register/", _registration_payload())

        assert response.status_code == 201
        assert response.json()["user"]["email"] == "ada@example.com"
        assert User.objects.filter(email="Ada@Example.com").exists() is False
        assert User.objects.filter(email="ada@example.com").count() == 1

    def test_register_duplicate_with_different_casing_rejected(self, api_client):
        first = api_client.post(f"{AUTH_URL}register/", _registration_payload())
        second = api_client.post(
            f"{AUTH_URL}register/",
            _registration_payload(company_name="Other Co"),
        )

        assert first.status_code == 201
        assert second.status_code == 400
        assert User.objects.count() == 1

    def test_service_duplicate_with_different_casing_rejected(self):
        register_company(
            email="ada@example.com",
            password=PASSWORD,
            first_name="Ada",
            last_name="Lovelace",
            company_name="First Co",
        )
        with pytest.raises(ApplicationError):
            register_company(
                email="ADA@Example.com",
                password=PASSWORD,
                first_name="Ada",
                last_name="Lovelace",
                company_name="Second Co",
            )


@pytest.mark.django_db
def test_concurrent_duplicate_maps_to_domain_error(monkeypatch):
    """The unique constraint race window surfaces as ApplicationError, not a 500."""
    from apps.accounts import services

    monkeypatch.setattr(
        services.User.objects,
        "create_user",
        lambda *a, **kw: (_ for _ in ()).throw(IntegrityError("duplicate")),
    )

    with pytest.raises(ApplicationError):
        register_company(
            email="race@example.com",
            password=PASSWORD,
            first_name="A",
            last_name="B",
            company_name="Race Co",
        )


# --- Login -------------------------------------------------------------------


@pytest.mark.django_db
class TestLoginCasing:
    @pytest.mark.parametrize(
        ("registered", "attempted"),
        [
            ("Ada@Example.com", "ada@example.com"),
            ("ada@example.com", "ADA@EXAMPLE.COM"),
        ],
    )
    def test_login_ignores_email_casing(self, api_client, registered, attempted):
        api_client.post(f"{AUTH_URL}register/", _registration_payload(email=registered))

        response = api_client.post(f"{AUTH_URL}token/", {"email": attempted, "password": PASSWORD})

        assert response.status_code == 200
        body = response.json()
        assert body["access"]
        assert body["user"]["email"] == registered.lower()

    def test_login_wrong_cased_email_and_wrong_password_rejected(self, api_client):
        api_client.post(f"{AUTH_URL}register/", _registration_payload())

        response = api_client.post(
            f"{AUTH_URL}token/", {"email": "ADA@EXAMPLE.COM", "password": "wrong-pass-123"}
        )

        assert response.status_code == 401
