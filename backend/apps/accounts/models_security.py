"""Security event log for the account Security settings tab.

Each row records a noteworthy security action (login, password change, email
verification, session revocation, ...). Unlike the company-scoped business
``Activity`` feed, security events are **user-scoped**: they follow the
account regardless of the active company and are shown only to the owner.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.db.models import UUIDModel


class SecurityEventType(models.TextChoices):
    """The catalogue of audited account-security events."""

    LOGIN = "login", "Login"
    LOGIN_FAILED = "login_failed", "Failed login"
    PASSWORD_CHANGED = "password_changed", "Password changed"
    PASSWORD_RESET = "password_reset", "Password reset"
    EMAIL_VERIFIED = "email_verified", "Email verified"
    PROFILE_UPDATED = "profile_updated", "Profile updated"
    SESSION_REVOKED = "session_revoked", "Session revoked"
    SESSIONS_REVOKED_OTHERS = "sessions_revoked_others", "All other sessions revoked"


class SecurityEvent(UUIDModel):
    """A single user-scoped security log entry; append-only by convention."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_events",
    )
    event_type = models.CharField(
        max_length=40,
        choices=SecurityEventType.choices,
        db_index=True,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Non-sensitive contextual detail (e.g. session id).",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="acc_sec_evt_user_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} for {self.user_id}"

    def save(self, *args, **kwargs):
        """Security events may be created, never updated."""
        if not self._state.adding:
            raise ValueError("SecurityEvent records are immutable.")
        return super().save(*args, **kwargs)
