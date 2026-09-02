"""Customer records scoped to a company."""

from django.db import models

from apps.core.db.models import TenantedModel


class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    ARCHIVED = "ARCHIVED", "Archived"


class Customer(TenantedModel):
    name = models.CharField("contact name", max_length=120, db_index=True)
    company_name = models.CharField(max_length=200, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=CustomerStatus.choices,
        default=CustomerStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name
