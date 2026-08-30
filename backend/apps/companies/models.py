"""Company (tenant) and membership models.

A ``Company`` is the tenant boundary for all business data in Nexora.
Every user accesses data through a ``Membership`` which carries their role
within that specific company.
"""

from django.conf import settings
from django.db import models

from apps.core.db.models import TimestampedModel


class RoleChoices(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    EMPLOYEE = "EMPLOYEE", "Employee"


class Company(TimestampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Membership(TimestampedModel):
    """Links a user to a company together with their role in it."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "user"],
                name="uniq_membership_per_company",
            ),
        ]
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.company} ({self.role})"
