"""Immutable audit-log records.

An :class:`Activity` captures a single noteworthy business event (a customer
was created, a task's status changed, a teammate's role was changed, ...).
Records are:

* **tenant scoped** — every row carries the owning ``company``; the API filters
  strictly to the request's active company.
* **append-only** — :meth:`Activity.save` forbids updates and there is no API
  write path, so the log cannot be rewritten after the fact.
* **actor-attributed** — ``actor`` is the user who caused the event (or ``NULL``
  for system actions such as data migrations).

Records are produced centrally by model signals (see ``apps.activities.signals``
and ``apps.activities.services.record_activity``), never by view code.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.db.models import UUIDModel


class ActivityAction(models.TextChoices):
    """The catalogue of audited business events."""

    CUSTOMER_CREATED = "customer.created", "Customer created"
    CUSTOMER_UPDATED = "customer.updated", "Customer updated"
    CUSTOMER_ARCHIVED = "customer.archived", "Customer archived"
    PROJECT_CREATED = "project.created", "Project created"
    PROJECT_UPDATED = "project.updated", "Project updated"
    PROJECT_STATUS_CHANGED = "project.status_changed", "Project status changed"
    TASK_CREATED = "task.created", "Task created"
    TASK_ASSIGNED = "task.assigned", "Task assigned"
    TASK_STATUS_CHANGED = "task.status_changed", "Task status changed"
    TEAM_ROLE_CHANGED = "team.role_changed", "Team role changed"


class EntityType(models.TextChoices):
    """The kind of object an activity refers to."""

    CUSTOMER = "customer", "Customer"
    PROJECT = "project", "Project"
    TASK = "task", "Task"
    MEMBERSHIP = "membership", "Membership"


class Activity(UUIDModel):
    """A single append-only audit-log entry scoped to one company."""

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        editable=False,
        help_text="User who caused the event; NULL for system actions.",
    )
    action = models.CharField(
        max_length=40,
        choices=ActivityAction.choices,
        editable=False,
    )
    entity_type = models.CharField(
        max_length=40,
        choices=EntityType.choices,
        editable=False,
    )
    entity_id = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        help_text="Primary key of the affected object (retained even if it is later deleted).",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
        help_text="Non-sensitive contextual detail. Sanitized before storage.",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)

    class Meta:
        verbose_name = "activity"
        verbose_name_plural = "activities"
        ordering = ["-timestamp"]
        indexes = [
            # Primary access pattern: a company's reverse-chronological feed.
            models.Index(fields=["company", "-timestamp"]),
            # Per-entity history ("what happened to this project?").
            models.Index(fields=["company", "entity_type", "entity_id"]),
            # Filtered feeds by action type and by actor.
            models.Index(fields=["company", "action"]),
            models.Index(fields=["company", "actor"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} ({self.entity_type}:{self.entity_id})"

    def save(self, *args, **kwargs):
        """Enforce append-only semantics: an activity may be created, never updated."""
        if not self._state.adding:
            raise ValueError("Activity records are immutable and cannot be updated.")
        return super().save(*args, **kwargs)
