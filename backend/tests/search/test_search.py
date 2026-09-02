"""Tests for the global search endpoint (command palette backend).

Covers grouped results, per-category limits, tenant isolation, empty/blank
queries, literal special-character handling, permission boundaries, expected
metadata/navigation links, and a bounded query budget (no N+1).
"""

import pytest
from apps.companies.models import RoleChoices
from apps.search.services import PER_CATEGORY_LIMIT
from django.db import connection
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db

SEARCH_URL = "/api/v1/search/"


def _search(client, company, query=""):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(SEARCH_URL, {"q": query})


@pytest.fixture
def search_client(auth_client, tenant):
    """APIClient authenticated as tenant.admin within tenant.company."""

    def _make(user=None, company=None):
        return auth_client(user or tenant.admin, company or tenant.company)

    return _make


# --------------------------------------------------------------------------- #
# Results across entity types
# --------------------------------------------------------------------------- #
class TestGroupedResults:
    def test_returns_matches_across_all_entity_types(
        self,
        search_client,
        tenant,
        user_factory,
        membership_factory,
        project_factory,
        task_factory,
    ):
        manager = user_factory(email="mgr@acme.test", first_name="Maya", last_name="Moore")
        dev = user_factory(email="dev@acme.test", first_name="Dev", last_name="Braun")
        membership_factory(dev, tenant.company, RoleChoices.EMPLOYEE)
        project = project_factory(company=tenant.company, name="Cloud Migration", manager=manager)
        task = task_factory(
            company=tenant.company, title="Cloud Migration steps", project=project, assignee=dev
        )
        response = _search(search_client(), tenant.company, "cloud")
        assert response.status_code == 200

        projects = response.data["projects"]
        assert [p["name"] for p in projects] == ["Cloud Migration"]
        assert projects[0]["link"] == f"/projects/{project.pk}"
        assert projects[0]["manager_name"] == "Maya Moore"

        tasks = response.data["tasks"]
        assert [t["title"] for t in tasks] == ["Cloud Migration steps"]
        assert tasks[0]["link"] == f"/tasks/{task.pk}"
        assert tasks[0]["project_name"] == "Cloud Migration"
        assert tasks[0]["assignee_name"] == "Dev Braun"

    def test_returns_customers(self, search_client, tenant, customer_factory):
        customer = customer_factory(company=tenant.company, name="Atlas Logistics")
        response = _search(search_client(), tenant.company, "atlas")

        assert response.data["projects"] == []
        assert [c["name"] for c in response.data["customers"]] == ["Atlas Logistics"]
        assert response.data["customers"][0]["link"] == "/customers"
        assert response.data["customers"][0]["id"] == str(customer.pk)

    def test_member_search_by_name_and_email(
        self, search_client, tenant, user_factory, membership_factory
    ):
        member = user_factory(email="sara.alami@nexora.test", first_name="Sara", last_name="Alami")
        membership_factory(member, tenant.company, RoleChoices.ADMIN)

        by_name = _search(search_client(), tenant.company, "sara")
        assert by_name.data["members"] == [
            {
                "id": str(member.pk),
                "name": "Sara Alami",
                "email": "sara.alami@nexora.test",
                "role": "ADMIN",
                "link": "/team",
            }
        ]

        by_email = _search(search_client(), tenant.company, "nexora.test")
        assert [m["id"] for m in by_email.data["members"]] == [str(member.pk)]

    def test_inactive_membership_is_not_searchable(
        self, search_client, tenant, user_factory, membership_factory
    ):
        member = user_factory(email="gone@nexora.test", first_name="Gone", last_name="Guy")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE, is_active=False)
        response = _search(search_client(), tenant.company, "gone")
        assert response.data["members"] == []

    def test_search_is_case_insensitive(self, search_client, tenant, project_factory):
        project_factory(company=tenant.company, name="Cloud Migration")
        for term in ("CLOUD", "cloud", "ClOuD"):
            response = _search(search_client(), tenant.company, term)
            assert [p["name"] for p in response.data["projects"]] == ["Cloud Migration"]


# --------------------------------------------------------------------------- #
# Limits / query budget
# --------------------------------------------------------------------------- #
class TestLimits:
    def test_per_category_limit_applied(self, search_client, tenant, project_factory):
        for i in range(PER_CATEGORY_LIMIT + 2):
            project_factory(company=tenant.company, name=f"Acme Project {i}")

        response = _search(search_client(), tenant.company, "acme")
        assert len(response.data["projects"]) == PER_CATEGORY_LIMIT

    def test_blank_query_returns_empty_groups(self, search_client, tenant, project_factory):
        project_factory(company=tenant.company, name="Cloud Migration")
        response = _search(search_client(), tenant.company, "")

        assert response.status_code == 200
        assert response.data["query"] == ""
        for group in ("projects", "customers", "tasks", "members"):
            assert response.data[group] == []

    def test_whitespace_only_query_returns_empty_groups(
        self, search_client, tenant, project_factory
    ):
        project_factory(company=tenant.company, name="Cloud Migration")
        response = _search(search_client(), tenant.company, "   ")

        assert response.status_code == 200
        for group in ("projects", "customers", "tasks", "members"):
            assert response.data[group] == []

    def test_very_long_query_is_capped_without_error(self, search_client, tenant, project_factory):
        project_factory(company=tenant.company, name="Cloud Migration")
        response = _search(search_client(), tenant.company, "x" * 500)

        assert response.status_code == 200
        assert response.data["projects"] == []

    def test_bounded_query_budget_no_nplus1(
        self, tenant, auth_client, project_factory, task_factory
    ):
        project = project_factory(company=tenant.company, name="Acme Alpha")
        for i in range(PER_CATEGORY_LIMIT + 2):
            task_factory(
                company=tenant.company,
                title=f"Acme chore {i}",
                project=project,
                assignee=tenant.employee,
            )
        project_factory(company=tenant.company, name="Acme Parent")

        client = auth_client(tenant.admin, tenant.company)
        with CaptureQueriesContext(connection) as ctx:
            response = client.get(SEARCH_URL, {"q": "acme"})
        assert response.status_code == 200
        assert len(response.data["tasks"]) == PER_CATEGORY_LIMIT
        # 4 bounded entity queries + a fixed small overhead, never N+1.
        assert len(ctx.captured_queries) <= 10


# --------------------------------------------------------------------------- #
# Tenant isolation
# --------------------------------------------------------------------------- #
class TestTenantIsolation:
    def test_query_never_returns_other_company_records(
        self,
        search_client,
        tenant,
        company_factory,
        user_factory,
        membership_factory,
        project_factory,
        task_factory,
    ):
        other_company = company_factory(name="Rival Inc", slug="rival")
        rival_admin = user_factory(email="rival@test.com")
        membership_factory(rival_admin, other_company, RoleChoices.ADMIN)
        project_factory(company=other_company, name="Cloud Migration")
        task_factory(company=other_company, title="Configure SSO")

        response = _search(search_client(), tenant.company, "cloud")
        assert response.data["projects"] == []
        assert response.data["tasks"] == []

    def test_same_term_in_both_companies_is_separated(
        self,
        search_client,
        tenant,
        company_factory,
        user_factory,
        membership_factory,
        project_factory,
    ):
        other_company = company_factory(name="Rival Inc", slug="rival")
        rival_admin = user_factory(email="rival@test.com")
        membership_factory(rival_admin, other_company, RoleChoices.ADMIN)

        ours = project_factory(company=tenant.company, name="Cloud Migration")
        theirs = project_factory(company=other_company, name="Cloud Migration")

        admin_results = _search(search_client(), tenant.company, "cloud")
        assert [p["id"] for p in admin_results.data["projects"]] == [str(ours.pk)]

        rival_results = _search(search_client(rival_admin), other_company, "cloud")
        assert [p["id"] for p in rival_results.data["projects"]] == [str(theirs.pk)]
        assert admin_results.data["projects"][0]["id"] != rival_results.data["projects"][0]["id"]


# --------------------------------------------------------------------------- #
# Special characters
# --------------------------------------------------------------------------- #
class TestSpecialCharacters:
    def test_percent_sign_matches_literally(self, search_client, tenant, project_factory):
        project_factory(company=tenant.company, name="100% done board")
        response = _search(search_client(), tenant.company, "100%")

        assert [p["name"] for p in response.data["projects"]] == ["100% done board"]

    def test_percent_sign_does_not_match_everything(self, search_client, tenant, project_factory):
        project_factory(company=tenant.company, name="plain project")
        response = _search(search_client(), tenant.company, "%")

        assert response.data["projects"] == []

    def test_underscore_matches_literally(self, search_client, tenant, task_factory):
        task_factory(company=tenant.company, title="my_task")
        response = _search(search_client(), tenant.company, "my_task")

        assert [t["title"] for t in response.data["tasks"]] == ["my_task"]

    def test_underscore_is_not_a_wildcard(self, search_client, tenant, task_factory):
        task_factory(company=tenant.company, title="mxxtaskrequest")
        response = _search(search_client(), tenant.company, "m_t")

        assert response.data["tasks"] == []


# --------------------------------------------------------------------------- #
# Permissions
# --------------------------------------------------------------------------- #
class TestPermissions:
    def test_unauthenticated_is_rejected(self, api_client):
        response = api_client.get(SEARCH_URL, {"q": "cloud"})
        assert response.status_code in (401, 403)

    def test_user_without_membership_is_rejected(self, user_factory, api_client):
        lone = user_factory(email="lone@test.com")
        api_client.force_authenticate(user=lone)
        response = api_client.get(SEARCH_URL, {"q": "cloud"})
        assert response.status_code == 403

    def test_other_company_header_is_rejected(self, search_client, tenant, company_factory):
        other = company_factory(name="Other", slug="other")
        # tenant.admin belongs only to tenant.company; claiming company "other" is denied.
        response = _search(search_client(), other, "cloud")
        assert response.status_code == 403
