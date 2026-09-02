"""Project business logic: health, progress and aggregate metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.db.models import Count, Q, Sum
from django.db.models.enums import TextChoices
from django.utils import timezone

from apps.projects.models import Project, ProjectStatus
from apps.tasks.models import Task, TaskStatus


class ProjectHealth(TextChoices):
    """Derived health of a project based on real status/deadline/task data."""

    NOT_STARTED = "NOT_STARTED", "Not started"
    ON_TRACK = "ON_TRACK", "On track"
    AT_RISK = "AT_RISK", "At risk"
    OVERDUE = "OVERDUE", "Overdue"
    COMPLETED = "COMPLETED", "Completed"


@dataclass
class ProjectMetrics:
    """Aggregate metrics computed for a single project."""

    task_count: int = 0
    done_count: int = 0
    in_progress_count: int = 0
    todo_count: int = 0
    overdue_count: int = 0
    tracked_hours: float = 0.0
    progress: int = 0
    health: str = ProjectHealth.NOT_STARTED


def compute_progress(done_count: int, task_count: int) -> int:
    """Return the percentage of completed tasks (0 if no tasks).

    Progress is always derived from tasks — never a hand-entered percentage.
    A project with zero tasks has no completed fraction, so progress is 0.
    """
    if task_count <= 0:
        return 0
    return round((done_count / task_count) * 100)


def compute_health(
    status: str,
    deadline: date | None,
    progress: int,
    overdue_count: int,
) -> str:
    """Derive a health indicator from actual project/task state.

    Priority of decisions:
    1. Completed project => COMPLETED.
    2. Overdue tasks still open or past deadline => OVERDUE.
    3. Progress lags the calendar with a close deadline => AT_RISK.
    4. No work started yet => NOT_STARTED.
    5. Otherwise => ON_TRACK.
    """
    if status == ProjectStatus.COMPLETED.value:
        return ProjectHealth.COMPLETED.value

    today = timezone.localdate()
    if overdue_count > 0:
        return ProjectHealth.OVERDUE.value
    if deadline is not None and deadline < today:
        return ProjectHealth.OVERDUE.value

    if progress == 0:
        return ProjectHealth.NOT_STARTED.value

    if deadline is not None:
        remaining_days = (deadline - today).days
        if remaining_days <= 7 and progress < 60:
            return ProjectHealth.AT_RISK.value

    return ProjectHealth.ON_TRACK.value


def _overdue_task_ids(project) -> set:
    """Ids of open tasks whose due date is before today (incomplete overdue)."""
    qs = Task.objects.filter(
        project=project,
    ).exclude(
        Q(status=TaskStatus.DONE) | Q(status=TaskStatus.CANCELLED),
    )
    return set(qs.values_list("id", flat=True))


def metrics_for_project(project: Project) -> ProjectMetrics:
    """Compute aggregate metrics for a single project via one query."""
    base = Task.objects.filter(project=project)
    total = base.count()
    done = base.filter(status=TaskStatus.DONE).count()
    in_progress = base.filter(status=TaskStatus.IN_PROGRESS).count()
    todo = base.filter(status=TaskStatus.TODO).count()

    open_statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
    today = timezone.localdate()
    overdue = (
        base.filter(status__in=open_statuses)
        .filter(due_date__isnull=False, due_date__lt=today)
        .count()
    )

    tracked_total = project.time_entries.aggregate(total=Sum("duration"))["total"]
    tracked_hours = round(tracked_total.total_seconds() / 3600.0, 2) if tracked_total else 0.0

    progress = compute_progress(done, total)
    health = compute_health(
        project.status,
        project.deadline,
        progress,
        overdue,
    )

    return ProjectMetrics(
        task_count=total,
        done_count=done,
        in_progress_count=in_progress,
        todo_count=todo,
        overdue_count=overdue,
        tracked_hours=tracked_hours,
        progress=progress,
        health=health,
    )


def annotate_project_queryset(qs):
    """Annotate a project queryset with efficient per-project counts/hours.

    Used on ``list`` to avoid N+1 aggregate queries. Progress and health are
    derived in Python from the annotated numbers.

    ``distinct=True`` on every aggregation is essential: joining both ``tasks``
    and ``time_entries`` would otherwise multiply the row count and inflate the
    task/overdue counts.
    """
    open_statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
    today = timezone.localdate()
    return qs.annotate(
        _task_count=Count("tasks", distinct=True),
        _done_count=Count("tasks", filter=Q(tasks__status=TaskStatus.DONE), distinct=True),
        _in_progress_count=Count(
            "tasks", filter=Q(tasks__status=TaskStatus.IN_PROGRESS), distinct=True
        ),
        _todo_count=Count("tasks", filter=Q(tasks__status=TaskStatus.TODO), distinct=True),
        _overdue_count=Count(
            "tasks",
            filter=Q(tasks__status__in=open_statuses)
            & Q(tasks__due_date__isnull=False)
            & Q(tasks__due_date__lt=today),
            distinct=True,
        ),
        _tracked_hours=Sum("time_entries__duration"),
        _member_count=Count("members", distinct=True),
    )


def recent_activity_for_project(project, limit=10):
    """Latest project-scoped activity feed (append-only audit log)."""
    from apps.activities.models import Activity, EntityType

    return list(
        Activity.objects.filter(
            company=project.company,
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        .select_related("actor")
        .order_by("-timestamp")[:limit]
    )


def metrics_from_annotated(project, tasks) -> ProjectMetrics:
    """Build metrics from an annotated project row (list view).

    ``tasks`` may be an annotated ``_task_count`` etc.; we read attributes
    defensively and fall back to live aggregate computation when the
    annotation is absent (e.g. after a single-object query).
    """
    total = getattr(project, "_task_count", None)
    done = getattr(project, "_done_count", None)
    in_progress = getattr(project, "_in_progress_count", None)
    todo = getattr(project, "_todo_count", None)
    overdue = getattr(project, "_overdue_count", None)
    tracked = getattr(project, "_tracked_hours", None)

    if total is not None:
        total = total or 0
        done = done or 0
        in_progress = in_progress or 0
        todo = todo or 0
        overdue = overdue or 0
        hours = round(tracked.total_seconds() / 3600.0, 2) if tracked else 0.0
    else:
        m = metrics_for_project(project)
        return m

    progress = compute_progress(done, total)
    health = compute_health(project.status, project.deadline, progress, overdue)
    return ProjectMetrics(
        task_count=total,
        done_count=done,
        in_progress_count=in_progress,
        todo_count=todo,
        overdue_count=overdue,
        tracked_hours=hours,
        progress=progress,
        health=health,
    )
