"""API-level tests for the Customer CRUD + archive endpoints."""

import pytest
from apps.companies.models import Membership, RoleChoices
from apps.customers.models import Customer, CustomerStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(**overrides):
    data = {
        "name": "Jane Smith",
        "company_name": "Acme Corp",
        "email": "jane@acme.com",
        "phone": "+1-555-0100",
        "address": "123 Main St",
        "notes": "VIP",
        "status": "ACTIVE",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# List & Retrieve
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListCustomers:
    def test_returns_paginated_list(self, tenant, auth_client, customer_factory):
        for i in range(3):
            customer_factory(tenant.company, name=f"Cust {i}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/customers/")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 3
        assert len(body["results"]) == 3

    def test_empty_list(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/customers/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


@pytest.mark.django_db
class TestRetrieveCustomer:
    def test_retrieve_own_customer(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company, name="Acquired")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/customers/{c.id}/")

        assert resp.status_code == 200
        assert resp.json()["name"] == "Acquired"
        assert resp.json()["id"] == str(c.id)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateCustomer:
    def test_create_with_valid_data(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Jane Smith"
        assert body["company_name"] == "Acme Corp"
        assert body["status"] == "ACTIVE"

    def test_create_auto_stamps_company(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        c = Customer.objects.get(pk=resp.json()["id"])
        assert c.company_id == tenant.company.id

    def test_create_minimal_fields(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            {"name": "Minimal"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == ""
        assert body["phone"] == ""
        assert body["status"] == "ACTIVE"

    def test_create_requires_name(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            {},
            format="json",
        )
        assert resp.status_code == 400
        assert "name" in resp.json()


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateCustomer:
    def test_partial_update(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company, name="Old Name")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/customers/{c.id}/",
            {"name": "New Name", "email": "new@test.com"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"
        assert resp.json()["email"] == "new@test.com"

    def test_full_update(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company, name="Original")
        resp = auth_client(tenant.admin, tenant.company).put(
            f"/api/v1/customers/{c.id}/",
            _payload(name="Replaced", email="replaced@test.com"),
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Replaced"
        assert body["email"] == "replaced@test.com"


# ---------------------------------------------------------------------------
# Archive (soft-delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestArchiveCustomer:
    def test_archive_sets_status(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/customers/{c.id}/archive/",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ARCHIVED"
        c.refresh_from_db()
        assert c.status == CustomerStatus.ARCHIVED
        assert c.is_active is False

    def test_archive_already_archived_returns_400(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company, status=CustomerStatus.ARCHIVED, is_active=False)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/customers/{c.id}/archive/",
        )
        assert resp.status_code == 400

    def test_archive_requires_manager_or_admin(self, tenant, auth_client, customer_factory):
        employee = tenant.employee
        c = customer_factory(tenant.company)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        resp = auth_client(employee, tenant.company).post(
            f"/api/v1/customers/{c.id}/archive/",
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Delete (permanent)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeleteCustomer:
    def test_delete_removes_customer(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).delete(
            f"/api/v1/customers/{c.id}/",
        )
        assert resp.status_code == 204
        assert not Customer.objects.filter(pk=c.id).exists()

    def test_delete_requires_manager_or_admin(self, tenant, auth_client, customer_factory):
        employee = tenant.employee
        c = customer_factory(tenant.company)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/customers/{c.id}/",
        )
        assert resp.status_code == 403

        Membership.objects.filter(user=employee).update(role=RoleChoices.ADMIN)
        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/customers/{c.id}/",
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidation:
    def test_invalid_status_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            _payload(status="BOGUS"),
            format="json",
        )
        assert resp.status_code == 400
        assert "status" in resp.json()

    def test_name_max_length_enforced(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            _payload(name="X" * 121),
            format="json",
        )
        assert resp.status_code == 400
        assert "name" in resp.json()

    def test_invalid_email_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/customers/",
            _payload(email="not-an-email"),
            format="json",
        )
        assert resp.status_code == 400
        assert "email" in resp.json()


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSearch:
    def test_search_by_name(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Alice Corp")
        customer_factory(tenant.company, name="Bob Ltd")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"search": "Alice"},
        )
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Alice Corp"]

    def test_search_by_email(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="A", email="x@y.com")
        customer_factory(tenant.company, name="B")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"search": "x@y.com"},
        )
        assert resp.json()["count"] == 1

    def test_search_by_company_name(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Contact", company_name="Globex Inc")
        customer_factory(tenant.company, name="Other")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"search": "Globex"},
        )
        assert resp.json()["count"] == 1

    def test_search_by_phone(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="A", phone="555-1234")
        customer_factory(tenant.company, name="B")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"search": "555-1234"},
        )
        assert resp.json()["count"] == 1


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFiltering:
    def test_filter_by_status(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Active", status=CustomerStatus.ACTIVE)
        customer_factory(
            tenant.company,
            name="Archived",
            status=CustomerStatus.ARCHIVED,
            is_active=False,
        )

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"status": "ACTIVE"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "Active"

    def test_filter_by_is_active(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Live", is_active=True)
        customer_factory(tenant.company, name="Dead", is_active=False)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"is_active": "true"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "Live"


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrdering:
    def test_order_by_name(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Zebra")
        customer_factory(tenant.company, name="Alpha")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"ordering": "name"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Alpha", "Zebra"]

    def test_order_by_created_at_desc(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="First")
        customer_factory(tenant.company, name="Second")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"ordering": "-created_at"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Second", "First"]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPagination:
    def test_default_page_size(self, tenant, auth_client, customer_factory):
        for i in range(30):
            customer_factory(tenant.company, name=f"C{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/customers/")
        body = resp.json()
        assert body["count"] == 30
        assert len(body["results"]) == 25
        assert body["next"] is not None

    def test_custom_page_size(self, tenant, auth_client, customer_factory):
        for i in range(5):
            customer_factory(tenant.company, name=f"C{i}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"page_size": 2},
        )
        body = resp.json()
        assert body["count"] == 5
        assert len(body["results"]) == 2
        assert body["next"] is not None

    def test_second_page(self, tenant, auth_client, customer_factory):
        for i in range(30):
            customer_factory(tenant.company, name=f"C{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/customers/",
            {"page": 2},
        )
        body = resp.json()
        assert len(body["results"]) == 5
        assert body["previous"] is not None


# ---------------------------------------------------------------------------
# Tenant isolation (customer-specific)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantIsolation:
    def test_cannot_list_other_company_customers(
        self,
        two_tenants,
        auth_client,
        customer_factory,
    ):
        factory = customer_factory
        own = factory(two_tenants["a"]["company"], name="Mine")
        foreign = factory(two_tenants["b"]["company"], name="Theirs")

        resp = auth_client(two_tenants["a"]["user"]).get("/api/v1/customers/")
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()["results"]}
        assert str(own.id) in ids
        assert str(foreign.id) not in ids

    def test_cannot_retrieve_other_company_customer(
        self,
        two_tenants,
        auth_client,
        customer_factory,
    ):
        foreign = customer_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).get(
            f"/api/v1/customers/{foreign.id}/",
        )
        assert resp.status_code == 404

    def test_cannot_update_other_company_customer(
        self,
        two_tenants,
        auth_client,
        customer_factory,
    ):
        foreign = customer_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/customers/{foreign.id}/",
            {"name": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404
        foreign.refresh_from_db()
        assert str(foreign) != "Hacked"

    def test_cannot_archive_other_company_customer(
        self,
        two_tenants,
        auth_client,
        customer_factory,
    ):
        foreign = customer_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/customers/{foreign.id}/archive/",
        )
        assert resp.status_code == 404

    def test_created_customer_belongs_to_request_company(
        self,
        two_tenants,
        auth_client,
    ):
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/customers/",
            {"name": "Local Only"},
            format="json",
        )
        assert resp.status_code == 201
        c = Customer.objects.get(pk=resp.json()["id"])
        assert c.company_id == two_tenants["a"]["company"].id


# ---------------------------------------------------------------------------
# Fixtures: two_tenants (duplicated here for independence)
# ---------------------------------------------------------------------------


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    admin_a = user_factory(email="admin@a-cust.test")
    admin_b = user_factory(email="admin@b-cust.test")
    company_a = company_factory(name="Company A Cust", slug="company-a-cust")
    company_b = company_factory(name="Company B Cust", slug="company-b-cust")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
