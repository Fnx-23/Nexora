"""CSV export generation for business reports.

Provides streaming/formatted CSV file downloads with UTF-8 BOM encoding
for Excel and spreadsheet application compatibility.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from django.http import HttpResponse
from django.utils import timezone

from apps.companies.models import Company
from apps.reports.services import (
    get_customer_overview_report,
    get_project_performance_report,
    get_team_workload_report,
    get_time_report,
)


def _build_csv_response(filename: str, headers: list[str], rows: list[list[Any]]) -> HttpResponse:
    """Build a streaming HttpResponse with UTF-8 BOM encoding and CSV rows."""
    output = io.StringIO()
    output.write("\ufeff")

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def export_project_performance_csv(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> HttpResponse:
    """Export Project Performance report as a CSV spreadsheet."""
    data = get_project_performance_report(company, filters)
    today = timezone.localdate().isoformat()
    filename = f"project-performance-{company.slug}-{today}.csv"

    headers = [
        "Project Name",
        "Status",
        "Progress (%)",
        "Completed Tasks",
        "Open Tasks",
        "Overdue Tasks",
        "Total Tasks",
        "Tracked Hours",
        "Customer",
        "Manager",
        "Start Date",
        "Deadline",
    ]

    rows = []
    for item in data["results"]:
        rows.append(
            [
                item["project_name"],
                item["status_label"],
                f"{item['progress']}%",
                item["completed_tasks"],
                item["open_tasks"],
                item["overdue_tasks"],
                item["total_tasks"],
                f"{item['tracked_hours']:.2f}",
                item["customer_name"] or "—",
                item["manager_name"] or "—",
                item["start_date"] or "—",
                item["deadline"] or "—",
            ]
        )

    summary = data["summary"]
    rows.append([])
    rows.append(
        [
            "TOTAL / AVERAGE",
            "",
            f"{summary['average_progress']}%",
            summary["total_completed_tasks"],
            summary["total_open_tasks"],
            summary["total_overdue_tasks"],
            summary["total_tasks"],
            f"{summary['total_tracked_hours']:.2f}",
            "",
            "",
            "",
            "",
        ]
    )

    return _build_csv_response(filename, headers, rows)


def export_team_workload_csv(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> HttpResponse:
    """Export Team Workload report as a CSV spreadsheet."""
    data = get_team_workload_report(company, filters)
    today = timezone.localdate().isoformat()
    filename = f"team-workload-{company.slug}-{today}.csv"

    headers = [
        "Team Member",
        "Email",
        "Role",
        "Assigned Tasks",
        "Open Tasks",
        "Completed Tasks",
        "Overdue Tasks",
        "Tracked Hours",
        "Completion Rate (%)",
    ]

    rows = []
    for item in data["results"]:
        rows.append(
            [
                item["name"],
                item["email"],
                item["role"],
                item["assigned_tasks"],
                item["open_tasks"],
                item["completed_tasks"],
                item["overdue_tasks"],
                f"{item['tracked_hours']:.2f}",
                f"{item['completion_rate']}%",
            ]
        )

    summary = data["summary"]
    rows.append([])
    rows.append(
        [
            "TOTAL / OVERALL",
            "",
            f"{summary['total_members']} members",
            summary["total_assigned_tasks"],
            summary["total_open_tasks"],
            summary["total_completed_tasks"],
            summary["total_overdue_tasks"],
            f"{summary['total_tracked_hours']:.2f}",
            f"{summary['overall_completion_rate']}%",
        ]
    )

    return _build_csv_response(filename, headers, rows)


def export_time_report_csv(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> HttpResponse:
    """Export Time Tracking report as a CSV spreadsheet.

    Includes detailed entries log, as well as project and user summary totals.
    """
    data = get_time_report(company, filters)
    today = timezone.localdate().isoformat()
    filename = f"time-report-{company.slug}-{today}.csv"

    headers = [
        "Date",
        "Project",
        "User",
        "Task",
        "Duration (Hours)",
        "Start Time",
        "End Time",
        "Description",
    ]

    rows = []
    for item in data["entries"]:
        rows.append(
            [
                item["date"],
                item["project_name"],
                item["user_name"],
                item["task_title"] or "—",
                f"{item['duration_hours']:.2f}",
                item["start_time"] or "—",
                item["end_time"] or "—",
                item["description"] or "",
            ]
        )

    summary = data["summary"]
    rows.append([])
    rows.append(
        [
            "TOTAL TIME",
            f"{summary['active_projects_count']} projects",
            f"{summary['active_users_count']} contributors",
            f"{summary['total_entries']} entries",
            f"{summary['total_hours']:.2f}",
            "",
            "",
            "",
        ]
    )

    return _build_csv_response(filename, headers, rows)


def export_customer_overview_csv(
    company: Company,
    filters: dict[str, Any] | None = None,
) -> HttpResponse:
    """Export Customer Overview report as a CSV spreadsheet."""
    data = get_customer_overview_report(company, filters)
    today = timezone.localdate().isoformat()
    filename = f"customer-overview-{company.slug}-{today}.csv"

    headers = [
        "Customer / Contact",
        "Company Name",
        "Status",
        "Active Projects",
        "Completed Projects",
        "Total Projects",
        "Open Tasks",
        "Tracked Hours",
        "Email",
        "Phone",
    ]

    rows = []
    for item in data["results"]:
        rows.append(
            [
                item["customer_name"],
                item["company_name"] or "—",
                item["status"],
                item["active_projects"],
                item["completed_projects"],
                item["total_projects"],
                item["open_tasks"],
                f"{item['hours_tracked']:.2f}",
                item["email"] or "—",
                item["phone"] or "—",
            ]
        )

    summary = data["summary"]
    rows.append([])
    rows.append(
        [
            "TOTAL",
            f"{summary['total_customers']} customers",
            f"{summary['active_customers']} active",
            summary["total_active_projects"],
            summary["total_completed_projects"],
            summary["total_active_projects"] + summary["total_completed_projects"],
            "",
            f"{summary['total_tracked_hours']:.2f}",
            "",
            "",
        ]
    )

    return _build_csv_response(filename, headers, rows)
