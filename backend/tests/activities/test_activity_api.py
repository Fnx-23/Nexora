"""API-level tests for the read-only, tenant-scoped Activity endpoint.

Covers the "read-only API for normal users" and "tenant scoped" requirements:
list/retrieve work for any company member, all write verbs answer 405, filtering
and pagination behave, and no company can ever see another company's audit trail.
"""

import pytest
from apps.activities.models import Activity, ActivityAction
from apps.companies.models import RoleChoices

LIST_URL = "/api/v1/activities/"


# --------------------------------------------------------------------------- #
# Read-only surface
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestReadOnlyAccess:
    def test_member_can_list(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).get(LIST_URL)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_employee_can_read(self, tenant, auth_client, customer_factory):
        # "read-only API for normal users" — a plain employee may read the log.
        customer_factory(tenant.company)
        resp = auth_client(tenant.employee, tenant.company).get(LIST_URL)
        assert resp.status_code == 200

    def test_retrieve_single(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company)
        act = Activity.objects.get(action=ActivityAction.CUSTOMER_CREATED, entity_id=c.id)
        resp = auth_client(tenant.admin, tenant.company).get(f"{LIST_URL}{act.id}/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["action"] == "customer.created"
        assert body["entity_type"] == "customer"
        assert body["entity_id"] == str(c.id)

    def test_unauthenticated_is_rejected(self, api_client):
        assert api_client.get(LIST_URL).status_code in (401, 403)


@pytest.mark.django_db
class TestWriteVerbsRejected:
    def test_post_not_allowed(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(LIST_URL, {}, format="json")
        assert resp.status_code == 405

    def test_detail_write_verbs_not_allowed(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company)
        act = Activity.objects.get(action=ActivityAction.CUSTOMER_CREATED, entity_id=c.id)
        client = auth_client(tenant.admin, tenant.company)
        detail = f"{LIST_URL}{act.id}/"
        assert client.put(detail, {}, format="json").status_code == 405
        assert client.patch(detail, {}, format="json").status_code == 405
        assert client.delete(detail).status_code == 405
        # The record must survive every rejected write attempt.
        assert Activity.objects.filter(pk=act.id).exists()


# --------------------------------------------------------------------------- #
# Filtering / ordering / pagination
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestFiltering:
    def test_filter_by_action(self, tenant, auth_client, customer_factory, project_factory):
        customer_factory(tenant.company)
        project_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).get(
            LIST_URL, {"action": "customer.created"}
        )
        actions = {r["action"] for r in resp.json()["results"]}
        assert actions == {"customer.created"}

    def test_filter_by_entity_type(self, tenant, auth_client, customer_factory, project_factory):
        customer_factory(tenant.company)
        project_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).get(LIST_URL, {"entity_type": "project"})
        results = resp.json()["results"]
        assert results and all(r["entity_type"] == "project" for r in results)

    def test_filter_by_entity_id(self, tenant, auth_client, customer_factory):
        target = customer_factory(tenant.company, name="Target")
        customer_factory(tenant.company, name="Other")
        resp = auth_client(tenant.admin, tenant.company).get(
            LIST_URL, {"entity_id": str(target.id)}
        )
        ids = {r["entity_id"] for r in resp.json()["results"]}
        assert ids == {str(target.id)}

    def test_filter_by_actor(self, tenant, auth_client, customer_factory):
        client = auth_client(tenant.admin, tenant.company)
        client.post("/api/v1/customers/", {"name": "Via API"}, format="json")  # actor=admin
        customer_factory(tenant.company, name="Via ORM")  # actor=None
        resp = client.get(LIST_URL, {"actor": str(tenant.admin.id)})
        results = resp.json()["results"]
        assert results and all(r["actor"] == str(tenant.admin.id) for r in results)


@pytest.mark.django_db
class TestOrdering:
    def test_default_is_newest_first(self, tenant, auth_client, customer_factory):
        for i in range(3):
            customer_factory(tenant.company, name=f"C{i}")
        resp = auth_client(tenant.admin, tenant.company).get(LIST_URL)
        timestamps = [r["timestamp"] for r in resp.json()["results"]]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_ascending_ordering(self, tenant, auth_client, customer_factory):
        for i in range(3):
            customer_factory(tenant.company, name=f"C{i}")
        resp = auth_client(tenant.admin, tenant.company).get(LIST_URL, {"ordering": "timestamp"})
        timestamps = [r["timestamp"] for r in resp.json()["results"]]
        assert timestamps == sorted(timestamps)


@pytest.mark.django_db
class TestPagination:
    def test_default_page_size(self, tenant, auth_client, customer_factory):
        for i in range(30):
            customer_factory(tenant.company, name=f"C{i:02d}")
        resp = auth_client(tenant.admin, tenant.company).get(LIST_URL)
        body = resp.json()
        assert body["count"] == 30
        assert len(body["results"]) == 25
        assert body["next"] is not None


# --------------------------------------------------------------------------- #
# Tenant isolation
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestTenantIsolation:
    def test_list_only_shows_own_company(self, two_tenants, auth_client, customer_factory):
        customer_factory(two_tenants["a"]["company"], name="A cust")
        customer_factory(two_tenants["b"]["company"], name="B cust")
        resp = auth_client(two_tenants["a"]["user"]).get(LIST_URL)
        assert resp.status_code == 200
        # Company A produced exactly one activity; B's must not appear.
        assert resp.json()["count"] == 1

    def test_cannot_retrieve_other_company_activity(
        self, two_tenants, auth_client, customer_factory
    ):
        b_cust = customer_factory(two_tenants["b"]["company"])
        b_act = Activity.objects.get(action=ActivityAction.CUSTOMER_CREATED, entity_id=b_cust.id)
        resp = auth_client(two_tenants["a"]["user"]).get(f"{LIST_URL}{b_act.id}/")
        assert resp.status_code == 404

    def test_entity_id_filter_cannot_leak_other_company(
        self, two_tenants, auth_client, customer_factory
    ):
        b_cust = customer_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).get(LIST_URL, {"entity_id": str(b_cust.id)})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


# --------------------------------------------------------------------------- #
# Fixtures: two_tenants (duplicated here for independence)
# --------------------------------------------------------------------------- #
@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    admin_a = user_factory(email="admin@a-act.test")
    admin_b = user_factory(email="admin@b-act.test")
    company_a = company_factory(name="Company A Act", slug="company-a-act")
    company_b = company_factory(name="Company B Act", slug="company-b-act")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
