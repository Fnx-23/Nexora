"""Session device model for per-session tracking and revocation."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.db.models import UUIDModel


class SessionDevice(UUIDModel):
    """Tracks an authenticated browser/device session for the sessions UI."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_devices",
    )
    token_id = models.UUIDField(editable=False)
    refresh_token = models.TextField(editable=False, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    last_activity = models.DateTimeField(auto_now=True, editable=False)
    is_current = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "is_current"], name="acc_sessdev_current_idx"),
            models.Index(fields=["user", "created_at"], name="acc_sessdev_created_idx"),
        ]

    @property
    def browser(self) -> str:
        ua = self.user_agent or ""
        if "firefox" in ua.lower():
            return "Firefox"
        if "chrome" in ua.lower() or "chromium" in ua.lower():
            return "Chrome"
        if "safari" in ua.lower():
            return "Safari"
        if "edge" in ua.lower():
            return "Edge"
        if "mobile" in ua.lower():
            return "Mobile"
        return "Unknown"

    @property
    def device(self) -> str:
        ua = self.user_agent or ""
        if "mobile" in ua.lower() or "android" in ua.lower() or "iphone" in ua.lower():
            return "Mobile"
        if "windows" in ua.lower():
            return "Windows"
        if "macintosh" in ua.lower() or "mac os" in ua.lower():
            return "macOS"
        if "linux" in ua.lower():
            return "Linux"
        return "Desktop"

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.browser} ({self.ip_address or '?'})"
