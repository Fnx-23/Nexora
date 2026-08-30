"""Company context and role-based access tests."""

import pytest


@pytest.mark.django_db
def test_current_company_returns_users_company(auth_client, tenant):
    response = auth_client(tenant.employee).get("/api/v1/companies/current/")

    assert response.status_code == 200
    assert response.json()["id"] == str(tenant.company.id)


@pytest.mark.django_db
def test_current_company_requires_membership(api_client, user_factory):
    from rest_framework.test import APIClient

    outsider = APIClient()
    outsider.force_authenticate(user=user_factory(email="loner@nomad.test"))

    response = outsider.get("/api/v1/companies/current/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_employee_cannot_update_company(auth_client, tenant):
    response = auth_client(tenant.employee).patch(
        "/api/v1/companies/current/", {"name": "Hacked Co"}, format="json"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_update_company(auth_client, tenant):
    response = auth_client(tenant.admin).patch(
        "/api/v1/companies/current/", {"description": "We build things."}, format="json"
    )

    assert response.status_code == 200
    assert response.json()["description"] == "We build things."
    tenant.company.refresh_from_db()
    assert tenant.company.description == "We build things."


@pytest.mark.django_db
def test_admin_cannot_deactivate_company_via_settings(auth_client, tenant):
    """H-3 regression: self-deactivation through the public endpoint is ignored."""
    response = auth_client(tenant.admin).patch(
        "/api/v1/companies/current/", {"is_active": False}, format="json"
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True

    tenant.company.refresh_from_db()
    assert tenant.company.is_active is True

    # The workspace must remain fully usable afterwards.
    follow_up = auth_client(tenant.admin).get("/api/v1/companies/current/")
    assert follow_up.status_code == 200


@pytest.mark.django_db
def test_admin_settings_patch_ignores_read_only_fields_only(auth_client, tenant):
    """A mixed payload updates writable fields while dropping protected ones."""
    response = auth_client(tenant.admin).patch(
        "/api/v1/companies/current/",
        {"name": "Renamed Inc", "slug": "hijacked", "is_active": False},
        format="json",
    )

    assert response.status_code == 200
    tenant.company.refresh_from_db()
    assert tenant.company.name == "Renamed Inc"
    assert tenant.company.slug == "acme"
    assert tenant.company.is_active is True


@pytest.mark.django_db
def test_foreign_company_header_is_rejected(auth_client, tenant, company_factory):
    """BUG-2 regression: a member cannot switch into a company they do not belong to.

    An explicit X-Company-Id for a foreign company must be rejected (403)
    rather than silently falling back to default context.
    """
    foreign = company_factory(name="Foreign", slug="foreign")

    response = auth_client(tenant.admin, foreign).get("/api/v1/companies/current/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_users_lists_only_company_members(auth_client, tenant, user_factory):
    from apps.companies.models import Membership, RoleChoices

    colleague = user_factory(email="colleague@acme.test")
    Membership.objects.create(user=colleague, company=tenant.company, role=RoleChoices.MANAGER)
    stranger = user_factory(email="stranger@elsewhere.test")

    response = auth_client(tenant.employee).get("/api/v1/users/")

    assert response.status_code == 200
    emails = {row["email"] for row in response.json()["results"]}
    assert emails == {"admin@acme.test", "employee@acme.test", "colleague@acme.test"}
    assert stranger.email not in emails
