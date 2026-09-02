"""Task business logic: aggregate counts and per-task activity feeds."""

from __future__ import annotations

from django.db.models import Count, Q


def annotate_task_queryset(qs):
    """Annotate a task queryset with efficient per-task completion counts.

    Used on ``list`` and ``retrieve`` to avoid N+1 aggregate queries.

    ``distinct=True`` on every aggregation is essential: joining ``comments``
    with ``checklist_items``/``subtasks`` would otherwise multiply the row count
    and inflate the totals.
    """
    return qs.annotate(
        _checklist_total=Count("checklist_items", distinct=True),
        _checklist_done=Count(
            "checklist_items",
            filter=Q(checklist_items__completed=True),
            distinct=True,
        ),
        _subtask_total=Count("subtasks", distinct=True),
        _subtask_done=Count(
            "subtasks",
            filter=Q(subtasks__completed=True),
            distinct=True,
        ),
        _comments_count=Count("comments", distinct=True),
    )


def recent_activity_for_task(task, limit=10):
    """Latest task-scoped activity feed (append-only audit log)."""
    from apps.activities.models import Activity, EntityType

    return list(
        Activity.objects.filter(
            company=task.company,
            entity_type=EntityType.TASK,
            entity_id=task.id,
        )
        .select_related("actor")
        .order_by("-timestamp")[:limit]
    )
