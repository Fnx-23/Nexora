"""Tests for the time tracking feature."""

from datetime import time

import pytest
from apps.companies.models import RoleChoices

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TIME_ENTRIES_URL = "/api/v1/time-entries/"


def _list(client, company, **params):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(TIME_ENTRIES_URL, params)


def _create(client, company, payload):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.post(TIME_ENTRIES_URL, payload)


def _detail(client, company, entry_id, **kwargs):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    method = kwargs.pop("method", "get")
    url = f"{TIME_ENTRIES_URL}{entry_id}/"
    if method == "patch":
        return client.patch(url, kwargs.get("data", {}))
    if method == "delete":
        return client.delete(url)
    return client.get(url)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestTimeEntryCRUD:
    def test_create_time_entry(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "10:30",
                "description": "Morning standup",
            },
        )
        assert resp.status_code == 201
        data = resp.data
        assert data["project"] == project.id
        assert data["user"] == tenant.admin.id
        assert data["description"] == "Morning standup"
        assert data["duration"] is not None

    def test_duration_auto_calculated(self, tenant, auth_client, project_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "11:30",
            },
        )
        assert resp.status_code == 201
        assert "2:30:00" in resp.data["duration"]

    def test_list_time_entries(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-16")

        resp = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_retrieve_time_entry(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        entry = time_entry_factory(tenant.company, tenant.admin, project)

        resp = _detail(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            entry.id,
        )
        assert resp.status_code == 200
        assert resp.data["id"] == str(entry.id)

    def test_update_time_entry(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        entry = time_entry_factory(tenant.company, tenant.admin, project)

        resp = _detail(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            entry.id,
            method="patch",
            data={"description": "Updated description"},
        )
        assert resp.status_code == 200
        assert resp.data["description"] == "Updated description"

    def test_delete_time_entry_requires_manager(
        self, tenant, auth_client, project_factory, time_entry_factory
    ):
        project = project_factory(tenant.company)
        entry = time_entry_factory(tenant.company, tenant.admin, project)

        resp = _detail(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            entry.id,
            method="delete",
        )
        assert resp.status_code == 204

    def test_employee_cannot_delete(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        entry = time_entry_factory(tenant.company, tenant.employee, project)

        resp = _detail(
            auth_client(tenant.employee, tenant.company),
            tenant.company,
            entry.id,
            method="delete",
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Duration calculations
# ---------------------------------------------------------------------------


class TestDurationCalculations:
    def test_duration_30_minutes(self, tenant, auth_client, project_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "09:30",
            },
        )
        assert resp.status_code == 201
        assert "0:30:00" in resp.data["duration"]

    def test_duration_without_end_time(self, tenant, auth_client, project_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
            },
        )
        assert resp.status_code == 201
        assert resp.data["duration"] is None

    def test_duration_recalculated_when_times_edited(self, tenant, auth_client, project_factory):
        """Regression: editing start/end must recompute the stored duration.

        Create 01:00 -> 02:00 (1h), then update end to 04:00 and expect 3h in
        both the API response and the database.
        """
        from datetime import timedelta

        from apps.time_tracking.models import TimeEntry

        project = project_factory(tenant.company)
        client = auth_client(tenant.admin, tenant.company)

        # Create 01:00 -> 02:00 (1h)
        create = _create(
            client,
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "01:00",
                "end_time": "02:00",
            },
        )
        assert create.status_code == 201
        assert "1:00:00" in create.data["duration"]
        entry_id = create.data["id"]

        # DB reflects 1h on creation
        db_entry = TimeEntry.objects.get(id=entry_id)
        assert db_entry.duration == timedelta(hours=1)

        # Update end to 04:00 -> duration must become 3h
        update = _detail(
            client,
            tenant.company,
            entry_id,
            method="patch",
            data={"end_time": "04:00"},
        )
        assert update.status_code == 200
        assert "3:00:00" in update.data["duration"]

        # DB reflects 3h after update
        db_entry.refresh_from_db()
        assert db_entry.duration == timedelta(hours=3)

    def test_duration_recalculated_when_start_edited(self, tenant, auth_client, project_factory):
        """Regression: editing start_time also recomputes duration."""
        from datetime import timedelta

        from apps.time_tracking.models import TimeEntry

        project = project_factory(tenant.company)
        client = auth_client(tenant.admin, tenant.company)

        create = _create(
            client,
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "11:00",
            },
        )
        assert create.status_code == 201
        assert "2:00:00" in create.data["duration"]
        entry_id = create.data["id"]

        # Move start later (10:00 -> 11:00 = 1h)
        update = _detail(
            client,
            tenant.company,
            entry_id,
            method="patch",
            data={"start_time": "10:00"},
        )
        assert update.status_code == 200
        assert "1:00:00" in update.data["duration"]
        assert TimeEntry.objects.get(id=entry_id).duration == timedelta(hours=1)

    def test_summary_uses_updated_duration(
        self, tenant, auth_client, project_factory, time_entry_factory
    ):
        """Regression: summary totals must reflect an edited entry's duration."""
        from datetime import timedelta

        from apps.time_tracking.models import TimeEntry

        project = project_factory(tenant.company, name="Web App")
        entry = time_entry_factory(
            tenant.company,
            tenant.admin,
            project,
            date="2025-06-15",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        client = auth_client(tenant.admin, tenant.company)

        resp_before = client.get(f"{TIME_ENTRIES_URL}summary/")
        assert resp_before.status_code == 200
        assert resp_before.data["total_duration_minutes"] == 60.0

        # Edit end to 04:00 -> duration 7h (420 min), total becomes 420
        _detail(
            client,
            tenant.company,
            entry.id,
            method="patch",
            data={"end_time": "16:00"},
        )
        assert TimeEntry.objects.get(id=entry.id).duration == timedelta(hours=7)

        resp_after = client.get(f"{TIME_ENTRIES_URL}summary/")
        assert resp_after.status_code == 200
        assert resp_after.data["total_duration_minutes"] == 420.0
        assert resp_after.data["by_project"][0]["total_minutes"] == 420.0
        by_date = {d["date"]: d["total_minutes"] for d in resp_after.data["by_date"]}
        assert by_date["2025-06-15"] == 420.0


# ---------------------------------------------------------------------------
# Validation: invalid time ranges
# ---------------------------------------------------------------------------


class TestValidation:
    def test_end_time_before_start_time_rejected(self, tenant, auth_client, project_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "10:00",
                "end_time": "09:00",
            },
        )
        assert resp.status_code == 400
        assert "end_time" in resp.data

    def test_cross_project_task_rejected(self, tenant, auth_client, project_factory, task_factory):
        project_a = project_factory(tenant.company, name="Project A")
        project_b = project_factory(tenant.company, name="Project B")
        task = task_factory(tenant.company, project=project_b)

        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(project_a.id),
                "task": str(task.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "10:00",
            },
        )
        assert resp.status_code == 400

    def test_invalid_project_rejected(self, tenant, auth_client, company_factory, project_factory):
        other_company = company_factory(name="Other")
        other_project = project_factory(other_company)

        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "project": str(other_project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "10:00",
            },
        )
        assert resp.status_code == 400

    def test_missing_project_rejected(self, tenant, auth_client):
        resp = _create(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            {
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "10:00",
            },
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class TestPermissions:
    def test_employee_sees_own_entries_only(
        self, tenant, auth_client, project_factory, time_entry_factory
    ):
        project = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.employee, project, date="2025-06-16")

        resp = _list(auth_client(tenant.employee, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["user"] == tenant.employee.id

    def test_manager_sees_all_entries(
        self,
        tenant,
        auth_client,
        project_factory,
        time_entry_factory,
        user_factory,
        membership_factory,
    ):
        project = project_factory(tenant.company)
        manager = user_factory(email="manager@test.com")
        membership_factory(manager, tenant.company, RoleChoices.MANAGER)

        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.employee, project, date="2025-06-16")

        resp = _list(auth_client(manager, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_admin_sees_all_entries(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.employee, project, date="2025-06-16")

        resp = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_employee_can_create_own_entry(self, tenant, auth_client, project_factory):
        project = project_factory(tenant.company)
        resp = _create(
            auth_client(tenant.employee, tenant.company),
            tenant.company,
            {
                "project": str(project.id),
                "date": "2025-06-15",
                "start_time": "09:00",
                "end_time": "10:00",
            },
        )
        assert resp.status_code == 201
        assert resp.data["user"] == tenant.employee.id


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    def test_company_a_cannot_see_company_b_entries(
        self,
        tenant,
        auth_client,
        project_factory,
        time_entry_factory,
        company_factory,
        user_factory,
        membership_factory,
    ):
        company_b = company_factory(name="Company B", slug="company-b")
        admin_b = user_factory(email="admin@b.test")
        membership_factory(admin_b, company_b, RoleChoices.ADMIN)
        project_b = project_factory(company_b)

        project_a = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project_a)
        time_entry_factory(company_b, admin_b, project_b)

        resp_a = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        resp_b = _list(auth_client(admin_b, company_b), company_b)

        assert resp_a.data["count"] == 1
        assert resp_b.data["count"] == 1
        assert resp_a.data["results"][0]["user"] == tenant.admin.id
        assert resp_b.data["results"][0]["user"] == admin_b.id

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(TIME_ENTRIES_URL)
        assert resp.status_code in (401, 403)

    def test_no_membership_returns_403(self, api_client, user_factory):
        orphan = user_factory(email="orphan@test.com")
        api_client.force_authenticate(user=orphan)
        resp = api_client.get(TIME_ENTRIES_URL)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    def test_filter_by_project(self, tenant, auth_client, project_factory, time_entry_factory):
        p1 = project_factory(tenant.company, name="P1")
        p2 = project_factory(tenant.company, name="P2")
        time_entry_factory(tenant.company, tenant.admin, p1)
        time_entry_factory(tenant.company, tenant.admin, p2)

        resp = _list(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            project=str(p1.id),
        )
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["project"] == p1.id

    def test_filter_by_date_range(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-10")
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-20")

        resp = _list(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            date_from="2025-06-12",
            date_to="2025-06-18",
        )
        assert resp.data["count"] == 1

    def test_filter_by_user(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company)
        time_entry_factory(tenant.company, tenant.admin, project, date="2025-06-15")
        time_entry_factory(tenant.company, tenant.employee, project, date="2025-06-15")

        resp = _list(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            user=str(tenant.employee.id),
        )
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["user"] == tenant.employee.id


# ---------------------------------------------------------------------------
# Summary endpoint
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_empty(self, tenant, auth_client, project_factory):
        resp = auth_client(tenant.admin, tenant.company).get(f"{TIME_ENTRIES_URL}summary/")
        assert resp.status_code == 200
        assert resp.data["total_entries"] == 0
        assert resp.data["total_duration_minutes"] == 0

    def test_summary_calculations(self, tenant, auth_client, project_factory, time_entry_factory):
        project = project_factory(tenant.company, name="Web App")
        time_entry_factory(
            tenant.company,
            tenant.admin,
            project,
            date="2025-06-15",
            start_time=time(9, 0),
            end_time=time(10, 30),
        )
        time_entry_factory(
            tenant.company,
            tenant.admin,
            project,
            date="2025-06-15",
            start_time=time(14, 0),
            end_time=time(15, 0),
        )
        time_entry_factory(
            tenant.company,
            tenant.employee,
            project,
            date="2025-06-16",
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        resp = auth_client(tenant.admin, tenant.company).get(f"{TIME_ENTRIES_URL}summary/")
        assert resp.status_code == 200
        assert resp.data["total_entries"] == 3
        # 90 + 60 + 120 = 270 minutes
        assert resp.data["total_duration_minutes"] == 270.0
        assert len(resp.data["by_project"]) == 1
        assert resp.data["by_project"][0]["project_name"] == "Web App"
        assert resp.data["by_project"][0]["total_minutes"] == 270.0
        assert len(resp.data["by_date"]) == 2

    def test_summary_respects_employee_scope(
        self, tenant, auth_client, project_factory, time_entry_factory
    ):
        project = project_factory(tenant.company)
        time_entry_factory(
            tenant.company,
            tenant.admin,
            project,
            date="2025-06-15",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        time_entry_factory(
            tenant.company,
            tenant.employee,
            project,
            date="2025-06-16",
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        resp = auth_client(tenant.employee, tenant.company).get(f"{TIME_ENTRIES_URL}summary/")
        assert resp.status_code == 200
        assert resp.data["total_entries"] == 1
        assert resp.data["total_duration_minutes"] == 180.0
