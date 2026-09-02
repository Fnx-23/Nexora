"""Celery tasks for asynchronous notification processing."""

from __future__ import annotations

import contextlib
import logging
from datetime import timedelta

from django.utils import timezone

from apps.notifications.models import NotificationCategory
from apps.notifications.services import create_notification, create_unique_notification
from celery import shared_task

logger = logging.getLogger("apps.notifications")


def _resolve_actor(actor_id: str | None):
    """Resolve an actor by id, or ``None`` (system) when unknown/absent."""
    if not actor_id:
        return None
    from apps.accounts.models import User

    with contextlib.suppress(User.DoesNotExist):
        return User.objects.get(pk=actor_id)
    return None


@shared_task
def notify_task_assigned(task_id: str, actor_id: str | None = None, **kwargs) -> None:
    """Create a notification when a task is assigned or reassigned to a user."""
    from apps.tasks.models import Task

    reassigned = kwargs.get("reassigned", False)

    try:
        task = Task.objects.select_related("assignee", "project").get(pk=task_id)
    except Task.DoesNotExist:
        logger.warning("Task %s not found, skipping notification.", task_id)
        return

    if task.assignee_id is None:
        return

    verb = (
        f'Task "{task.title}" was reassigned to you'
        if reassigned
        else f'You have been assigned to task "{task.title}"'
    )
    create_notification(
        company=task.company,
        recipient=task.assignee,
        verb=verb,
        entity_type="task",
        entity_id=task.pk,
        entity_name=task.title,
        link=f"/tasks/{task.pk}",
        actor=_resolve_actor(actor_id),
        category=NotificationCategory.TASK_ASSIGNED,
    )


@shared_task
def notify_task_commented(comment_id: str) -> None:
    """Notify the assignee when someone comments on their assigned task."""
    from apps.tasks.models import TaskComment

    try:
        comment = TaskComment.objects.select_related("task", "task__assignee", "author").get(
            pk=comment_id
        )
    except TaskComment.DoesNotExist:
        logger.warning("Task comment %s not found, skipping notification.", comment_id)
        return

    task = comment.task
    if task.assignee_id is None or task.assignee_id == comment.author_id:
        return

    actor_name = (
        comment.author and (comment.author.get_full_name() or comment.author.email)
    ) or "System"
    create_notification(
        company=task.company,
        recipient=task.assignee,
        verb=f'{actor_name} commented on task "{task.title}"',
        entity_type="task",
        entity_id=task.pk,
        entity_name=task.title,
        link=f"/tasks/{task.pk}",
        actor=comment.author,
        category=NotificationCategory.TASK_COMMENT,
    )


@shared_task
def notify_project_assigned(project_id: str, actor_id: str | None = None) -> None:
    """Create a notification when a project manager is assigned."""
    from apps.projects.models import Project

    try:
        project = Project.objects.select_related("manager").get(pk=project_id)
    except Project.DoesNotExist:
        logger.warning("Project %s not found, skipping notification.", project_id)
        return

    if project.manager_id is None:
        return

    create_notification(
        company=project.company,
        recipient=project.manager,
        verb=f'You have been assigned as manager of project "{project.name}"',
        entity_type="project",
        entity_id=project.pk,
        entity_name=project.name,
        link=f"/projects/{project.pk}",
        actor=_resolve_actor(actor_id),
        category=NotificationCategory.PROJECT_ASSIGNED,
    )


@shared_task
def notify_project_member_added(project_member_id: str, actor_id: str | None = None) -> None:
    """Notify a user when they are added to a project."""
    from apps.projects.models import ProjectMember

    try:
        member = ProjectMember.objects.select_related("project", "user").get(pk=project_member_id)
    except ProjectMember.DoesNotExist:
        logger.warning("Project member %s not found, skipping notification.", project_member_id)
        return

    actor = _resolve_actor(actor_id)
    if member.project.manager_id == member.user_id or (actor and actor.pk == member.user_id):
        return

    create_notification(
        company=member.company,
        recipient=member.user,
        verb=f'You have been added to project "{member.project.name}"',
        entity_type="project",
        entity_id=member.project.pk,
        entity_name=member.project.name,
        link=f"/projects/{member.project.pk}",
        actor=actor,
        category=NotificationCategory.PROJECT_ASSIGNED,
    )


@shared_task
def notify_invitation_received(invitation_id: str, actor_id: str | None = None) -> None:
    """Notify an existing user when they receive an invitation to a company."""
    from apps.accounts.models import User
    from apps.companies.models import InvitationStatus, TeamInvitation

    try:
        invitation = TeamInvitation.objects.select_related("company").get(pk=invitation_id)
    except TeamInvitation.DoesNotExist:
        logger.warning("Invitation %s not found, skipping notification.", invitation_id)
        return

    if invitation.status != InvitationStatus.PENDING:
        return

    recipient = (
        User.objects.filter(email__iexact=invitation.email)
        .exclude(pk=invitation.invited_by_id)
        .first()
    )
    if recipient is None:
        return

    if recipient.memberships.filter(company=invitation.company, is_active=True).exists():
        return

    actor = _resolve_actor(actor_id) or invitation.invited_by
    create_notification(
        company=invitation.company,
        recipient=recipient,
        verb=f'You have been invited to join "{invitation.company.name}" as '
        f"{invitation.get_role_display()}",
        entity_type="invitation",
        entity_id=invitation.pk,
        entity_name=invitation.company.name,
        link="/team",
        actor=actor,
        category=NotificationCategory.INVITATION_RECEIVED,
    )


@shared_task
def notify_team_role_changed(membership_id: str, actor_id: str | None = None) -> None:
    """Create a notification when a team member's role changes."""
    from apps.companies.models import Membership

    try:
        membership = Membership.objects.select_related("user", "company").get(pk=membership_id)
    except Membership.DoesNotExist:
        logger.warning("Membership %s not found.", membership_id)
        return

    create_notification(
        company=membership.company,
        recipient=membership.user,
        verb=f"Your role has been changed to {membership.get_role_display()}",
        entity_type="membership",
        entity_id=membership.pk,
        entity_name=membership.company.name,
        link="/team",
        actor=_resolve_actor(actor_id),
        category=NotificationCategory.ROLE_CHANGED,
    )


@shared_task
def check_deadline_approaching() -> None:
    """Periodic task: notify users about approaching and overdue deadlines.

    Tasks due within 3 days and projects due within 7 days generate "due soon"
    reminders; tasks past their due date generate "overdue" reminders. Every
    reminder is deduplicated per recipient/category/entity for 24 hours via
    ``dedup_key`` (independent of read state), so Celery beat can run frequently
    without flooding inboxes.
    """
    from apps.notifications.models import NotificationCategory
    from apps.projects.models import Project, ProjectStatus
    from apps.tasks.models import Task, TaskStatus

    today = timezone.now().date()
    task_deadline = today + timedelta(days=3)
    project_deadline = today + timedelta(days=7)

    active_task_statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
    active_project_statuses = [
        ProjectStatus.PLANNING,
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.ON_HOLD,
    ]

    tasks_due = Task.objects.filter(
        due_date__lte=task_deadline,
        due_date__gte=today,
        status__in=active_task_statuses,
        assignee__isnull=False,
    ).select_related("assignee")

    for task in tasks_due:
        create_unique_notification(
            company=task.company,
            recipient=task.assignee,
            verb=f'Deadline approaching for task "{task.title}" (due {task.due_date})',
            entity_type="task",
            entity_id=task.pk,
            entity_name=task.title,
            link=f"/tasks/{task.pk}",
            category=NotificationCategory.TASK_DUE_SOON,
            dedup_key=f"task:{task.pk}",
        )

    tasks_overdue = Task.objects.filter(
        due_date__lt=today,
        status__in=active_task_statuses,
        assignee__isnull=False,
    ).select_related("assignee")

    for task in tasks_overdue:
        create_unique_notification(
            company=task.company,
            recipient=task.assignee,
            verb=f'Task "{task.title}" is overdue (was due {task.due_date})',
            entity_type="task",
            entity_id=task.pk,
            entity_name=task.title,
            link=f"/tasks/{task.pk}",
            category=NotificationCategory.TASK_OVERDUE,
            dedup_key=f"task:{task.pk}",
        )

    projects_due = Project.objects.filter(
        deadline__lte=project_deadline,
        deadline__gte=today,
        status__in=active_project_statuses,
        manager__isnull=False,
    ).select_related("manager")

    for project in projects_due:
        create_unique_notification(
            company=project.company,
            recipient=project.manager,
            verb=f'Deadline approaching for project "{project.name}" (due {project.deadline})',
            entity_type="project",
            entity_id=project.pk,
            entity_name=project.name,
            link=f"/projects/{project.pk}",
            category=NotificationCategory.PROJECT_DEADLINE,
            dedup_key=f"project:{project.pk}",
        )
