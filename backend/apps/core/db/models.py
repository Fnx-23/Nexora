"""Abstract model bases shared across Nexora applications."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantedModel(TimestampedModel):
    """
    Base class for every company-scoped business entity.

    Concrete models carry a mandatory ``company`` foreign key. Row-level tenant
    isolation is enforced at the API boundary by scoping querysets to the
    request's active company (see ``apps.core.api.views.TenantScopedModelViewSet``
    and ``apps.core.api.permissions.IsCompanyMember``).
    """

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        abstract = True
