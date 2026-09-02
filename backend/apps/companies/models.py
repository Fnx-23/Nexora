"""Company (tenant) and membership models.

A ``Company`` is the tenant boundary for all business data in Nexora.
Every user accesses data through a ``Membership`` which carries their role
within that specific company.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.db.models import TimestampedModel

COMPANY_LOCALES = [
    ("en", "English"),
    ("fr", "Français"),
    ("es", "Español"),
    ("ar", "العربية"),
    ("de", "Deutsch"),
]


def company_logo_upload_path(instance: Company, filename: str) -> str:
    """Storage path for company logos under the company's UUID directory.

    The client-supplied name is discarded (only the validated extension is
    kept); stored names are random hex to rule out collisions and traversal.
    """
    import os
    from uuid import uuid4

    extension = os.path.splitext(filename)[1].lower()
    return f"logos/{instance.id}/{uuid4().hex}{extension}"


class RoleChoices(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    EMPLOYEE = "EMPLOYEE", "Employee"


class InvitationStatus(models.TextChoices):
    """Lifecycle of a team invitation.

    An invitation is created ``PENDING`` and becomes ``ACCEPTED`` once the
    invitee joins, ``REVOKED`` if the inviting admin withdraws it, or
    ``EXPIRED`` when ``expires_at`` passes while still pending. ``EXPIRED`` and
    ``REVOKED`` are terminal states; a consumed invitation can never be reused.
    """

    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"


INVITATION_TTL = timedelta(days=7)


class Company(TimestampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA time zone for the workspace (e.g. America/New_York).",
    )
    locale = models.CharField(
        max_length=8,
        choices=COMPANY_LOCALES,
        default="en",
        help_text="Curated interface language for the workspace.",
    )
    logo = models.ImageField(
        upload_to=company_logo_upload_path,
        blank=True,
        null=True,
        help_text="Optional workspace logo (JPEG/PNG/WebP).",
    )

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


class TeamInvitation(TimestampedModel):
    """An invitation to join a company, issued by an admin.

    The invite token is stored only as a hash (see ``apps.companies.services``):
    the model never retains the raw, unguessable value, so a database leak
    cannot be used to accept invitations directly.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    token_hash = models.CharField(max_length=128, editable=False)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(status=InvitationStatus.PENDING),
                fields=["company", "email"],
                name="uniq_pending_invitation_per_company_email",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return f"Invite {self.email} -> {self.company} ({self.status})"

    @property
    def is_expired(self) -> bool:
        return self.status == InvitationStatus.PENDING and timezone.now() >= self.expires_at

    def mark_expired(self, save: bool = True) -> None:
        """Transition a pending invitation to EXPIRED if its window has passed."""
        if self.status == InvitationStatus.PENDING and timezone.now() >= self.expires_at:
            self.status = InvitationStatus.EXPIRED
            if save:
                self.save(update_fields=["status", "updated_at"])
