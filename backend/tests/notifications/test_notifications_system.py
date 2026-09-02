"""Tests for the production notification system.

Covers each notification scenario the feature promises, the deduplication
strategy for scheduled reminders, preferences gating, tenant isolation,
permission boundaries, read state, navigation targets (link field), and the
Celery beat schedule wiring.
"""

from datetime import date, timedelta

import pytest
from apps.companies.models import Company, InvitationStatus, Membership, RoleChoices
from apps.notifications.models import Notification, NotificationCategory, NotificationPreference
from apps.notifications.services import create_notification
from apps.notifications.tasks import (
    check_deadline_approaching,
    notify_invitation_received,
    notify_project_member_added,
    notify_task_commented,
)
from apps.projects.models import Project, ProjectMember, ProjectStatus
from apps.tasks.models import Task, TaskComment, TaskStatus
from django.conf import settings
from django.utils import timezone

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = "/api/v1/notifications/"
PREFERENCES_URL = f"{NOTIFICATIONS_URL}preferences/"


def _prefs(client, company):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(PREFERENCES_URL)


def _prefs_patch(client, company, **payload):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.patch(PREFERENCES_URL, payload, format="json")


def _notifications_for(recipient, **filters):
    return Notification.objects.filter(recipient=recipient, **filters)


# --------------------------------------------------------------------------- #
# Navigation targets and categories
# --------------------------------------------------------------------------- #
class TestNavigationLinks:
    def test_task_assignment_links_to_task_detail(self, tenant, user_factory):
        assignee = user_factory(email="linkee@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company, title="Linked task", project=project, assignee=assignee
        )
        n = _notifications_for(assignee, entity_type="task", entity_id=task.pk).first()
        assert n is not None
        assert n.link == f"/tasks/{task.pk}"
        assert n.category == NotificationCategory.TASK_ASSIGNED

    def test_project_assignment_links_to_project_detail(self, tenant, user_factory):
        manager = user_factory(email="pm-link@test.com")
        project = Project.objects.create(
            company=tenant.company, name="Linked project", manager=manager
        )
        n = _notifications_for(manager, entity_type="project", entity_id=project.pk).first()
        assert n is not None
        assert n.link == f"/projects/{project.pk}"
        assert n.category == NotificationCategory.PROJECT_ASSIGNED

    def test_project_membership_links_to_project_detail(self, tenant, user_factory):
        member = user_factory(email="member-link@test.com")
        project = Project.objects.create(company=tenant.company, name="Membership")
        notify_project_member_added(
            str(
                ProjectMember.objects.create(
                    company=tenant.company, project=project, user=member
                ).pk
            )
        )
        n = _notifications_for(member, entity_type="project", entity_name=project.name).first()
        assert n is not None
        assert n.link == f"/projects/{project.pk}"

    def test_role_change_links_to_team(self, tenant, user_factory):
        member = user_factory(email="role-link@test.com")
        membership = Membership.objects.create(
            user=member, company=tenant.company, role=RoleChoices.EMPLOYEE
        )
        membership.role = RoleChoices.MANAGER
        membership.save(update_fields=["role"])
        n = _notifications_for(member, entity_type="membership").first()
        assert n is not None
        assert n.link == "/team"
        assert n.category == NotificationCategory.ROLE_CHANGED

    def test_invitation_links_to_team(self, tenant, user_factory):
        invitee = user_factory(email="invitee-link@test.com")
        notify_invitation_received(str(_make_invitation(tenant.company, invitee.email).pk))
        n = _notifications_for(invitee, entity_type="invitation").first()
        assert n is not None
        assert n.link == "/team"
        assert n.category == NotificationCategory.INVITATION_RECEIVED


def _make_invitation(company: Company, email: str, **kwargs) -> Membership:
    from apps.companies.models import TeamInvitation

    return TeamInvitation.objects.create(
        company=company,
        email=email,
        role=kwargs.pop("role", RoleChoices.EMPLOYEE),
        expires_at=timezone.now() + timedelta(days=7),
        status=InvitationStatus.PENDING,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# Task comment notifications
# --------------------------------------------------------------------------- #
class TestCommentNotifications:
    def test_notifies_assignee(self, tenant, user_factory):
        assignee = user_factory(email="assignee-c@test.com")
        commenter = user_factory(email="commenter@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company, title="Commented task", project=project, assignee=assignee
        )
        comment = TaskComment.objects.create(
            company=tenant.company, task=task, author=commenter, body="Hello"
        )
        notify_task_commented(str(comment.pk))
        n = _notifications_for(
            assignee,
            entity_type="task",
            entity_id=task.pk,
            category=NotificationCategory.TASK_COMMENT,
        ).first()
        assert n is not None
        assert n.actor == commenter
        assert "commented" in n.verb.lower()
        assert n.link == f"/tasks/{task.pk}"

    def test_does_not_notify_author(self, tenant, user_factory):
        assignee = user_factory(email="author@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company, title="Self comment", project=project, assignee=assignee
        )
        comment = TaskComment.objects.create(
            company=tenant.company, task=task, author=assignee, body="Self note"
        )
        notify_task_commented(str(comment.pk))
        assert (
            _notifications_for(
                assignee, entity_type="task", category=NotificationCategory.TASK_COMMENT
            ).count()
            == 0
        )

    def test_signal_dispatches_comment_notification(self, tenant, user_factory):
        assignee = user_factory(email="signal-c@test.com")
        commenter = user_factory(email="signal-author@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company, title="Signal comment", project=project, assignee=assignee
        )
        TaskComment.objects.create(
            company=tenant.company, task=task, author=commenter, body="Via signal"
        )
        n = _notifications_for(assignee, entity_type="task", entity_id=task.pk).first()
        assert n is not None
        assert "commented" in n.verb.lower()

    def test_no_assignee_no_notification(self, tenant, user_factory):
        commenter = user_factory(email="unassigned-c@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(company=tenant.company, title="Unassigned", project=project)
        comment = TaskComment.objects.create(
            company=tenant.company, task=task, author=commenter, body="Hello"
        )
        notify_task_commented(str(comment.pk))
        assert _notifications_for(tenant.admin, entity_type="task", entity_id=task.pk).count() == 0


# --------------------------------------------------------------------------- #
# Invitation received
# --------------------------------------------------------------------------- #
class TestInvitationReceived:
    def test_notifies_existing_user(self, tenant, user_factory):
        invitee = user_factory(email="already-registered@test.com")
        invitation = _make_invitation(tenant.company, invitee.email, invited_by=tenant.admin)
        notify_invitation_received(str(invitation.pk))
        n = _notifications_for(invitee, entity_type="invitation").first()
        assert n is not None
        assert "invited" in n.verb.lower()
        assert n.actor == tenant.admin  # falls back to the inviter

    def test_no_notification_for_unknown_email(self, tenant, user_factory):
        invitation = _make_invitation(tenant.company, "nobody@test.com")
        notify_invitation_received(str(invitation.pk))
        assert Notification.objects.filter(entity_type="invitation").count() == 0

    def test_no_notification_for_active_member(self, tenant):
        invitation = _make_invitation(tenant.company, tenant.employee.email)
        notify_invitation_received(str(invitation.pk))
        assert Notification.objects.filter(entity_type="invitation").count() == 0

    def test_case_insensitive_email_match(self, tenant, user_factory):
        invitee = user_factory(email="mixedcase@test.com")
        invitation = _make_invitation(tenant.company, "MixedCase@test.com")
        notify_invitation_received(str(invitation.pk))
        n = _notifications_for(invitee, entity_type="invitation").first()
        assert n is not None

    def test_signal_dispatches_invitation_notification(self, tenant, user_factory):
        invitee = user_factory(email="invited-via-signal@test.com")
        _make_invitation(tenant.company, invitee.email, invited_by=tenant.admin)
        n = _notifications_for(invitee, entity_type="invitation").first()
        assert n is not None
        assert n.actor == tenant.admin


# --------------------------------------------------------------------------- #
# Project member added
# --------------------------------------------------------------------------- #
class TestProjectMemberAdded:
    def test_notifies_added_member(self, tenant, user_factory):
        member = user_factory(email="pm@test.com")
        project = Project.objects.create(company=tenant.company, name="Shared")
        notify_project_member_added(
            str(
                ProjectMember.objects.create(
                    company=tenant.company, project=project, user=member
                ).pk
            )
        )
        n = _notifications_for(member, entity_type="project", entity_id=project.pk).first()
        assert n is not None
        assert "added" in n.verb.lower()
        assert n.link == f"/projects/{project.pk}"
        assert n.category == NotificationCategory.PROJECT_ASSIGNED

    def test_signal_dispatches_member_notification(self, tenant, user_factory):
        member = user_factory(email="pm-signal@test.com")
        project = Project.objects.create(company=tenant.company, name="Shared 2")
        ProjectMember.objects.create(company=tenant.company, project=project, user=member)
        n = _notifications_for(member, entity_type="project", entity_id=project.pk).first()
        assert n is not None

    def test_skips_manager_membership(self, tenant, user_factory):
        manager = user_factory(email="manager-pm@test.com")
        project = Project.objects.create(company=tenant.company, name="Managed", manager=manager)
        pm = ProjectMember.objects.create(company=tenant.company, project=project, user=manager)
        notify_project_member_added(str(pm.pk))
        # Only the manager-assignment notification should exist for this project.
        assert _notifications_for(manager, entity_type="project", entity_id=project.pk).count() == 1


# --------------------------------------------------------------------------- #
# Reassignment
# --------------------------------------------------------------------------- #
class TestReassignment:
    def test_reassigned_uses_reassigned_verb_and_links_task(self, tenant, user_factory):
        old = user_factory(email="old-a@test.com")
        new = user_factory(email="new-a@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company, title="Who owns this", project=project, assignee=old
        )
        Notification.objects.filter(entity_type="task", entity_id=task.pk).delete()
        task.assignee = new
        task.save(update_fields=["assignee"])
        n = _notifications_for(new, entity_type="task", entity_id=task.pk).first()
        assert n is not None
        assert "reassigned" in n.verb.lower()
        assert n.link == f"/tasks/{task.pk}"


# --------------------------------------------------------------------------- #
# Scheduled reminders — creation, overdue, deduplication
# --------------------------------------------------------------------------- #
class TestScheduledReminders:
    def test_due_soon_and_overdue_create_notifications(self, tenant, user_factory):
        assignee = user_factory(email="remindee@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Upcoming",
            project=project,
            assignee=assignee,
            due_date=date.today() + timedelta(days=2),
            status=TaskStatus.IN_PROGRESS,
        )
        Task.objects.create(
            company=tenant.company,
            title="Late",
            project=project,
            assignee=assignee,
            due_date=date.today() - timedelta(days=2),
            status=TaskStatus.IN_PROGRESS,
        )
        check_deadline_approaching()
        n_upcoming = _notifications_for(
            assignee, entity_type="task", category=NotificationCategory.TASK_DUE_SOON
        ).first()
        n_overdue = _notifications_for(
            assignee, entity_type="task", category=NotificationCategory.TASK_OVERDUE
        ).first()
        assert n_upcoming is not None
        assert n_overdue is not None
        assert "deadline" in n_upcoming.verb.lower()
        assert "overdue" in n_overdue.verb.lower()
        assert n_upcoming.link == f"/tasks/{n_upcoming.entity_id}"
        assert n_overdue.link == f"/tasks/{n_overdue.entity_id}"

    def test_completed_tasks_skip_reminders(self, tenant, user_factory):
        assignee = user_factory(email="done@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Finished late",
            project=project,
            assignee=assignee,
            due_date=date.today() - timedelta(days=1),
            status=TaskStatus.DONE,
        )
        check_deadline_approaching()
        assert (
            _notifications_for(
                assignee,
                entity_type="task",
                category__in=[
                    NotificationCategory.TASK_DUE_SOON,
                    NotificationCategory.TASK_OVERDUE,
                ],
            ).count()
            == 0
        )

    def test_reminders_deduplicate_even_after_reading(self, tenant, user_factory):
        assignee = user_factory(email="read-dedup@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Dedup me",
            project=project,
            assignee=assignee,
            due_date=date.today() + timedelta(days=1),
            status=TaskStatus.TODO,
        )
        check_deadline_approaching()
        due_soon = _notifications_for(assignee, category=NotificationCategory.TASK_DUE_SOON).first()
        assert due_soon is not None
        # Reading the reminder must NOT clear the dedup window.
        due_soon.is_read = True
        due_soon.save(update_fields=["is_read", "updated_at"])
        check_deadline_approaching()
        assert (
            _notifications_for(
                assignee, entity_type="task", category=NotificationCategory.TASK_DUE_SOON
            ).count()
            == 1
        )

    def test_overdue_reminders_deduplicate(self, tenant, user_factory):
        assignee = user_factory(email="overdue-dedup@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Late again",
            project=project,
            assignee=assignee,
            due_date=date.today() - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        check_deadline_approaching()
        check_deadline_approaching()
        assert (
            _notifications_for(
                assignee, entity_type="task", category=NotificationCategory.TASK_OVERDUE
            ).count()
            == 1
        )

    def test_different_categories_do_not_deduplicate_each_other(self, tenant, user_factory):
        assignee = user_factory(email="cross-cat@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        task = Task.objects.create(
            company=tenant.company,
            title="Both categories",
            project=project,
            assignee=assignee,
            due_date=date.today() + timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        check_deadline_approaching()
        # Manually create an overdue-style reminder for the same entity: same
        # dedup_key, different category — must coexist within the window.
        from apps.notifications.tasks import _resolve_actor

        created = create_notification(
            company=task.company,
            recipient=assignee,
            verb='Task "Both categories" is overdue',
            entity_type="task",
            entity_id=task.pk,
            entity_name=task.title,
            link=f"/tasks/{task.pk}",
            actor=_resolve_actor(None),
            category=NotificationCategory.TASK_OVERDUE,
            dedup_key=f"task:{task.pk}",
        )
        assert created is not None

    def test_project_deadline_deduplicates(self, tenant, user_factory):
        manager = user_factory(email="project-dedup@test.com")
        Project.objects.create(
            company=tenant.company,
            name="Deadline",
            manager=manager,
            deadline=date.today() + timedelta(days=4),
            status=ProjectStatus.IN_PROGRESS,
        )
        check_deadline_approaching()
        check_deadline_approaching()
        assert (
            _notifications_for(
                manager, entity_type="project", category=NotificationCategory.PROJECT_DEADLINE
            ).count()
            == 1
        )


# --------------------------------------------------------------------------- #
# Preferences — service-level gating
# --------------------------------------------------------------------------- #
class TestPreferenceGating:
    def test_disabled_category_suppresses_notification(self, tenant, user_factory):
        assignee = user_factory(email="opted-out@test.com")
        NotificationPreference.objects.create(
            company=tenant.company, user=assignee, task_assigned=False
        )
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company, title="Opted out", project=project, assignee=assignee
        )
        assert (
            _notifications_for(assignee, entity_type="task", entity_id__isnull=False).count() == 0
        )

    def test_disabled_reminder_category_skips_scheduled_run(self, tenant, user_factory):
        assignee = user_factory(email="remind-off@test.com")
        NotificationPreference.objects.create(
            company=tenant.company, user=assignee, task_overdue=False
        )
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company,
            title="Late but opted out",
            project=project,
            assignee=assignee,
            due_date=date.today() - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        check_deadline_approaching()
        assert (
            _notifications_for(
                assignee, entity_type="task", category=NotificationCategory.TASK_OVERDUE
            ).count()
            == 0
        )

    def test_absent_preference_means_all_enabled(self, tenant, user_factory):
        assignee = user_factory(email="no-pref@test.com")
        project = Project.objects.create(company=tenant.company, name="P1")
        Task.objects.create(
            company=tenant.company, title="Default on", project=project, assignee=assignee
        )
        assert _notifications_for(assignee, entity_type="task").exists()


# --------------------------------------------------------------------------- #
# Preferences — API
# --------------------------------------------------------------------------- #
class TestPreferencesAPI:
    def test_get_creates_default_preference(self, tenant, auth_client):
        resp = _prefs(auth_client(tenant.employee, tenant.company), tenant.company)
        assert resp.status_code == 200
        assert resp.data["task_assigned"] is True
        assert resp.data["role_changed"] is True
        assert NotificationPreference.objects.filter(
            company=tenant.company, user=tenant.employee
        ).exists()

    def test_patch_updates_flags(self, tenant, auth_client):
        auth_client(tenant.employee, tenant.company)
        resp = _prefs_patch(
            auth_client(tenant.employee, tenant.company), tenant.company, task_overdue=False
        )
        assert resp.status_code == 200
        assert resp.data["task_overdue"] is False
        assert resp.data["task_assigned"] is True

    def test_preferences_are_isolated_per_company(self, tenant, auth_client, company_factory):
        company_b = company_factory(name="Company B", slug="company-b2")
        Membership.objects.create(
            user=tenant.employee, company=company_b, role=RoleChoices.EMPLOYEE
        )
        _prefs_patch(auth_client(tenant.employee, company_b), company_b, project_assigned=False)
        pref_b = NotificationPreference.objects.get(company=company_b, user=tenant.employee)
        assert pref_b.project_assigned is False
        assert (
            NotificationPreference.objects.filter(
                company=tenant.company, user=tenant.employee
            ).exists()
            is False
        )

    def test_preferences_require_valid_company_context(self, tenant, auth_client, company_factory):
        company_b = company_factory(name="Company B", slug="company-b5")
        client = auth_client(tenant.employee)
        client.credentials(HTTP_X_COMPANY_ID=str(company_b.id))
        resp = client.get(PREFERENCES_URL)
        assert resp.status_code == 403

    def test_unauthenticated_preferences_denied(self, api_client):
        resp = api_client.get(PREFERENCES_URL)
        assert resp.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# Tenant isolation for new flows
# --------------------------------------------------------------------------- #
class TestTenantIsolationNewFlows:
    def test_invitation_notification_scoped_to_inviting_company(
        self, tenant, company_factory, user_factory
    ):
        company_b = company_factory(name="Company B", slug="company-b3")
        invitee = user_factory(email="cross-tenant@test.com")
        invitation = _make_invitation(company_b, invitee.email)
        notify_invitation_received(str(invitation.pk))
        n = _notifications_for(invitee, entity_type="invitation").first()
        assert n is not None
        assert n.company == company_b

    def test_comment_notification_scoped_to_task_company(
        self, tenant, company_factory, user_factory
    ):
        company_b = company_factory(name="Company B", slug="company-b4")
        assignee = user_factory(email="cross-comment@test.com")
        project = Project.objects.create(company=company_b, name="P B")
        task = Task.objects.create(
            company=company_b, title="T B", project=project, assignee=assignee
        )
        comment = TaskComment.objects.create(
            company=company_b, task=task, author=tenant.admin, body="Hi"
        )
        notify_task_commented(str(comment.pk))
        n = _notifications_for(assignee, entity_type="task", entity_id=task.pk).first()
        assert n.company == company_b


# --------------------------------------------------------------------------- #
# Read state / permissions
# --------------------------------------------------------------------------- #
class TestReadStateAndPermissions:
    def test_employee_cannot_mark_others_notification_read(self, tenant, auth_client):
        notif = Notification.objects.create(
            company=tenant.company,
            recipient=tenant.admin,
            actor=tenant.admin,
            verb="For admin only",
            category=NotificationCategory.TASK_ASSIGNED,
        )
        resp = auth_client(tenant.employee, tenant.company).patch(
            f"{NOTIFICATIONS_URL}{notif.pk}/mark-read/"
        )
        assert resp.status_code == 404
        notif.refresh_from_db()
        assert notif.is_read is False

    def test_unread_count_reflects_no_unread_after_mark_all(self, tenant, auth_client):
        Notification.objects.create(
            company=tenant.company, recipient=tenant.admin, verb="A", is_read=False
        )
        client = auth_client(tenant.admin, tenant.company)
        client.patch(f"{NOTIFICATIONS_URL}mark-all-read/")
        resp = client.get(f"{NOTIFICATIONS_URL}unread-count/")
        assert resp.data["count"] == 0


# --------------------------------------------------------------------------- #
# Celery beat schedule
# --------------------------------------------------------------------------- #
class TestBeatSchedule:
    def test_deadline_task_registered_in_beat_schedule(self):
        schedule = settings.CELERY_BEAT_SCHEDULE
        entry = schedule.get("notify-deadline-approaching")
        assert entry is not None
        assert entry["task"] == "apps.notifications.tasks.check_deadline_approaching"
