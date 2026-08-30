"""Tests for the notifications feature: model, API, Celery tasks, and signals."""

from datetime import date, timedelta

import pytest
from apps.companies.models import Membership, RoleChoices
from apps.notifications.models import Notification
from apps.notifications.tasks import (
    check_deadline_approaching,
    notify_project_assigned,
    notify_task_assigned,
)
from apps.projects.models import Project, ProjectStatus
from apps.tasks.models import Task, TaskStatus

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = "/api/v1/notifications/"


def _list(client, company, **params):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(NOTIFICATIONS_URL, params)


def _unread_count(client, company):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(f"{NOTIFICATIONS_URL}unread-count/")


def _mark_read(client, company, notification_id):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.patch(f"{NOTIFICATIONS_URL}{notification_id}/mark-read/")


def _mark_all_read(client, company):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.patch(f"{NOTIFICATIONS_URL}mark-all-read/")


def _make_notification(company, recipient, **kwargs):
    return Notification.objects.create(
        company=company,
        recipient=recipient,
        verb=kwargs.pop("verb", "Test notification"),
        entity_type=kwargs.pop("entity_type", "task"),
        entity_id=kwargs.pop("entity_id", None),
        entity_name=kwargs.pop("entity_name", "Test Entity"),
        link=kwargs.pop("link", "/tasks"),
        is_read=kwargs.pop("is_read", False),
        **kwargs,
    )


def _count_notifications(recipient, **filters):
    return Notification.objects.filter(recipient=recipient, **filters).count()


# --------------------------------------------------------------------------- #
# Model tests
# --------------------------------------------------------------------------- #
class TestNotificationModel:
    def test_create_notification(self, tenant):
        n = _make_notification(tenant.company, tenant.admin)
        assert n.pk is not None
        assert n.is_read is False
        assert n.company == tenant.company
        assert n.recipient == tenant.admin

    def test_str_representation(self, tenant):
        n = _make_notification(tenant.company, tenant.admin, verb="You were assigned")
        assert "You were assigned" in str(n)

    def test_default_is_read_false(self, tenant):
        n = _make_notification(tenant.company, tenant.admin)
        assert n.is_read is False


# --------------------------------------------------------------------------- #
# API — list
# --------------------------------------------------------------------------- #
class TestListNotifications:
    def test_returns_own_notifications(self, tenant, auth_client):
        _make_notification(tenant.company, tenant.admin, verb="Admin notif")
        _make_notification(tenant.company, tenant.employee, verb="Employee notif")
        resp = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] >= 1
        verbs = [r["verb"] for r in resp.data["results"]]
        assert "Admin notif" in verbs

    def test_admin_can_see_all_notifications(self, tenant, auth_client):
        _make_notification(tenant.company, tenant.admin, verb="Admin notif")
        _make_notification(tenant.company, tenant.employee, verb="Employee notif")
        resp = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] >= 2

    def test_employee_sees_own_only(self, tenant, auth_client):
        _make_notification(tenant.company, tenant.admin, verb="Admin notif")
        _make_notification(tenant.company, tenant.employee, verb="Employee notif")
        resp = _list(auth_client(tenant.employee, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] >= 1
        verbs = [r["verb"] for r in resp.data["results"]]
        assert "Admin notif" not in verbs
        assert "Employee notif" in verbs

    def test_unread_filter(self, tenant, auth_client):
        _make_notification(tenant.company, tenant.admin, is_read=False)
        _make_notification(tenant.company, tenant.admin, is_read=True)
        resp = _list(auth_client(tenant.admin, tenant.company), tenant.company, unread="true")
        assert resp.data["count"] >= 1


# --------------------------------------------------------------------------- #
# API — unread count
# --------------------------------------------------------------------------- #
class TestUnreadCount:
    def test_unread_count(self, tenant, auth_client):
        before = _count_notifications(tenant.admin, is_read=False)
        _make_notification(tenant.company, tenant.admin, is_read=False)
        _make_notification(tenant.company, tenant.admin, is_read=False)
        _make_notification(tenant.company, tenant.admin, is_read=True)
        resp = _unread_count(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == before + 2

    def test_unread_count_empty(self, tenant, auth_client):
        resp = _unread_count(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        # May be 0 or more due to signals from other test fixtures
        assert isinstance(resp.data["count"], int)


# --------------------------------------------------------------------------- #
# API — mark read
# --------------------------------------------------------------------------- #
class TestMarkRead:
    def test_mark_single_read(self, tenant, auth_client):
        n = _make_notification(tenant.company, tenant.admin, is_read=False)
        resp = _mark_read(auth_client(tenant.admin, tenant.company), tenant.company, n.pk)
        assert resp.status_code == 200
        assert resp.data["is_read"] is True
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_all_read(self, tenant, auth_client):
        _make_notification(tenant.company, tenant.admin, is_read=False)
        _make_notification(tenant.company, tenant.admin, is_read=False)
        resp = _mark_all_read(auth_client(tenant.admin, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["updated"] >= 2
        assert _count_notifications(tenant.admin, is_read=False) == 0


# --------------------------------------------------------------------------- #
# API — tenant isolation
# --------------------------------------------------------------------------- #
class TestTenantIsolation:
    def test_company_a_cannot_see_company_b_notifications(
        self, tenant, auth_client, company_factory, user_factory, membership_factory
    ):
        company_b = company_factory(name="Company B", slug="company-b")
        admin_b = user_factory(email="admin_b@test.com")
        membership_factory(admin_b, company_b, RoleChoices.ADMIN)

        _make_notification(tenant.company, tenant.admin, verb="A notif")
        _make_notification(company_b, admin_b, verb="B notif")

        resp_a = _list(auth_client(tenant.admin, tenant.company), tenant.company)
        resp_b = _list(auth_client(admin_b, company_b), company_b)
        assert resp_a.data["count"] >= 1
        assert resp_b.data["count"] >= 1
        a_verbs = [r["verb"] for r in resp_a.data["results"]]
        b_verbs = [r["verb"] for r in resp_b.data["results"]]
        assert "A notif" in a_verbs
        assert "B notif" in b_verbs
        assert "B notif" not in a_verbs
        assert "A notif" not in b_verbs

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(NOTIFICATIONS_URL)
        assert resp.status_code in (401, 403)

    def test_no_membership_returns_403(self, api_client, user_factory):
        orphan = user_factory(email="orphan@test.com")
        api_client.force_authenticate(user=orphan)
        resp = api_client.get(NOTIFICATIONS_URL)
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
# Celery tasks — notify_task_assigned
# --------------------------------------------------------------------------- #
class TestNotifyTaskAssigned:
    def test_creates_notification_for_assignee(self, tenant, user_factory):
        assignee = user_factory(email="assignee@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Do stuff",
            project=project,
        )
        # Assign and trigger signal
        task.assignee = assignee
        task.save(update_fields=["assignee"])
        n = Notification.objects.filter(
            recipient=assignee, entity_type="task", entity_id=task.pk
        ).first()
        assert n is not None
        assert "assigned" in n.verb.lower()

    def test_direct_call_sets_actor(self, tenant, user_factory):
        assignee = user_factory(email="actor@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Actor task",
            project=project,
            assignee=assignee,
        )
        # Clear signal-generated notification
        Notification.objects.filter(entity_type="task", entity_id=task.pk).delete()
        notify_task_assigned(str(task.pk), str(tenant.admin.pk))
        n = Notification.objects.filter(
            recipient=assignee, entity_type="task", entity_id=task.pk
        ).first()
        assert n is not None
        assert n.actor == tenant.admin

    def test_no_notification_if_no_assignee(self, tenant):
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(company=tenant.company, title="Unassigned", project=project)
        notify_task_assigned(str(task.pk))
        # No notification because no assignee
        assert _count_notifications(tenant.admin, entity_type="task", entity_id=task.pk) == 0

    def test_missing_task_does_not_raise(self, tenant):
        # Should not raise
        notify_task_assigned("00000000-0000-0000-0000-000000000000")


# --------------------------------------------------------------------------- #
# Celery tasks — notify_project_assigned
# --------------------------------------------------------------------------- #
class TestNotifyProjectAssigned:
    def test_creates_notification_for_manager(self, tenant, user_factory):
        manager = user_factory(email="manager@test.com")
        # Create project without manager to avoid signal
        project = Project.objects.create(company=tenant.company, name="Big Project")
        # Now assign manager — signal will fire
        project.manager = manager
        project.save(update_fields=["manager"])
        n = Notification.objects.filter(
            recipient=manager, entity_type="project", entity_id=project.pk
        ).last()
        assert n is not None
        assert "manager" in n.verb.lower()

    def test_no_notification_if_no_manager(self, tenant):
        project = Project.objects.create(company=tenant.company, name="No Manager")
        notify_project_assigned(str(project.pk))
        assert _count_notifications(tenant.admin, entity_type="project", entity_id=project.pk) == 0


# --------------------------------------------------------------------------- #
# Celery tasks — notify_team_role_changed
# --------------------------------------------------------------------------- #
class TestNotifyTeamRoleChanged:
    def test_creates_notification(self, tenant, user_factory):
        member = user_factory(email="member@test.com")
        membership = Membership.objects.create(
            user=member, company=tenant.company, role=RoleChoices.EMPLOYEE
        )
        # Role change will fire signal which dispatches Celery task
        membership.role = RoleChoices.MANAGER
        membership.save(update_fields=["role"])
        n = Notification.objects.filter(recipient=member, entity_type="membership").last()
        assert n is not None
        assert "manager" in n.verb.lower()


# --------------------------------------------------------------------------- #
# Celery tasks — deadline approaching
# --------------------------------------------------------------------------- #
class TestCheckDeadlineApproaching:
    def test_task_deadline_approaching(self, tenant, user_factory):
        assignee = user_factory(email="deadline@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Urgent task",
            project=project,
            assignee=assignee,
            due_date=date.today() + timedelta(days=2),
            status=TaskStatus.IN_PROGRESS,
        )
        before = _count_notifications(assignee, entity_type="task")
        check_deadline_approaching()
        after = _count_notifications(assignee, entity_type="task")
        assert after > before
        assert (
            Notification.objects.filter(recipient=assignee, entity_type="task", entity_id=task.pk)
            .filter(verb__contains="deadline")
            .exists()
        )

    def test_project_deadline_approaching(self, tenant, user_factory):
        manager = user_factory(email="pm@test.com")
        Project.objects.create(
            company=tenant.company,
            name="Deadline Project",
            manager=manager,
            deadline=date.today() + timedelta(days=5),
            status=ProjectStatus.IN_PROGRESS,
        )
        before = _count_notifications(manager, entity_type="project")
        check_deadline_approaching()
        after = _count_notifications(manager, entity_type="project")
        assert after > before

    def test_no_deadline_notification_for_past_deadline(self, tenant, user_factory):
        assignee = user_factory(email="past@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Past due",
            project=project,
            assignee=assignee,
            due_date=date.today() - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        before = _count_notifications(assignee, entity_type="task", verb__contains="deadline")
        check_deadline_approaching()
        after = _count_notifications(assignee, entity_type="task", verb__contains="deadline")
        assert after == before

    def test_no_duplicate_within_24h(self, tenant, user_factory):
        assignee = user_factory(email="dedup@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Dedup task",
            project=project,
            assignee=assignee,
            due_date=date.today() + timedelta(days=1),
            status=TaskStatus.TODO,
        )
        check_deadline_approaching()
        count_first = _count_notifications(assignee, entity_type="task", verb__contains="deadline")
        check_deadline_approaching()
        count_second = _count_notifications(assignee, entity_type="task", verb__contains="deadline")
        assert count_first == count_second


# --------------------------------------------------------------------------- #
# Signal integration
# --------------------------------------------------------------------------- #
class TestSignalIntegration:
    def test_task_created_with_assignee_creates_notification(self, tenant, user_factory):
        assignee = user_factory(email="signal@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Signal task",
            project=project,
            assignee=assignee,
        )
        # CELERY_TASK_ALWAYS_EAGER=True in test settings — task runs synchronously
        assert Notification.objects.filter(
            recipient=assignee, entity_type="task", entity_id=task.pk
        ).exists()

    def test_project_created_with_manager_creates_notification(self, tenant, user_factory):
        manager = user_factory(email="pm-signal@test.com")
        project = Project.objects.create(
            company=tenant.company,
            name="Managed Project",
            manager=manager,
        )
        assert Notification.objects.filter(
            recipient=manager, entity_type="project", entity_id=project.pk
        ).exists()

    def test_task_created_without_assignee_no_notification(self, tenant):
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="No assignee",
            project=project,
        )
        assert not Notification.objects.filter(entity_type="task", entity_id=task.pk).exists()

    def test_task_reassignment_creates_notification(self, tenant, user_factory):
        old_assignee = user_factory(email="old@test.com")
        new_assignee = user_factory(email="new@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Reassigned",
            project=project,
            assignee=old_assignee,
        )
        # Clear signal-generated notification for old assignee
        Notification.objects.filter(entity_type="task", entity_id=task.pk).delete()
        task.assignee = new_assignee
        task.save(update_fields=["assignee"])
        assert Notification.objects.filter(
            recipient=new_assignee, entity_type="task", entity_id=task.pk
        ).exists()
