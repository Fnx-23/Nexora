"""Notification models for user-facing alerts."""

from django.conf import settings
from django.db import models

from apps.core.db.models import TimestampedModel


class NotificationCategory(models.TextChoices):
    """Every subscribable notification type; maps 1:1 to preferences."""

    TASK_ASSIGNED = "task_assigned", "Task assignments"
    TASK_DUE_SOON = "task_due_soon", "Task due soon"
    TASK_OVERDUE = "task_overdue", "Task overdue"
    TASK_COMMENT = "task_comment", "Task comments"
    PROJECT_ASSIGNED = "project_assigned", "Project assignments"
    PROJECT_DEADLINE = "project_deadline", "Project deadlines"
    INVITATION_RECEIVED = "invitation_received", "Invitations"
    ROLE_CHANGED = "role_changed", "Role changes"


class Notification(TimestampedModel):
    """A single notification delivered to a specific user within a company."""

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="+",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    verb = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=40, blank=True, default="")
    entity_id = models.UUIDField(null=True, blank=True)
    entity_name = models.CharField(max_length=200, blank=True, default="")
    link = models.CharField(max_length=500, blank=True, default="")
    is_read = models.BooleanField(default=False, db_index=True)
    category = models.CharField(
        max_length=40,
        choices=NotificationCategory.choices,
        blank=True,
        default="",
        db_index=True,
    )
    dedup_key = models.CharField(max_length=200, blank=True, default="", db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["company", "recipient"]),
            models.Index(fields=["company", "recipient", "category", "dedup_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.verb} -> {self.recipient}"


class NotificationPreference(TimestampedModel):
    """Per-company opt-out flags for a user.

    Absence of a row means every category is enabled; a row with a flag set to
    ``False`` suppresses that category when the notification is created.
    """

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="+",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    task_assigned = models.BooleanField(default=True)
    task_due_soon = models.BooleanField(default=True)
    task_overdue = models.BooleanField(default=True)
    task_comment = models.BooleanField(default=True)
    project_assigned = models.BooleanField(default=True)
    project_deadline = models.BooleanField(default=True)
    invitation_received = models.BooleanField(default=True)
    role_changed = models.BooleanField(default=True)
    email_task_assigned = models.BooleanField(default=True)
    email_task_due_soon = models.BooleanField(default=True)
    email_task_overdue = models.BooleanField(default=True)
    email_task_comment = models.BooleanField(default=True)
    email_project_assigned = models.BooleanField(default=True)
    email_project_deadline = models.BooleanField(default=True)
    email_invitation_received = models.BooleanField(default=True)
    email_role_changed = models.BooleanField(default=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "user"],
                name="uniq_notification_preference_per_company_user",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "user"]),
        ]

    def __str__(self) -> str:
        return f"Preferences for {self.user} @ {self.company}"
