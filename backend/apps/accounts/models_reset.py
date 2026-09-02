"""Password reset token model for secure forgot-password flow."""

from __future__ import annotations

import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.db.models import UUIDModel


class PasswordResetToken(UUIDModel):
    """One-time, expiring password-reset token stored as a hash."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    expires_at = models.DateTimeField(editable=False)
    used = models.BooleanField(default=False, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "used", "expires_at"], name="acc_pwdreset_token_idx"),
        ]

    @classmethod
    def create(cls, user) -> tuple[PasswordResetToken, str]:
        """Create a token and return (instance, raw_token)."""
        raw = secrets.token_urlsafe(32)
        h = hashlib.sha256(raw.encode()).hexdigest()
        instance = cls.objects.create(
            user=user,
            token_hash=h,
            expires_at=timezone.now() + timezone.timedelta(hours=1),
        )
        return instance, raw

    def is_valid(self) -> bool:
        return not self.used and self.expires_at > timezone.now()

    def mark_used(self) -> None:
        self.used = True
        self.save(update_fields=["used"])

    @classmethod
    def consume(cls, user, token: str) -> PasswordResetToken | None:
        h = hashlib.sha256(token.encode()).hexdigest()
        try:
            obj = cls.objects.get(user=user, token_hash=h)
        except cls.DoesNotExist:
            return None
        if not obj.is_valid():
            return None
        return obj
