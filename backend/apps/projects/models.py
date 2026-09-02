"""Project records scoped to a company."""

from django.conf import settings
from django.db import models

from apps.core.db.models import TenantedModel


class ProjectStatus(models.TextChoices):
    PLANNING = "PLANNING", "Planning"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    ON_HOLD = "ON_HOLD", "On hold"
    COMPLETED = "COMPLETED", "Completed"
    ARCHIVED = "ARCHIVED", "Archived"


class ProjectPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class Project(TenantedModel):
    name = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True, default="")
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=ProjectPriority.choices,
        default=ProjectPriority.MEDIUM,
        db_index=True,
    )
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self) -> str:
        return self.name


class ProjectMember(TenantedModel):
    """A company user assigned to a project.

    Assignment is tenant-isolated: the ``user`` must hold an active membership
    in the same company as the ``project`` (enforced in the serializer/service).
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="uniq_project_member",
            ),
        ]
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} -> {self.project.name}"
