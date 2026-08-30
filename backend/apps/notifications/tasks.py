"""Celery tasks for asynchronous notification processing."""

from __future__ import annotations

import contextlib
import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

logger = logging.getLogger("apps.notifications")


@shared_task
def notify_task_assigned(task_id: str, actor_id: str | None = None) -> None:
    """Create a notification when a task is assigned to a user."""
    from apps.accounts.models import User
    from apps.notifications.services import create_notification
    from apps.tasks.models import Task

    try:
        task = Task.objects.select_related("assignee", "project").get(pk=task_id)
    except Task.DoesNotExist:
        logger.warning("Task %s not found, skipping notification.", task_id)
        return

    if task.assignee_id is None:
        return

    actor = None
    if actor_id:
        with contextlib.suppress(User.DoesNotExist):
            actor = User.objects.get(pk=actor_id)

    create_notification(
        company=task.company,
        recipient=task.assignee,
        verb=f'You have been assigned to task "{task.title}"',
        entity_type="task",
        entity_id=task.pk,
        entity_name=task.title,
        link="/tasks",
        actor=actor,
    )


@shared_task
def notify_project_assigned(project_id: str, actor_id: str | None = None) -> None:
    """Create a notification when a project manager is assigned."""
    from apps.accounts.models import User
    from apps.notifications.services import create_notification
    from apps.projects.models import Project

    try:
        project = Project.objects.select_related("manager").get(pk=project_id)
    except Project.DoesNotExist:
        logger.warning("Project %s not found, skipping notification.", project_id)
        return

    if project.manager_id is None:
        return

    actor = None
    if actor_id:
        with contextlib.suppress(User.DoesNotExist):
            actor = User.objects.get(pk=actor_id)

    create_notification(
        company=project.company,
        recipient=project.manager,
        verb=f'You have been assigned as manager of project "{project.name}"',
        entity_type="project",
        entity_id=project.pk,
        entity_name=project.name,
        link=f"/projects/{project.pk}",
        actor=actor,
    )


@shared_task
def notify_team_role_changed(membership_id: str, actor_id: str | None = None) -> None:
    """Create a notification when a team member's role changes."""
    from apps.accounts.models import User
    from apps.companies.models import Membership
    from apps.notifications.services import create_notification

    try:
        membership = Membership.objects.select_related("user", "company").get(pk=membership_id)
    except Membership.DoesNotExist:
        logger.warning("Membership %s not found.", membership_id)
        return

    actor = None
    if actor_id:
        with contextlib.suppress(User.DoesNotExist):
            actor = User.objects.get(pk=actor_id)

    create_notification(
        company=membership.company,
        recipient=membership.user,
        verb=f"Your role has been changed to {membership.get_role_display()}",
        entity_type="membership",
        entity_id=membership.pk,
        entity_name=membership.company.name,
        link="/team",
        actor=actor,
    )


@shared_task
def check_deadline_approaching() -> None:
    """Periodic task: notify users about approaching task and project deadlines.

    Tasks due within 3 days and projects due within 7 days generate notifications.
    Only sends one notification per entity per 24-hour window (dedup via is_read=False).
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification
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

    # Task deadline approaching
    tasks_due = Task.objects.filter(
        due_date__lte=task_deadline,
        due_date__gte=today,
        status__in=active_task_statuses,
        assignee__isnull=False,
    ).select_related("assignee", "project")

    for task in tasks_due:
        already_notified = Notification.objects.filter(
            company=task.company,
            recipient=task.assignee,
            entity_type="task",
            entity_id=task.pk,
            verb__contains="deadline approaching",
            is_read=False,
            created_at__gte=timezone.now() - timedelta(hours=23),
        ).exists()
        if not already_notified:
            create_notification(
                company=task.company,
                recipient=task.assignee,
                verb=f'Deadline approaching for task "{task.title}" (due {task.due_date})',
                entity_type="task",
                entity_id=task.pk,
                entity_name=task.title,
                link="/tasks",
            )

    # Project deadline approaching
    projects_due = Project.objects.filter(
        deadline__lte=project_deadline,
        deadline__gte=today,
        status__in=active_project_statuses,
        manager__isnull=False,
    ).select_related("manager")

    for project in projects_due:
        already_notified = Notification.objects.filter(
            company=project.company,
            recipient=project.manager,
            entity_type="project",
            entity_id=project.pk,
            verb__contains="deadline approaching",
            is_read=False,
            created_at__gte=timezone.now() - timedelta(hours=23),
        ).exists()
        if not already_notified:
            create_notification(
                company=project.company,
                recipient=project.manager,
                verb=f'Deadline approaching for project "{project.name}" (due {project.deadline})',
                entity_type="project",
                entity_id=project.pk,
                entity_name=project.name,
                link=f"/projects/{project.pk}",
            )
