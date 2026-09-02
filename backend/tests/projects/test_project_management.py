"""
Tests for the advanced project-management module.

Covers the derived metrics (progress, health), project members (CRUD + tenant
isolation + permissions), archive/restore lifecycle, and project aggregates.
"""

from datetime import timedelta

import pytest
from apps.activities.models import ActivityAction
from apps.companies.models import Membership, RoleChoices
from apps.projects.models import ProjectMember, ProjectStatus
from apps.projects.services import (
    ProjectHealth,
    compute_health,
    compute_progress,
    metrics_for_project,
)
from django.utils import timezone

today = timezone.localdate()

# ---------------------------------------------------------------------------
# Progress calculation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProgressCalculation:
    def test_zero_tasks_returns_zero(self):
        assert compute_progress(0, 0) == 0

    def test_some_done(self):
        assert compute_progress(3, 5) == 60

    def test_all_done(self):
        assert compute_progress(5, 5) == 100

    def test_none_done(self):
        assert compute_progress(0, 4) == 0

    def test_rounds(self):
        assert compute_progress(1, 3) == 33

    def test_negative_count_guarded(self):
        assert compute_progress(0, -1) == 0

    def test_metrics_zero_task_project_health_is_not_started(self, tenant, project_factory):
        p = project_factory(tenant.company)
        metrics = metrics_for_project(p)
        assert metrics.task_count == 0
        assert metrics.progress == 0
        assert metrics.health == ProjectHealth.NOT_STARTED


# ---------------------------------------------------------------------------
# Health computation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHealth:
    def test_completed_project_is_completed(self):
        assert (
            compute_health(ProjectStatus.COMPLETED.value, None, 100, 0)
            == ProjectHealth.COMPLETED.value
        )

    def test_overdue_tasks_force_overdue(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, None, 50, 2)
            == ProjectHealth.OVERDUE.value
        )

    def test_past_deadline_is_overdue(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, today - timedelta(days=1), 50, 0)
            == ProjectHealth.OVERDUE.value
        )

    def test_zero_progress_is_not_started(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, None, 0, 0)
            == ProjectHealth.NOT_STARTED.value
        )

    def test_close_deadline_low_progress_is_at_risk(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, today + timedelta(days=3), 20, 0)
            == ProjectHealth.AT_RISK.value
        )

    def test_far_deadline_is_on_track(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, today + timedelta(days=30), 20, 0)
            == ProjectHealth.ON_TRACK.value
        )

    def test_high_progress_near_deadline_is_on_track(self):
        assert (
            compute_health(ProjectStatus.IN_PROGRESS.value, today + timedelta(days=3), 90, 0)
            == ProjectHealth.ON_TRACK.value
        )


# ---------------------------------------------------------------------------
# Project aggregates (metrics from actual data)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectAggregates:
    def test_counts_and_progress_reflect_tasks(self, tenant, project_factory, task_factory):
        p = project_factory(tenant.company)
        task_factory(tenant.company, project=p, status="TODO")
        task_factory(tenant.company, project=p, status="IN_PROGRESS")
        task_factory(tenant.company, project=p, status="DONE")

        metrics = metrics_for_project(p)
        assert metrics.task_count == 3
        assert metrics.todo_count == 1
        assert metrics.in_progress_count == 1
        assert metrics.done_count == 1
        assert metrics.progress == 33

    def test_overdue_count(self, tenant, project_factory, task_factory):
        p = project_factory(tenant.company)
        task_factory(tenant.company, project=p, status="TODO", due_date=today - timedelta(days=2))
        task_factory(tenant.company, project=p, status="DONE", due_date=today - timedelta(days=2))
        task_factory(
            tenant.company, project=p, status="IN_PROGRESS", due_date=today - timedelta(days=2)
        )

        metrics = metrics_for_project(p)
        # Only open (non-DONE/CANCELLED) tasks with a past due date count.
        assert metrics.overdue_count == 2

    def test_no_tracked_hours(self, tenant, project_factory):
        p = project_factory(tenant.company)
        assert metrics_for_project(p).tracked_hours == 0.0

    def test_tracked_hours_summed(self, tenant, project_factory, time_entry_factory, user_factory):
        p = project_factory(tenant.company)
        u = user_factory(email="tracer@test.com")
        time_entry_factory(tenant.company, user=u, project=p)  # 1 hour by default
        time_entry_factory(tenant.company, user=u, project=p)
        assert metrics_for_project(p).tracked_hours == 2.0

    def test_cancelled_tasks_not_counted_as_done(self, tenant, project_factory, task_factory):
        p = project_factory(tenant.company)
        task_factory(tenant.company, project=p, status="DONE")
        task_factory(tenant.company, project=p, status="CANCELLED")
        task_factory(tenant.company, project=p, status="TODO")
        metrics = metrics_for_project(p)
        assert metrics.done_count == 1
        assert metrics.progress == 33


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMembers:
    def test_list_members(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="assignee@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/members/")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["user"] == str(member.id)

    def test_add_member(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="add-me@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)

        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/members/",
            {"user": str(member.id)},
            format="json",
        )
        assert resp.status_code == 201
        assert ProjectMember.objects.filter(project=p, user=member).exists()

    def test_duplicate_member_rejected(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="dup@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/members/",
            {"user": str(member.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_remove_member(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="bye@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        pm = ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        resp = auth_client(tenant.admin, tenant.company).delete(
            f"/api/v1/projects/{p.id}/members/{pm.id}/",
        )
        assert resp.status_code == 204
        assert not ProjectMember.objects.filter(id=pm.id).exists()

    def test_employee_cannot_add_member(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="emp@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)

        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/projects/{p.id}/members/",
            {"user": str(member.id)},
            format="json",
        )
        assert resp.status_code == 403

    def test_employee_can_view_members(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="view@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        resp = auth_client(tenant.employee, tenant.company).get(f"/api/v1/projects/{p.id}/members/")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Member tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMemberTenantIsolation:
    def test_cannot_add_foreign_company_user(
        self,
        auth_client,
        project_factory,
        user_factory,
        company_factory,
        membership_factory,
        two_tenants,
    ):
        p = project_factory(two_tenants["a"]["company"])
        foreign_user = two_tenants["b"]["user"]

        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/projects/{p.id}/members/",
            {"user": str(foreign_user.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "user" in resp.json()

    def test_cannot_list_members_of_foreign_project(
        self, auth_client, two_tenants, project_factory
    ):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).get(
            f"/api/v1/projects/{foreign.id}/members/",
        )
        assert resp.status_code == 404

    def test_cannot_add_member_to_foreign_project(self, auth_client, two_tenants, project_factory):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/projects/{foreign.id}/members/",
            {"user": str(two_tenants["a"]["user"].id)},
            format="json",
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Archive / restore lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestArchiveRestore:
    def test_restore_archived_project(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, status=ProjectStatus.ARCHIVED)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/restore/",
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == ProjectStatus.PLANNING
        p.refresh_from_db()
        assert p.status == ProjectStatus.PLANNING

    def test_restore_to_specific_status(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, status=ProjectStatus.ARCHIVED)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/restore/",
            {"status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_restore_non_archived_returns_400(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, status=ProjectStatus.IN_PROGRESS)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/restore/",
            format="json",
        )
        assert resp.status_code == 400

    def test_restore_requires_manager_or_admin(self, tenant, auth_client, project_factory):
        employee = tenant.employee
        p = project_factory(tenant.company, status=ProjectStatus.ARCHIVED)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)
        resp = auth_client(employee, tenant.company).post(
            f"/api/v1/projects/{p.id}/restore/",
            format="json",
        )
        assert resp.status_code == 403

    def test_cannot_restore_foreign_project(self, auth_client, two_tenants, project_factory):
        foreign = project_factory(two_tenants["b"]["company"], status=ProjectStatus.ARCHIVED)
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/projects/{foreign.id}/restore/",
            format="json",
        )
        assert resp.status_code == 404

    def test_archive_sets_archived_status(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/archive/",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == ProjectStatus.ARCHIVED


# ---------------------------------------------------------------------------
# Rich detail view (metrics, members, activity)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDetailView:
    def test_detail_includes_metrics(self, tenant, auth_client, project_factory, task_factory):
        p = project_factory(tenant.company)
        task_factory(tenant.company, project=p, status="DONE")
        task_factory(tenant.company, project=p, status="TODO")

        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")
        body = resp.json()
        assert body["task_count"] == 2
        assert body["done_count"] == 1
        assert body["todo_count"] == 1
        assert body["progress"] == 50
        assert "health" in body
        assert "tracked_hours" in body
        assert "overdue_count" in body

    def test_detail_includes_members(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        p = project_factory(tenant.company)
        member = user_factory(email="detail-member@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")
        body = resp.json()
        assert len(body["members"]) == 1
        assert body["members"][0]["user"] == str(member.id)
        assert body["members"][0]["email"] == "detail-member@test.com"

    def test_detail_includes_recent_activity(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")
        body = resp.json()
        assert isinstance(body["recent_activity"], list)
        assert body["recent_activity"][0]["action"] == ActivityAction.PROJECT_CREATED

    def test_list_includes_aggregate_metrics(
        self, tenant, auth_client, project_factory, task_factory
    ):
        p = project_factory(tenant.company)
        task_factory(tenant.company, project=p, status="DONE")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/projects/")
        row = resp.json()["results"][0]
        assert row["task_count"] == 1
        assert row["progress"] == 100
        assert "health" in row
        assert "member_count" in row


# ---------------------------------------------------------------------------
# Member activity recording
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMemberActivity:
    def test_add_member_records_activity(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        from apps.activities.models import Activity

        p = project_factory(tenant.company)
        member = user_factory(email="activity@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)

        auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/members/",
            {"user": str(member.id)},
            format="json",
        )

        assert Activity.objects.filter(
            entity_type="project", entity_id=p.id, action=ActivityAction.PROJECT_MEMBER_ADDED
        ).exists()

    def test_remove_member_records_activity(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        from apps.activities.models import Activity

        p = project_factory(tenant.company)
        member = user_factory(email="remove-activity@test.com")
        membership_factory(member, tenant.company, RoleChoices.EMPLOYEE)
        pm = ProjectMember.objects.create(project=p, user=member, company=tenant.company)

        auth_client(tenant.admin, tenant.company).delete(
            f"/api/v1/projects/{p.id}/members/{pm.id}/",
        )

        assert Activity.objects.filter(
            entity_type="project", entity_id=p.id, action=ActivityAction.PROJECT_MEMBER_REMOVED
        ).exists()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    """Company A (with a member) and Company B (with its own member)."""
    admin_a = user_factory(email="admin@a-mgmt.test")
    admin_b = user_factory(email="admin@b-mgmt.test")
    company_a = company_factory(name="Company A Mgmt", slug="company-a-mgmt")
    company_b = company_factory(name="Company B Mgmt", slug="company-b-mgmt")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
