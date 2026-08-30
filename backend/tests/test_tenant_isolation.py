"""
Tenant isolation tests — the most important suite in Nexora.

Guarantees that a user belonging to Company A can never read or write
Company B's customers, projects, or tasks, through any endpoint.
"""

import pytest

ISOLATED_RESOURCES = [
    ("customers", "customer_factory"),
    ("projects", "project_factory"),
    ("tasks", "task_factory"),
]


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    """Company A (with a member) and Company B (with its own member)."""
    admin_a = user_factory(email="admin@a.test")
    admin_b = user_factory(email="admin@b.test")
    company_a = company_factory(name="Company A", slug="company-a")
    company_b = company_factory(name="Company B", slug="company-b")

    from apps.companies.models import RoleChoices

    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }


@pytest.mark.django_db
class TestListIsolation:
    @pytest.mark.parametrize("endpoint,factory_key", [(r[0], r[1]) for r in ISOLATED_RESOURCES])
    def test_lists_only_own_tenant_data(
        self, two_tenants, auth_client, endpoint, factory_key, request
    ):
        factory = request.getfixturevalue(factory_key)
        own = factory(two_tenants["a"]["company"])
        foreign = factory(two_tenants["b"]["company"])

        response = auth_client(two_tenants["a"]["user"]).get(f"/api/v1/{endpoint}/")

        assert response.status_code == 200
        ids = {row["id"] for row in response.json()["results"]}
        assert str(own.id) in ids
        assert str(foreign.id) not in ids


@pytest.mark.django_db
class TestDetailIsolation:
    @pytest.mark.parametrize("endpoint,factory_key", [(r[0], r[1]) for r in ISOLATED_RESOURCES])
    def test_foreign_detail_returns_404(
        self, two_tenants, auth_client, endpoint, factory_key, request
    ):
        factory = request.getfixturevalue(factory_key)
        foreign = factory(two_tenants["b"]["company"])

        response = auth_client(two_tenants["a"]["user"]).get(f"/api/v1/{endpoint}/{foreign.id}/")

        assert response.status_code == 404

    @pytest.mark.parametrize("endpoint,factory_key", [(r[0], r[1]) for r in ISOLATED_RESOURCES])
    def test_cannot_update_foreign_object(
        self, two_tenants, auth_client, endpoint, factory_key, request
    ):
        factory = request.getfixturevalue(factory_key)
        foreign = factory(two_tenants["b"]["company"])

        response = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/{endpoint}/{foreign.id}/", {"name": "Owned"}, format="json"
        )

        assert response.status_code == 404
        foreign.refresh_from_db()
        # `str()` is `name` for Customer/Project and `title` for Task.
        assert str(foreign) != "Owned"


@pytest.mark.django_db
class TestCompanyHeaderValidation:
    """X-Company-Id header validation (BUG-2 regression)."""

    def test_missing_header_uses_default_company(self, two_tenants, auth_client):
        client = auth_client(two_tenants["a"]["user"])  # no header => oldest membership
        resp = client.get("/api/v1/customers/")
        assert resp.status_code == 200

    def test_explicit_own_company_accepted(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/customers/")
        assert resp.status_code == 200

    def test_own_company_list_only_own_data(self, two_tenants, auth_client, customer_factory):
        customer_factory(two_tenants["a"]["company"], name="Own A")
        customer_factory(two_tenants["b"]["company"], name="Own B")

        client = auth_client(two_tenants["a"]["user"], two_tenants["a"]["company"])
        resp = client.get("/api/v1/customers/")
        assert resp.status_code == 200
        names = {row["name"] for row in resp.json()["results"]}
        assert "Own A" in names
        assert "Own B" not in names

    def test_foreign_company_rejected(self, two_tenants, auth_client):
        client = auth_client(two_tenants["a"]["user"], two_tenants["b"]["company"])
        resp = client.get("/api/v1/customers/")
        assert resp.status_code == 403

    def test_nonexistent_company_rejected(self, tenant, auth_client):
        import uuid

        client = auth_client(tenant.admin)
        client.credentials(HTTP_X_COMPANY_ID=str(uuid.uuid4()))
        resp = client.get("/api/v1/customers/")
        assert resp.status_code in (400, 403)

    def test_malformed_uuid_rejected(self, tenant, auth_client):
        client = auth_client(tenant.admin)
        client.credentials(HTTP_X_COMPANY_ID="not-a-valid-uuid")
        resp = client.get("/api/v1/customers/")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestCrossTenantReferences:
    def test_project_cannot_reference_foreign_customer(
        self, two_tenants, auth_client, customer_factory
    ):
        foreign_customer = customer_factory(two_tenants["b"]["company"])

        response = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/projects/",
            {"name": "Sneaky project", "customer": str(foreign_customer.id)},
            format="json",
        )

        assert response.status_code == 400

    def test_task_cannot_belong_to_foreign_project(self, two_tenants, auth_client, project_factory):
        foreign_project = project_factory(two_tenants["b"]["company"])

        response = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/tasks/",
            {"title": "Sneaky task", "project": str(foreign_project.id)},
            format="json",
        )

        assert response.status_code == 400

    def test_task_cannot_be_assigned_to_non_member(self, two_tenants, auth_client):
        response = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/tasks/",
            {"title": "Sneaky task", "assignee": str(two_tenants["b"]["user"].id)},
            format="json",
        )

        assert response.status_code == 400

    def test_created_objects_are_stamped_with_active_company(self, two_tenants, auth_client):
        client = auth_client(two_tenants["a"]["user"])

        created = client.post("/api/v1/customers/", {"name": "Local Co"}, format="json")
        assert created.status_code == 201
        assert created.json()["is_active"] is True

        from apps.customers.models import Customer

        customer = Customer.objects.get(pk=created.json()["id"])
        assert customer.company_id == two_tenants["a"]["company"].id


@pytest.mark.django_db
class TestAuthenticationBoundaries:
    def test_anonymous_users_are_rejected(self, api_client):
        assert api_client.get("/api/v1/customers/").status_code == 401
        assert api_client.get("/api/v1/projects/").status_code == 401
        assert api_client.get("/api/v1/tasks/").status_code == 401

    def test_member_without_company_context_is_rejected(self, api_client, user_factory):
        from rest_framework.test import APIClient

        outsider = APIClient()
        outsider.force_authenticate(user=user_factory(email="floating@nomad.test"))

        assert outsider.get("/api/v1/customers/").status_code == 403

    def test_destroy_requires_manager_or_admin(self, two_tenants, auth_client, customer_factory):
        from apps.companies.models import Membership, RoleChoices

        employee = two_tenants["a"]["user"]
        target = customer_factory(two_tenants["a"]["company"])
        client = auth_client(employee)

        # The `tenant` fixture makes user A an ADMIN; demote to EMPLOYEE first.
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        response = client.delete(f"/api/v1/customers/{target.id}/")
        assert response.status_code == 403

        Membership.objects.filter(user=employee).update(role=RoleChoices.ADMIN)
        response = client.delete(f"/api/v1/customers/{target.id}/")
        assert response.status_code == 204
