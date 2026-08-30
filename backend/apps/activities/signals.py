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

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.activities.models import ActivityAction, EntityType
from apps.activities.services import record_activity
from apps.companies.models import Membership
from apps.customers.models import Customer, CustomerStatus
from apps.projects.models import Project
from apps.tasks.models import Task

# Fields whose changes we care about, per model. Also used to compute the
# ``changed_fields`` metadata list. FK columns use their ``*_id`` attribute.
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


# --------------------------------------------------------------------------- #
# Customer
# --------------------------------------------------------------------------- #
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

    # Only field *names* are recorded — values may be PII (email, phone, notes).
    record_activity(
        action=ActivityAction.CUSTOMER_UPDATED,
        entity=instance,
        entity_type=EntityType.CUSTOMER,
        metadata={"name": instance.name, "changed_fields": changed},
    )


# --------------------------------------------------------------------------- #
# Project
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Task
# --------------------------------------------------------------------------- #
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

    # Assignment and status change are distinct listed events; emit both when a
    # single save touches both.
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


# --------------------------------------------------------------------------- #
# Membership (team role changes)
# --------------------------------------------------------------------------- #
@receiver(pre_save, sender=Membership, dispatch_uid="activities.membership_pre_save")
def _membership_pre_save(sender, instance, **kwargs) -> None:
    _snapshot(sender, instance, _MEMBERSHIP_FIELDS)


@receiver(post_save, sender=Membership, dispatch_uid="activities.membership_post_save")
def _membership_post_save(sender, instance, created, **kwargs) -> None:
    # Membership creation is not one of the audited events; only role changes are.
    if created:
        return

    old = getattr(instance, "_audit_old", None)
    changed = _changed(old, instance, _MEMBERSHIP_FIELDS)
    if "role" not in changed:
        return

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
