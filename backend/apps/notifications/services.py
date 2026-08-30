"""Service layer for creating notifications."""

from __future__ import annotations

import logging
from typing import Any

from apps.core.request_context import get_actor
from apps.notifications.models import Notification

logger = logging.getLogger("apps.notifications")


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
) -> Notification | None:
    """Create a single notification for a user.

    ``actor`` defaults to the current request actor when not provided.
    Returns the notification or ``None`` if creation fails.
    """
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
        )
    except Exception:
        logger.exception("Failed to create notification for user %s", recipient)
        return None
