"""Notification model for user-facing alerts."""

from django.conf import settings
from django.db import models

from apps.core.db.models import TimestampedModel


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

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["company", "recipient"]),
        ]

    def __str__(self) -> str:
        return f"{self.verb} -> {self.recipient}"
