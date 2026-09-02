"""Service layer for creating notifications."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.core.request_context import get_actor
from apps.notifications.models import Notification, NotificationPreference

logger = logging.getLogger("apps.notifications")

REMINDER_DEDUP_WINDOW = timedelta(hours=24)


def _category_enabled(company: Any, recipient: Any, category: str) -> bool:
    """Return whether the recipient wants to receive a category.

    The absence of a :class:`NotificationPreference` row means "all enabled".
    """
    if not category:
        return True
    try:
        preference = NotificationPreference.objects.get(company=company, user=recipient)
    except NotificationPreference.DoesNotExist:
        return True
    return bool(getattr(preference, category, True))


def create_notification(
    *,
    company: Any,
    recipient: Any,
    verb: str,
    entity_type: str = "",
    entity_id: Any = None,
    entity_name: str = "",
    link: str = "",
    actor: Any = None,
    category: str = "",
    dedup_key: str = "",
) -> Notification | None:
    """Create a single notification for a user.

    ``actor`` defaults to the current request actor when not provided.
    Notifications carrying a ``category`` are suppressed when the recipient has
    opted out of that category. Returns the notification or ``None`` if creation
    fails or the recipient disabled the category.
    """
    if not _category_enabled(company, recipient, category):
        logger.info("Skip notification for %s: category %s disabled", recipient, category)
        return None
    try:
        if actor is None:
            actor = get_actor()
        return Notification.objects.create(
            company=company,
            recipient=recipient,
            actor=actor,
            verb=verb,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            link=link,
            category=category,
            dedup_key=dedup_key,
        )
    except Exception:
        logger.exception("Failed to create notification for user %s", recipient)
        return None


def create_unique_notification(
    *,
    window: timedelta = REMINDER_DEDUP_WINDOW,
    **kwargs: Any,
) -> Notification | None:
    """Create a notification only if a matching reminder does not already exist.

    Deduplication is keyed on (company, recipient, category, ``dedup_key``) and
    an optional recency ``window`` — deliberately independent of ``is_read``, so
    reading a reminder never causes the next Celery beat run to re-deliver it.
    When ``dedup_key`` is falsy this behaves exactly like :func:`create_notification`.
    """
    dedup_key = kwargs.get("dedup_key") or ""
    company = kwargs.get("company")
    recipient = kwargs.get("recipient")
    category = kwargs.get("category") or ""

    if (
        dedup_key
        and company
        and recipient
        and Notification.objects.filter(
            company=company,
            recipient=recipient,
            category=category,
            dedup_key=dedup_key,
            created_at__gte=timezone.now() - window,
        ).exists()
    ):
        logger.info("Notification %s for user %s already sent, skipping", dedup_key, recipient)
        return None

    return create_notification(**kwargs)
