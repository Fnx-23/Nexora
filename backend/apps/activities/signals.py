"""Signal receivers that translate domain writes into audit records.

This module is the *only* place that decides which model changes become audit
events. Views, serializers and services stay unaware of auditing entirely — they
just save models as usual, and these receivers (connected in
``ActivitiesConfig.ready``) record the appropriate :class:`Activity`.

Change detection
----------------
``pre_save`` snapshots the previous values of tracked fields onto the instance;
``post_save`` compares them to decide what happened (created vs. updated vs. a
specific transition such as archived / status-changed / assigned / role-changed).

Note: ``QuerySet.update()`` and ``bulk_create()`` bypass these signals by design
(Django does not emit per-row signals for them). All Nexora write paths go
through ``Model.save()``, so this is sufficient in practice.
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.activities.models import ActivityAction, EntityType
from apps.activities.services import record_activity
from apps.companies.models import InvitationStatus, Membership, TeamInvitation
from apps.customers.models import Customer, CustomerStatus
from apps.documents.models import Document, EntityKind
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, TaskComment

_CUSTOMER_FIELDS = (
    "name",
    "company_name",
    "email",
    "phone",
    "address",
    "notes",
    "status",
    "is_active",
)
_PROJECT_FIELDS = (
    "name",
    "description",
    "customer_id",
    "manager_id",
    "status",
    "priority",
    "start_date",
    "deadline",
)
_TASK_FIELDS = (
    "title",
    "description",
    "project_id",
    "status",
    "priority",
    "assignee_id",
    "due_date",
)
_MEMBERSHIP_FIELDS = ("role", "is_active")
_INVITATION_FIELDS = ("status",)


def _snapshot(sender, instance, fields: tuple[str, ...]) -> None:
    """Stash the DB's current values of ``fields`` on the instance before update."""
    if instance._state.adding:
        instance._audit_old = None
        return
    instance._audit_old = sender.objects.filter(pk=instance.pk).values(*fields).first()


def _changed(old: dict[str, Any] | None, instance, fields: tuple[str, ...]) -> list[str]:
    """Return the names of tracked fields whose value differs from the snapshot."""
    if not old:
        return []
    return [f for f in fields if old.get(f) != getattr(instance, f)]


@receiver(pre_save, sender=Customer, dispatch_uid="activities.customer_pre_save")
def _customer_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _CUSTOMER_FIELDS)


@receiver(post_save, sender=Customer, dispatch_uid="activities.customer_post_save")
def _customer_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        record_activity(
            action=ActivityAction.CUSTOMER_CREATED,
            entity=instance,
            entity_type=EntityType.CUSTOMER,
            metadata={"name": instance.name, "status": instance.status},
        )
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _CUSTOMER_FIELDS)
    if not changed:
        return

    became_archived = (
        instance.status == CustomerStatus.ARCHIVED
        and (old or {}).get("status") != CustomerStatus.ARCHIVED
    )
    if became_archived:
        record_activity(
            action=ActivityAction.CUSTOMER_ARCHIVED,
            entity=instance,
            entity_type=EntityType.CUSTOMER,
            metadata={"name": instance.name},
        )
        return

    record_activity(
        action=ActivityAction.CUSTOMER_UPDATED,
        entity=instance,
        entity_type=EntityType.CUSTOMER,
        metadata={"name": instance.name, "changed_fields": changed},
    )


@receiver(pre_save, sender=Project, dispatch_uid="activities.project_pre_save")
def _project_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _PROJECT_FIELDS)


@receiver(post_save, sender=Project, dispatch_uid="activities.project_post_save")
def _project_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        record_activity(
            action=ActivityAction.PROJECT_CREATED,
            entity=instance,
            entity_type=EntityType.PROJECT,
            metadata={
                "name": instance.name,
                "status": instance.status,
                "priority": instance.priority,
            },
        )
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _PROJECT_FIELDS)
    if not changed:
        return

    if "status" in changed:
        record_activity(
            action=ActivityAction.PROJECT_STATUS_CHANGED,
            entity=instance,
            entity_type=EntityType.PROJECT,
            metadata={
                "name": instance.name,
                "old_status": (old or {}).get("status"),
                "new_status": instance.status,
            },
        )
        return

    record_activity(
        action=ActivityAction.PROJECT_UPDATED,
        entity=instance,
        entity_type=EntityType.PROJECT,
        metadata={"name": instance.name, "changed_fields": changed},
    )


@receiver(pre_save, sender=Task, dispatch_uid="activities.task_pre_save")
def _task_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _TASK_FIELDS)


@receiver(post_save, sender=Task, dispatch_uid="activities.task_post_save")
def _task_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        record_activity(
            action=ActivityAction.TASK_CREATED,
            entity=instance,
            entity_type=EntityType.TASK,
            metadata={
                "title": instance.title,
                "status": instance.status,
                "priority": instance.priority,
                "assignee_id": str(instance.assignee_id) if instance.assignee_id else None,
            },
        )
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _TASK_FIELDS)
    if not changed:
        return

    if "assignee_id" in changed:
        old_assignee = (old or {}).get("assignee_id")
        record_activity(
            action=ActivityAction.TASK_ASSIGNED,
            entity=instance,
            entity_type=EntityType.TASK,
            metadata={
                "title": instance.title,
                "old_assignee_id": str(old_assignee) if old_assignee else None,
                "new_assignee_id": str(instance.assignee_id) if instance.assignee_id else None,
            },
        )

    if "status" in changed:
        record_activity(
            action=ActivityAction.TASK_STATUS_CHANGED,
            entity=instance,
            entity_type=EntityType.TASK,
            metadata={
                "title": instance.title,
                "old_status": (old or {}).get("status"),
                "new_status": instance.status,
            },
        )

    if "priority" in changed:
        record_activity(
            action=ActivityAction.TASK_PRIORITY_CHANGED,
            entity=instance,
            entity_type=EntityType.TASK,
            metadata={
                "title": instance.title,
                "old_priority": (old or {}).get("priority"),
                "new_priority": instance.priority,
            },
        )

    if "due_date" in changed:
        record_activity(
            action=ActivityAction.TASK_DUE_DATE_CHANGED,
            entity=instance,
            entity_type=EntityType.TASK,
            metadata={
                "title": instance.title,
                "old_due_date": str((old or {}).get("due_date") or ""),
                "new_due_date": str(instance.due_date or ""),
            },
        )


@receiver(post_save, sender=TaskComment, dispatch_uid="activities.task_comment_post_save")
def _task_comment_post_save(sender, instance, created, **kwargs) -> None:
    if not created:
        return
    record_activity(
        action=ActivityAction.TASK_COMMENT_ADDED,
        company=instance.company,
        entity_type=EntityType.TASK,
        entity_id=instance.task_id,
        metadata={"comment_id": str(instance.pk)},
    )


@receiver(post_delete, sender=TaskComment, dispatch_uid="activities.task_comment_post_delete")
def _task_comment_post_delete(sender, instance, **kwargs) -> None:
    record_activity(
        action=ActivityAction.TASK_COMMENT_DELETED,
        company=instance.company,
        entity_type=EntityType.TASK,
        entity_id=instance.task_id,
        metadata={"comment_id": str(instance.pk)},
    )


@receiver(post_save, sender=Document, dispatch_uid="activities.document_post_save")
def _document_post_save(sender, instance, created, **kwargs) -> None:
    if not created or instance.entity_kind != EntityKind.TASK:
        return
    record_activity(
        action=ActivityAction.TASK_ATTACHMENT_ADDED,
        company=instance.company,
        entity_type=EntityType.TASK,
        entity_id=instance.entity_id,
        metadata={
            "document_id": str(instance.pk),
            "original_filename": instance.original_filename,
            "size": instance.size,
        },
    )


@receiver(pre_save, sender=Membership, dispatch_uid="activities.membership_pre_save")
def _membership_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _MEMBERSHIP_FIELDS)


@receiver(post_save, sender=Membership, dispatch_uid="activities.membership_post_save")
def _membership_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _MEMBERSHIP_FIELDS)

    if "is_active" in changed:
        now_active = instance.is_active
        record_activity(
            action=(
                ActivityAction.TEAM_MEMBER_REACTIVATED
                if now_active
                else ActivityAction.TEAM_MEMBER_DEACTIVATED
            ),
            entity=instance,
            entity_type=EntityType.MEMBERSHIP,
            metadata={"member_user_id": str(instance.user_id)},
        )

    if "role" in changed:
        record_activity(
            action=ActivityAction.TEAM_ROLE_CHANGED,
            entity=instance,
            entity_type=EntityType.MEMBERSHIP,
            metadata={
                "member_user_id": str(instance.user_id),
                "old_role": (old or {}).get("role"),
                "new_role": instance.role,
            },
        )


@receiver(post_delete, sender=Membership, dispatch_uid="activities.membership_post_delete")
def _membership_post_delete(sender, instance, **kwargs) -> None:
    record_activity(
        action=ActivityAction.TEAM_MEMBER_REMOVED,
        company=instance.company,
        entity_type=EntityType.MEMBERSHIP,
        entity_id=instance.pk,
        metadata={"member_user_id": str(instance.user_id)},
    )


@receiver(pre_save, sender=TeamInvitation, dispatch_uid="activities.invitation_pre_save")
def _invitation_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _INVITATION_FIELDS)


@receiver(post_save, sender=TeamInvitation, dispatch_uid="activities.invitation_post_save")
def _invitation_post_save(sender, instance, created, **kwargs) -> None:
    if created:
        record_activity(
            action=ActivityAction.INVITATION_SENT,
            entity=instance,
            entity_type=EntityType.INVITATION,
            metadata={
                "invitee_email": instance.email,
                "role": instance.role,
            },
        )
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _INVITATION_FIELDS)
    if "status" not in changed or instance.status == InvitationStatus.ACCEPTED:
        return

    if instance.status == InvitationStatus.REVOKED:
        record_activity(
            action=ActivityAction.INVITATION_REVOKED,
            entity=instance,
            entity_type=EntityType.INVITATION,
            metadata={"invitee_email": instance.email, "role": instance.role},
        )


@receiver(post_save, sender=ProjectMember, dispatch_uid="activities.project_member_post_save")
def _project_member_post_save(sender, instance, created, **kwargs) -> None:
    if not created:
        return
    record_activity(
        action=ActivityAction.PROJECT_MEMBER_ADDED,
        company=instance.company,
        entity_type=EntityType.PROJECT,
        entity_id=instance.project_id,
        metadata={
            "project_name": instance.project.name,
            "member_user_id": str(instance.user_id),
        },
    )


@receiver(post_delete, sender=ProjectMember, dispatch_uid="activities.project_member_post_delete")
def _project_member_post_delete(sender, instance, **kwargs) -> None:
    record_activity(
        action=ActivityAction.PROJECT_MEMBER_REMOVED,
        company=instance.company,
        entity_type=EntityType.PROJECT,
        entity_id=instance.project_id,
        metadata={
            "project_name": instance.project.name,
            "member_user_id": str(instance.user_id),
        },
    )
