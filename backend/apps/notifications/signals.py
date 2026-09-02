"""Signal receivers that create notifications for domain events.

Runs synchronously within the same transaction as the business write.
Notifications are lightweight; delays are handled by Celery tasks dispatched
from these signals where the work is non-trivial (e.g. deadline checking).
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.companies.models import Membership, TeamInvitation
from apps.core.request_context import get_actor
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, TaskComment

_TASK_FIELDS = ("assignee_id", "status", "due_date")
_PROJECT_FIELDS = ("manager_id", "deadline", "status")
_MEMBERSHIP_FIELDS = ("role",)


def _snapshot(sender, instance, fields: tuple[str, ...]) -> None:
    """Stash the DB's current values before update."""
    if instance._state.adding:
        instance._notif_old = None
        return
    instance._notif_old = sender.objects.filter(pk=instance.pk).values(*fields).first()


def _changed(old: dict[str, Any] | None, instance, fields: tuple[str, ...]) -> list[str]:
    if not old:
        return []
    return [f for f in fields if old.get(f) != getattr(instance, f)]


@receiver(pre_save, sender=Task, dispatch_uid="notifications.task_pre_save")
def _task_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _TASK_FIELDS)


@receiver(post_save, sender=Task, dispatch_uid="notifications.task_post_save")
def _task_post_save(sender, instance, created, **kwargs) -> None:
    old = getattr(instance, "_notif_old", None)

    if created and instance.assignee_id:
        _dispatch_task_assigned(instance, reassigned=False)
        return

    changed = _changed(old, instance, _TASK_FIELDS)
    if "assignee_id" in changed and instance.assignee_id:
        _dispatch_task_assigned(instance, reassigned=True)


def _dispatch_task_assigned(instance: Task, *, reassigned: bool) -> None:
    from apps.notifications.tasks import notify_task_assigned

    actor = get_actor()
    notify_task_assigned.delay(
        str(instance.pk), str(actor.pk) if actor else None, reassigned=reassigned
    )


@receiver(pre_save, sender=Project, dispatch_uid="notifications.project_pre_save")
def _project_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _PROJECT_FIELDS)


@receiver(post_save, sender=Project, dispatch_uid="notifications.project_post_save")
def _project_post_save(sender, instance, created, **kwargs) -> None:
    old = getattr(instance, "_notif_old", None)

    if created and instance.manager_id:
        from apps.notifications.tasks import notify_project_assigned

        actor = get_actor()
        notify_project_assigned.delay(str(instance.pk), str(actor.pk) if actor else None)
        return

    changed = _changed(old, instance, _PROJECT_FIELDS)
    if "manager_id" in changed and instance.manager_id:
        from apps.notifications.tasks import notify_project_assigned

        actor = get_actor()
        notify_project_assigned.delay(str(instance.pk), str(actor.pk) if actor else None)


@receiver(pre_save, sender=Membership, dispatch_uid="notifications.membership_pre_save")
def _membership_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _MEMBERSHIP_FIELDS)


@receiver(post_save, sender=Membership, dispatch_uid="notifications.membership_post_save")
def _membership_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        return

    old = getattr(instance, "_notif_old", None)
    changed = _changed(old, instance, _MEMBERSHIP_FIELDS)
    if "role" not in changed:
        return

    from apps.notifications.tasks import notify_team_role_changed

    actor = get_actor()
    notify_team_role_changed.delay(str(instance.pk), str(actor.pk) if actor else None)


@receiver(post_save, sender=TaskComment, dispatch_uid="notifications.task_comment_post_save")
def _task_comment_post_save(sender, instance, created, **kwargs) -> None:
    if not created:
        return
    from apps.notifications.tasks import notify_task_commented

    notify_task_commented.delay(str(instance.pk))


@receiver(post_save, sender=ProjectMember, dispatch_uid="notifications.project_member_post_save")
def _project_member_post_save(sender, instance, created, **kwargs) -> None:
    if not created:
        return
    from apps.notifications.tasks import notify_project_member_added

    actor = get_actor()
    notify_project_member_added.delay(str(instance.pk), str(actor.pk) if actor else None)


@receiver(post_save, sender=TeamInvitation, dispatch_uid="notifications.invitation_post_save")
def _invitation_post_save(sender, instance, created, **kwargs) -> None:
    if not created:
        return
    from apps.notifications.tasks import notify_invitation_received

    actor = get_actor()
    notify_invitation_received.delay(str(instance.pk), str(actor.pk) if actor else None)
