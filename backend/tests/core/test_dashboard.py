"""Tests for the dashboard aggregation endpoint."""

from datetime import date, timedelta

import pytest
from apps.companies.models import RoleChoices
from apps.projects.models import ProjectStatus
from apps.tasks.models import TaskStatus

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dashboard(client, company):
    """GET /api/v1/dashboard/ with company context."""
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get("/api/v1/dashboard/")


# ---------------------------------------------------------------------------
# KPI counts
# ---------------------------------------------------------------------------


class TestKPICounts:
    def test_empty_company_returns_zeros(self, tenant, auth_client):
        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        kpis = resp.data["kpis"]
        assert kpis["active_projects"] == 0
        assert kpis["total_projects"] == 0
        assert kpis["total_customers"] == 0
        assert kpis["open_tasks"] == 0
        assert kpis["overdue_tasks"] == 0
        assert kpis["completed_tasks"] == 0
        assert kpis["total_tasks"] == 0
        assert kpis["team_members"] == 2  # admin + employee

    def test_active_projects_count(self, tenant, auth_client, project_factory, customer_factory):
        project_factory(tenant.company, status=ProjectStatus.PLANNING)
        project_factory(tenant.company, status=ProjectStatus.IN_PROGRESS)
        project_factory(tenant.company, status=ProjectStatus.ON_HOLD)
        project_factory(tenant.company, status=ProjectStatus.COMPLETED)
        project_factory(tenant.company, status=ProjectStatus.ARCHIVED)

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        kpis = resp.data["kpis"]
        # active = PLANNING + IN_PROGRESS + ON_HOLD = 3
        assert kpis["active_projects"] == 3
        assert kpis["total_projects"] == 5

    def test_open_tasks_count(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, status=TaskStatus.TODO)
        task_factory(tenant.company, status=TaskStatus.IN_PROGRESS)
        task_factory(tenant.company, status=TaskStatus.IN_REVIEW)
        task_factory(tenant.company, status=TaskStatus.DONE)
        task_factory(tenant.company, status=TaskStatus.CANCELLED)

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        kpis = resp.data["kpis"]
        # open = TODO + IN_PROGRESS + IN_REVIEW = 3
        assert kpis["open_tasks"] == 3
        assert kpis["completed_tasks"] == 1
        assert kpis["total_tasks"] == 5

    def test_overdue_tasks_count(self, tenant, auth_client, task_factory):
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        # Overdue: open task with due_date in the past
        task_factory(
            tenant.company,
            title="Overdue open",
            status=TaskStatus.TODO,
            due_date=yesterday,
        )
        # Not overdue: done task with past due_date
        task_factory(
            tenant.company,
            title="Done overdue",
            status=TaskStatus.DONE,
            due_date=yesterday,
        )
        # Not overdue: open task with future due_date
        task_factory(
            tenant.company,
            title="Future",
            status=TaskStatus.IN_PROGRESS,
            due_date=tomorrow,
        )
        # Overdue: in_progress with past due_date
        task_factory(
            tenant.company,
            title="Also overdue",
            status=TaskStatus.IN_PROGRESS,
            due_date=yesterday,
        )

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.data["kpis"]["overdue_tasks"] == 2

    def test_customer_count(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="A")
        customer_factory(tenant.company, name="B")
        customer_factory(tenant.company, name="C")

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.data["kpis"]["total_customers"] == 3

    def test_team_members_count(self, tenant, auth_client, user_factory, membership_factory):
        u = user_factory(email="extra@acme.test")
        membership_factory(u, tenant.company, RoleChoices.MANAGER)

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        # admin + employee + extra = 3
        assert resp.data["kpis"]["team_members"] == 3


# ---------------------------------------------------------------------------
# Status distributions
# ---------------------------------------------------------------------------


class TestStatusDistributions:
    def test_project_status_distribution(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, status=ProjectStatus.PLANNING)
        project_factory(tenant.company, status=ProjectStatus.PLANNING)
        project_factory(tenant.company, status=ProjectStatus.IN_PROGRESS)

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        dist = {d["status"]: d["count"] for d in resp.data["project_status_distribution"]}
        assert dist["PLANNING"] == 2
        assert dist["IN_PROGRESS"] == 1
        assert dist["COMPLETED"] == 0

    def test_task_status_distribution(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, status=TaskStatus.TODO)
        task_factory(tenant.company, status=TaskStatus.TODO)
        task_factory(tenant.company, status=TaskStatus.DONE)

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        dist = {d["status"]: d["count"] for d in resp.data["task_status_distribution"]}
        assert dist["TODO"] == 2
        assert dist["DONE"] == 1
        assert dist["IN_PROGRESS"] == 0


# ---------------------------------------------------------------------------
# Recent items
# ---------------------------------------------------------------------------


class TestRecentItems:
    def test_recent_projects_limited_to_5(self, tenant, auth_client, project_factory):
        for i in range(7):
            project_factory(tenant.company, name=f"P{i}")

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert len(resp.data["recent_projects"]) == 5

    def test_recent_tasks_limited_to_10(self, tenant, auth_client, task_factory):
        for i in range(15):
            task_factory(tenant.company, title=f"T{i}")

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert len(resp.data["recent_tasks"]) == 10

    def test_recent_projects_ordered_by_updated_at(self, tenant, auth_client, project_factory):
        p1 = project_factory(tenant.company, name="First")
        project_factory(tenant.company, name="Second")
        # Touch p1 to make it more recent
        p1.save()

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        names = [p["name"] for p in resp.data["recent_projects"]]
        assert names[0] == "First"

    def test_activity_mixed_and_limited(self, tenant, auth_client, project_factory, task_factory):
        for i in range(6):
            project_factory(tenant.company, name=f"P{i}")
        for i in range(8):
            task_factory(tenant.company, title=f"T{i}")

        resp = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        assert len(resp.data["activity"]) == 10
        types = {a["type"] for a in resp.data["activity"]}
        assert "project" in types or "task" in types


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    def test_company_a_sees_only_own_data(
        self,
        tenant,
        auth_client,
        user_factory,
        company_factory,
        membership_factory,
        project_factory,
        task_factory,
        customer_factory,
    ):
        # Create a second company
        company_b = company_factory(name="Company B", slug="company-b")
        admin_b = user_factory(email="admin@b.test")
        membership_factory(admin_b, company_b, RoleChoices.ADMIN)

        # Populate both companies
        project_factory(tenant.company, name="A-Project")
        project_factory(company_b, name="B-Project")
        task_factory(tenant.company, title="A-Task")
        task_factory(company_b, title="B-Task")
        customer_factory(tenant.company, name="A-Customer")
        customer_factory(company_b, name="B-Customer")

        resp_a = _dashboard(auth_client(tenant.admin, tenant.company), tenant.company)
        resp_b = _dashboard(auth_client(admin_b, company_b), company_b)

        # Company A
        assert resp_a.data["kpis"]["total_projects"] == 1
        assert resp_a.data["kpis"]["total_tasks"] == 1
        assert resp_a.data["kpis"]["total_customers"] == 1
        assert resp_a.data["recent_projects"][0]["name"] == "A-Project"
        assert resp_a.data["recent_tasks"][0]["title"] == "A-Task"

        # Company B
        assert resp_b.data["kpis"]["total_projects"] == 1
        assert resp_b.data["kpis"]["total_tasks"] == 1
        assert resp_b.data["kpis"]["total_customers"] == 1
        assert resp_b.data["recent_projects"][0]["name"] == "B-Project"
        assert resp_b.data["recent_tasks"][0]["title"] == "B-Task"

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/v1/dashboard/")
        assert resp.status_code in (401, 403)

    def test_user_without_membership_returns_403(self, api_client, user_factory, company_factory):
        orphan = user_factory(email="orphan@test.com")
        api_client.force_authenticate(user=orphan)
        resp = api_client.get("/api/v1/dashboard/")
        assert resp.status_code == 403
