"""API views for Business Reporting and Exports."""

from apps.core.api.permissions import IsCompanyMember
from apps.reports.exports import (
    export_customer_overview_csv,
    export_project_performance_csv,
    export_team_workload_csv,
    export_time_report_csv,
)
from apps.reports.services import (
    get_customer_overview_report,
    get_executive_summary,
    get_project_performance_report,
    get_team_workload_report,
    get_time_report,
)
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def _extract_filters(request) -> dict:
    """Extract standard report filter parameters from request query."""
    params = request.query_params
    filters = {}
    if params.get("project"):
        filters["project"] = params.get("project")
    if params.get("customer"):
        filters["customer"] = params.get("customer")
    if params.get("user"):
        filters["user"] = params.get("user")
    if params.get("status"):
        filters["status"] = params.get("status")
    if params.get("date_from"):
        filters["date_from"] = params.get("date_from")
    if params.get("date_to"):
        filters["date_to"] = params.get("date_to")
    return filters


COMMON_REPORT_PARAMS = [
    OpenApiParameter("date_from", str, description="Start date (YYYY-MM-DD) for time tracking"),
    OpenApiParameter("date_to", str, description="End date (YYYY-MM-DD) for time tracking"),
    OpenApiParameter("project", str, description="Filter by project ID"),
    OpenApiParameter("user", str, description="Filter by user ID"),
    OpenApiParameter("customer", str, description="Filter by customer ID"),
    OpenApiParameter("status", str, description="Filter by status where applicable"),
    OpenApiParameter("export", str, description="Set to 'csv' to download report spreadsheet"),
]


@extend_schema(
    tags=["Reports"],
    description=(
        "Project Performance report: status, progress %, task breakdown, "
        "overdue tasks, and tracked hours."
    ),
    parameters=COMMON_REPORT_PARAMS,
)
class ProjectPerformanceReportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)

        if request.query_params.get("export") == "csv":
            return export_project_performance_csv(company, filters)

        data = get_project_performance_report(company, filters)
        return Response(data)


@extend_schema(
    tags=["Reports"],
    description="Export Project Performance report as CSV file.",
    parameters=COMMON_REPORT_PARAMS,
)
class ProjectPerformanceExportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)
        return export_project_performance_csv(company, filters)


@extend_schema(
    tags=["Reports"],
    description=(
        "Team Workload report: assigned tasks, open/completed/overdue tasks, "
        "tracked hours per member."
    ),
    parameters=COMMON_REPORT_PARAMS,
)
class TeamWorkloadReportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)

        if request.query_params.get("export") == "csv":
            return export_team_workload_csv(company, filters)

        data = get_team_workload_report(company, filters)
        return Response(data)


@extend_schema(
    tags=["Reports"],
    description="Export Team Workload report as CSV file.",
    parameters=COMMON_REPORT_PARAMS,
)
class TeamWorkloadExportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)
        return export_team_workload_csv(company, filters)


@extend_schema(
    tags=["Reports"],
    description=(
        "Time report: hours by project, hours by user, date range timeline, "
        "and detailed log entries."
    ),
    parameters=COMMON_REPORT_PARAMS,
)
class TimeReportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)

        if request.query_params.get("export") == "csv":
            return export_time_report_csv(company, filters)

        data = get_time_report(company, filters)
        return Response(data)


@extend_schema(
    tags=["Reports"],
    description="Export Time report as CSV file.",
    parameters=COMMON_REPORT_PARAMS,
)
class TimeReportExportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)
        return export_time_report_csv(company, filters)


@extend_schema(
    tags=["Reports"],
    description=(
        "Customer Overview report: active/completed projects, open tasks, "
        "and hours tracked per customer."
    ),
    parameters=COMMON_REPORT_PARAMS,
)
class CustomerOverviewReportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)

        if request.query_params.get("export") == "csv":
            return export_customer_overview_csv(company, filters)

        data = get_customer_overview_report(company, filters)
        return Response(data)


@extend_schema(
    tags=["Reports"],
    description="Export Customer Overview report as CSV file.",
    parameters=COMMON_REPORT_PARAMS,
)
class CustomerOverviewExportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)
        return export_customer_overview_csv(company, filters)


@extend_schema(
    tags=["Reports"],
    description="Executive Summary report: roll-up KPIs across all 4 report domains.",
    parameters=COMMON_REPORT_PARAMS,
)
class ExecutiveSummaryReportView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company
        filters = _extract_filters(request)
        data = get_executive_summary(company, filters)
        return Response(data)
