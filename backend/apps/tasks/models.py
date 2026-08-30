"""Task records scoped to a company."""

from django.conf import settings
from django.db import models

from apps.core.db.models import TenantedModel


class TaskStatus(models.TextChoices):
    TODO = "TODO", "To do"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    IN_REVIEW = "IN_REVIEW", "In review"
    DONE = "DONE", "Done"
    CANCELLED = "CANCELLED", "Cancelled"


class TaskPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class Task(TenantedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self) -> str:
        return self.title
