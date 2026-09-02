"""Business reporting aggregation services.

Efficient, tenant-scoped calculation engine for:
1. Project Performance
2. Team Workload
3. Time Report
4. Customer Overview

All queries strictly enforce company isolation, use database-level aggregates,
and avoid N+1 queries.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.companies.models import Company, Membership
from apps.customers.models import Customer
from apps.projects.models import Project, ProjectStatus
from apps.projects.services import compute_progress
from apps.tasks.models import Task, TaskStatus
from apps.time_tracking.models import TimeEntry

OPEN_TASK_STATUSES = [
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.IN_REVIEW,
]


def _duration_to_hours(duration: timedelta | None) -> float:
    if not duration:
        return 0.0
    return round(duration.total_seconds() / 3600.0, 2)


def get_project_performance_report(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate project performance metrics for the active company.

    Fields per project:
    - project (id, name)
    - status
    - progress (derived from completed/total tasks)
    - completed/open tasks
    - overdue tasks
    - tracked hours
    """
    filters = filters or {}
    today = timezone.localdate()

    qs = Project.objects.filter(company=company).select_related("customer", "manager")

    if filters.get("project"):
        qs = qs.filter(id=filters["project"])
    if filters.get("customer"):
        qs = qs.filter(customer_id=filters["customer"])
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])

    qs = qs.annotate(
        total_tasks=Count("tasks", distinct=True),
        completed_tasks=Count(
            "tasks",
            filter=Q(tasks__status=TaskStatus.DONE),
            distinct=True,
        ),
        open_tasks=Count(
            "tasks",
            filter=Q(tasks__status__in=OPEN_TASK_STATUSES),
            distinct=True,
        ),
        overdue_tasks=Count(
            "tasks",
            filter=Q(
                tasks__status__in=OPEN_TASK_STATUSES,
                tasks__due_date__isnull=False,
                tasks__due_date__lt=today,
            ),
            distinct=True,
        ),
    ).order_by("name")

    time_qs = TimeEntry.objects.filter(company=company)
    if filters.get("date_from"):
        time_qs = time_qs.filter(date__gte=filters["date_from"])
    if filters.get("date_to"):
        time_qs = time_qs.filter(date__lte=filters["date_to"])
    if filters.get("user"):
        time_qs = time_qs.filter(user_id=filters["user"])
    if filters.get("project"):
        time_qs = time_qs.filter(project_id=filters["project"])
    if filters.get("customer"):
        time_qs = time_qs.filter(project__customer_id=filters["customer"])

    project_hours_map = {
        row["project_id"]: _duration_to_hours(row["total_duration"])
        for row in time_qs.values("project_id").annotate(total_duration=Sum("duration"))
    }

    items: list[dict[str, Any]] = []
    for p in qs:
        if p.total_tasks > 0:
            prog = compute_progress(p.completed_tasks, p.total_tasks)
        elif p.status == ProjectStatus.COMPLETED:
            prog = 100
        else:
            prog = 0

        tracked_hours = project_hours_map.get(p.id, 0.0)

        items.append(
            {
                "project_id": str(p.id),
                "project_name": p.name,
                "status": p.status,
                "status_label": p.get_status_display(),
                "priority": p.priority,
                "progress": prog,
                "completed_tasks": p.completed_tasks,
                "open_tasks": p.open_tasks,
                "total_tasks": p.total_tasks,
                "overdue_tasks": p.overdue_tasks,
                "tracked_hours": tracked_hours,
                "customer_id": str(p.customer_id) if p.customer_id else None,
                "customer_name": (
                    (p.customer.company_name or p.customer.name) if p.customer else None
                ),
                "manager_name": (
                    (p.manager.get_full_name() or p.manager.email) if p.manager else None
                ),
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "deadline": p.deadline.isoformat() if p.deadline else None,
            }
        )

    total_projects = len(items)
    total_tracked_hours = round(sum(item["tracked_hours"] for item in items), 2)
    avg_progress = (
        round(sum(item["progress"] for item in items) / total_projects, 1)
        if total_projects > 0
        else 0.0
    )
    total_tasks = sum(item["total_tasks"] for item in items)
    total_completed_tasks = sum(item["completed_tasks"] for item in items)
    total_open_tasks = sum(item["open_tasks"] for item in items)
    total_overdue_tasks = sum(item["overdue_tasks"] for item in items)

    status_counts: dict[str, int] = {}
    for item in items:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    status_distribution = [
        {"status": s, "label": label, "count": status_counts.get(s, 0)}
        for s, label in ProjectStatus.choices
    ]

    return {
        "summary": {
            "total_projects": total_projects,
            "total_tracked_hours": total_tracked_hours,
            "average_progress": avg_progress,
            "total_tasks": total_tasks,
            "total_completed_tasks": total_completed_tasks,
            "total_open_tasks": total_open_tasks,
            "total_overdue_tasks": total_overdue_tasks,
        },
        "status_distribution": status_distribution,
        "results": items,
    }


def get_team_workload_report(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate team workload metrics for active company members.

    Fields per team member:
    - team member (user_id, name, email, role)
    - assigned tasks
    - open tasks
    - completed tasks
    - tracked hours
    - overdue tasks
    """
    filters = filters or {}
    today = timezone.localdate()

    mem_qs = Membership.objects.filter(company=company, is_active=True).select_related("user")
    if filters.get("user"):
        mem_qs = mem_qs.filter(user_id=filters["user"])

    task_qs = Task.objects.filter(company=company, assignee__isnull=False)
    if filters.get("project"):
        task_qs = task_qs.filter(project_id=filters["project"])
    if filters.get("customer"):
        task_qs = task_qs.filter(project__customer_id=filters["customer"])

    task_stats_rows = task_qs.values("assignee_id").annotate(
        total_assigned=Count("id"),
        completed=Count("id", filter=Q(status=TaskStatus.DONE)),
        open=Count("id", filter=Q(status__in=OPEN_TASK_STATUSES)),
        overdue=Count(
            "id",
            filter=Q(
                status__in=OPEN_TASK_STATUSES,
                due_date__isnull=False,
                due_date__lt=today,
            ),
        ),
    )
    user_task_stats = {
        row["assignee_id"]: {
            "assigned": row["total_assigned"],
            "completed": row["completed"],
            "open": row["open"],
            "overdue": row["overdue"],
        }
        for row in task_stats_rows
    }

    time_qs = TimeEntry.objects.filter(company=company)
    if filters.get("date_from"):
        time_qs = time_qs.filter(date__gte=filters["date_from"])
    if filters.get("date_to"):
        time_qs = time_qs.filter(date__lte=filters["date_to"])
    if filters.get("project"):
        time_qs = time_qs.filter(project_id=filters["project"])
    if filters.get("customer"):
        time_qs = time_qs.filter(project__customer_id=filters["customer"])

    user_hours_map = {
        row["user_id"]: _duration_to_hours(row["total_duration"])
        for row in time_qs.values("user_id").annotate(total_duration=Sum("duration"))
    }

    items: list[dict[str, Any]] = []
    for m in mem_qs:
        user = m.user
        default_stats = {"assigned": 0, "completed": 0, "open": 0, "overdue": 0}
        stats = user_task_stats.get(user.id, default_stats)
        tracked_hours = user_hours_map.get(user.id, 0.0)

        assigned_tasks = stats["assigned"]
        completed_tasks = stats["completed"]
        open_tasks = stats["open"]
        overdue_tasks = stats["overdue"]
        completion_rate = (
            round((completed_tasks / assigned_tasks) * 100) if assigned_tasks > 0 else 0
        )

        items.append(
            {
                "user_id": str(user.id),
                "name": user.get_full_name() or user.email.split("@")[0],
                "email": user.email,
                "role": m.role,
                "assigned_tasks": assigned_tasks,
                "open_tasks": open_tasks,
                "completed_tasks": completed_tasks,
                "overdue_tasks": overdue_tasks,
                "tracked_hours": tracked_hours,
                "completion_rate": completion_rate,
            }
        )

    items.sort(key=lambda x: (x["assigned_tasks"], x["tracked_hours"]), reverse=True)

    total_members = len(items)
    total_assigned_tasks = sum(item["assigned_tasks"] for item in items)
    total_open_tasks = sum(item["open_tasks"] for item in items)
    total_completed_tasks = sum(item["completed_tasks"] for item in items)
    total_overdue_tasks = sum(item["overdue_tasks"] for item in items)
    total_tracked_hours = round(sum(item["tracked_hours"] for item in items), 2)
    overall_completion_rate = (
        round((total_completed_tasks / total_assigned_tasks) * 100)
        if total_assigned_tasks > 0
        else 0
    )

    return {
        "summary": {
            "total_members": total_members,
            "total_assigned_tasks": total_assigned_tasks,
            "total_open_tasks": total_open_tasks,
            "total_completed_tasks": total_completed_tasks,
            "total_overdue_tasks": total_overdue_tasks,
            "total_tracked_hours": total_tracked_hours,
            "overall_completion_rate": overall_completion_rate,
        },
        "results": items,
    }


def get_time_report(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate time tracking report for the active company.

    Breakdowns:
    - hours by project
    - hours by user
    - date range timeline
    - detailed log entries
    """
    filters = filters or {}

    time_qs = TimeEntry.objects.filter(company=company).select_related(
        "project", "user", "task", "project__customer"
    )

    if filters.get("date_from"):
        time_qs = time_qs.filter(date__gte=filters["date_from"])
    if filters.get("date_to"):
        time_qs = time_qs.filter(date__lte=filters["date_to"])
    if filters.get("project"):
        time_qs = time_qs.filter(project_id=filters["project"])
    if filters.get("user"):
        time_qs = time_qs.filter(user_id=filters["user"])
    if filters.get("customer"):
        time_qs = time_qs.filter(project__customer_id=filters["customer"])

    overall_agg = time_qs.aggregate(total_duration=Sum("duration"), count=Count("id"))
    total_hours = _duration_to_hours(overall_agg["total_duration"])
    total_entries = overall_agg["count"] or 0

    by_project_qs = (
        time_qs.values(
            "project_id",
            "project__name",
            "project__customer__company_name",
            "project__customer__name",
        )
        .annotate(total_duration=Sum("duration"), entry_count=Count("id"))
        .order_by("-total_duration")
    )
    hours_by_project = []
    for row in by_project_qs:
        hours = _duration_to_hours(row["total_duration"])
        pct = round((hours / total_hours) * 100, 1) if total_hours > 0 else 0.0
        cust_name = (
            row["project__customer__company_name"] or row["project__customer__name"]
            if row.get("project__customer__name") or row.get("project__customer__company_name")
            else "Internal"
        )
        hours_by_project.append(
            {
                "project_id": str(row["project_id"]),
                "project_name": row["project__name"],
                "customer_name": cust_name,
                "hours": hours,
                "entry_count": row["entry_count"],
                "percentage": pct,
            }
        )

    by_user_qs = (
        time_qs.values(
            "user_id",
            "user__first_name",
            "user__last_name",
            "user__email",
        )
        .annotate(total_duration=Sum("duration"), entry_count=Count("id"))
        .order_by("-total_duration")
    )
    hours_by_user = []
    for row in by_user_qs:
        hours = _duration_to_hours(row["total_duration"])
        pct = round((hours / total_hours) * 100, 1) if total_hours > 0 else 0.0
        first = row["user__first_name"] or ""
        last = row["user__last_name"] or ""
        full_name = f"{first} {last}".strip() or row["user__email"].split("@")[0]
        hours_by_user.append(
            {
                "user_id": str(row["user_id"]),
                "user_name": full_name,
                "email": row["user__email"],
                "hours": hours,
                "entry_count": row["entry_count"],
                "percentage": pct,
            }
        )

    timeline_qs = (
        time_qs.values("date")
        .annotate(total_duration=Sum("duration"), entry_count=Count("id"))
        .order_by("date")
    )
    timeline = [
        {
            "date": row["date"].isoformat(),
            "hours": _duration_to_hours(row["total_duration"]),
            "entry_count": row["entry_count"],
        }
        for row in timeline_qs
    ]

    entry_rows = time_qs.order_by("-date", "-start_time")[:200]
    entries = [
        {
            "id": str(e.id),
            "date": e.date.isoformat(),
            "project_id": str(e.project_id),
            "project_name": e.project.name,
            "user_id": str(e.user_id),
            "user_name": e.user.get_full_name() or e.user.email,
            "task_id": str(e.task_id) if e.task_id else None,
            "task_title": e.task.title if e.task else None,
            "duration_hours": _duration_to_hours(e.duration),
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "description": e.description,
        }
        for e in entry_rows
    ]

    days_count = len(timeline)
    avg_daily_hours = round(total_hours / days_count, 1) if days_count > 0 else 0.0

    return {
        "summary": {
            "total_hours": total_hours,
            "total_entries": total_entries,
            "active_projects_count": len(hours_by_project),
            "active_users_count": len(hours_by_user),
            "days_with_activity": days_count,
            "avg_daily_hours": avg_daily_hours,
        },
        "hours_by_project": hours_by_project,
        "hours_by_user": hours_by_user,
        "timeline": timeline,
        "entries": entries,
    }


def get_customer_overview_report(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate customer overview report for the active company.

    Fields per customer:
    - customer (id, name, company_name, email)
    - active projects (PLANNING, IN_PROGRESS, ON_HOLD)
    - completed projects (COMPLETED)
    - total projects
    - hours tracked
    """
    filters = filters or {}

    cust_qs = Customer.objects.filter(company=company)

    if filters.get("customer"):
        cust_qs = cust_qs.filter(id=filters["customer"])
    if filters.get("status"):
        cust_qs = cust_qs.filter(status=filters["status"])

    active_project_statuses = [
        ProjectStatus.PLANNING,
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.ON_HOLD,
    ]
    cust_qs = cust_qs.annotate(
        total_projects=Count("projects", distinct=True),
        active_projects=Count(
            "projects",
            filter=Q(projects__status__in=active_project_statuses),
            distinct=True,
        ),
        completed_projects=Count(
            "projects",
            filter=Q(projects__status=ProjectStatus.COMPLETED),
            distinct=True,
        ),
    ).order_by("name")

    time_qs = TimeEntry.objects.filter(company=company, project__customer__isnull=False)
    if filters.get("date_from"):
        time_qs = time_qs.filter(date__gte=filters["date_from"])
    if filters.get("date_to"):
        time_qs = time_qs.filter(date__lte=filters["date_to"])
    if filters.get("user"):
        time_qs = time_qs.filter(user_id=filters["user"])
    if filters.get("project"):
        time_qs = time_qs.filter(project_id=filters["project"])
    if filters.get("customer"):
        time_qs = time_qs.filter(project__customer_id=filters["customer"])

    customer_hours_map = {
        row["project__customer_id"]: _duration_to_hours(row["total_duration"])
        for row in time_qs.values("project__customer_id").annotate(total_duration=Sum("duration"))
    }

    task_qs = Task.objects.filter(
        company=company,
        project__customer__isnull=False,
        status__in=OPEN_TASK_STATUSES,
    )
    if filters.get("project"):
        task_qs = task_qs.filter(project_id=filters["project"])
    if filters.get("customer"):
        task_qs = task_qs.filter(project__customer_id=filters["customer"])

    customer_tasks_map = {
        row["project__customer_id"]: row["open_task_count"]
        for row in task_qs.values("project__customer_id").annotate(open_task_count=Count("id"))
    }

    items: list[dict[str, Any]] = []
    for c in cust_qs:
        hours = customer_hours_map.get(c.id, 0.0)
        open_tasks = customer_tasks_map.get(c.id, 0)

        items.append(
            {
                "customer_id": str(c.id),
                "customer_name": c.name,
                "company_name": c.company_name,
                "display_name": c.company_name or c.name,
                "email": c.email,
                "phone": c.phone,
                "status": c.status,
                "is_active": c.is_active,
                "active_projects": c.active_projects,
                "completed_projects": c.completed_projects,
                "total_projects": c.total_projects,
                "open_tasks": open_tasks,
                "hours_tracked": hours,
            }
        )

    items.sort(key=lambda x: (x["active_projects"], x["hours_tracked"]), reverse=True)

    total_customers = len(items)
    active_customers = sum(1 for c in items if c["active_projects"] > 0)
    total_active_projects = sum(c["active_projects"] for c in items)
    total_completed_projects = sum(c["completed_projects"] for c in items)
    total_tracked_hours = round(sum(c["hours_tracked"] for c in items), 2)

    return {
        "summary": {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_active_projects": total_active_projects,
            "total_completed_projects": total_completed_projects,
            "total_tracked_hours": total_tracked_hours,
        },
        "results": items,
    }


def get_executive_summary(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return top-level cross-module summary for rapid executive dashboard view."""
    perf = get_project_performance_report(company, filters)
    workload = get_team_workload_report(company, filters)
    time_rep = get_time_report(company, filters)
    cust = get_customer_overview_report(company, filters)

    return {
        "project_performance": perf["summary"],
        "team_workload": workload["summary"],
        "time_report": time_rep["summary"],
        "customer_overview": cust["summary"],
    }
