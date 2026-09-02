"""Task records scoped to a company."""

import re

from django.conf import settings
from django.core.validators import RegexValidator
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


class TaskLabel(TenantedModel):
    """A reusable company-scoped tag that can be applied to many tasks."""

    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        default="#3b82f6",
        validators=[RegexValidator(regex=re.compile(r"^#[0-9a-fA-F]{6}$"))],
        help_text="Hex color for the label chip, e.g. #3b82f6.",
    )

    class Meta:
        verbose_name = "task label"
        verbose_name_plural = "task labels"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_task_label_name_per_company",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Task(TenantedModel):
    title = models.CharField(max_length=200, db_index=True)
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
    labels = models.ManyToManyField(
        TaskLabel,
        blank=True,
        related_name="tasks",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self) -> str:
        return self.title


class TaskComment(TenantedModel):
    """A comment on a task, ordered oldest-first."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_comments",
    )
    body = models.TextField()

    class Meta:
        verbose_name = "task comment"
        verbose_name_plural = "task comments"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["task", "created_at"])]

    def __str__(self) -> str:
        return f"Comment on {self.task_id} by {self.author_id}"


class TaskChecklistItem(TenantedModel):
    """A single checkbox row within a task's checklist."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="checklist_items")
    text = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "task checklist item"
        verbose_name_plural = "task checklist items"
        ordering = ["position", "id"]
        indexes = [models.Index(fields=["task", "position"])]

    def __str__(self) -> str:
        return self.text


class TaskSubtask(TenantedModel):
    """A lightweight single-level checklist-style breakdown of a task."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "task subtask"
        verbose_name_plural = "task subtasks"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.title
