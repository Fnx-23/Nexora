"""The single entry point for writing audit records.

``record_activity`` is called from signal handlers (never from views). It
resolves the acting user from the request context, sanitizes metadata, and
creates the :class:`~apps.activities.models.Activity` row.

Reliability model
-----------------
Recording an audit row is best-effort and must never take down the user's actual
operation. Two safeguards enforce this:

* The record is created inside its own savepoint (``transaction.atomic``), so a
  database-level failure in the audit insert rolls back only that savepoint and
  cannot poison an enclosing transaction that the business write depends on.
* Any exception raised while building or writing the record is logged and
  swallowed rather than propagated, so a broken audit path degrades to a missing
  log line instead of a failed create/update.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from apps.activities.models import Activity, EntityType
from apps.activities.sanitizer import sanitize_metadata
from apps.core.request_context import get_actor

logger = logging.getLogger("apps.activities")

_UNSET = object()


def record_activity(
    *,
    action: str,
    company: Any = None,
    entity: Any = None,
    entity_type: str | None = None,
    entity_id: Any = None,
    actor: Any = _UNSET,
    metadata: dict[str, Any] | None = None,
) -> Activity | None:
    """Create one audit record. Returns the record, or ``None`` if it was skipped.

    ``company``/``entity_id``/``entity_type`` are inferred from ``entity`` when
    not given explicitly. ``actor`` defaults to the current request actor; pass
    ``actor=None`` explicitly to force a system-attributed record.
    """
    try:
        if entity is not None:
            if company is None:
                company = getattr(entity, "company", None)
            if entity_id is None:
                entity_id = getattr(entity, "pk", None)
            if entity_type is None:
                entity_type = entity._meta.model_name  # e.g. "customer"

        if company is None:
            # Nothing to scope the record to — cannot store it safely.
            logger.warning("Skipping activity %s: no company context.", action)
            return None

        resolved_actor = get_actor() if actor is _UNSET else actor

        # Savepoint: a DB-level failure in the audit insert rolls back only this
        # write, never an enclosing transaction the business operation depends on.
        with transaction.atomic():
            return Activity.objects.create(
                company=company,
                actor=resolved_actor,
                action=action,
                entity_type=entity_type or EntityType.CUSTOMER,
                entity_id=entity_id,
                metadata=sanitize_metadata(metadata or {}),
            )
    except Exception:  # audit must never break the business operation
        logger.exception("Failed to record activity %s", action)
        return None
