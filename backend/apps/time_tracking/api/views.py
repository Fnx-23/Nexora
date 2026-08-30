from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.time_tracking.api.serializers import TimeEntrySerializer
from apps.time_tracking.models import TimeEntry


@extend_schema_view(
    list=extend_schema(description="List time entries for the active company."),
    retrieve=extend_schema(description="Retrieve a single time entry."),
    create=extend_schema(description="Log a new time entry."),
    update=extend_schema(description="Update a time entry."),
    partial_update=extend_schema(description="Partially update a time entry."),
    destroy=extend_schema(description="Delete a time entry."),
    summary=extend_schema(description="Aggregated time tracking summary."),
)
class TimeEntryViewSet(TenantScopedModelViewSet):
    """CRUD + summary for the active company's time entries."""

    queryset = TimeEntry.objects.select_related("project", "task", "user")
    serializer_class = TimeEntrySerializer
    filterset_fields = ["project", "user", "date", "task"]
    search_fields = ["description"]
    ordering_fields = ["date", "start_time", "duration", "created_at"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action == "destroy":
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        company_role = getattr(self.request, "company_role", None)

        # Employees can only see their own entries
        if company_role == RoleChoices.EMPLOYEE:
            qs = qs.filter(user=user)

        # Date range filtering
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.company,
            user=self.request.user,
        )

    @decorators.action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Return aggregated time tracking data for the active company."""
        qs = self.get_queryset()

        total_entries = qs.count()

        duration_agg = qs.aggregate(total=Coalesce(Sum("duration"), timedelta(0)))
        total_seconds = duration_agg["total"].total_seconds() if duration_agg["total"] else 0
        total_minutes = round(total_seconds / 60, 2)

        # By project
        by_project = (
            qs.values("project__name")
            .annotate(total=Coalesce(Sum("duration"), timedelta(0)))
            .order_by("-total")
        )
        by_project_list = [
            {
                "project_name": item["project__name"] or "No project",
                "total_minutes": round(item["total"].total_seconds() / 60, 2)
                if item["total"]
                else 0,
            }
            for item in by_project
        ]

        # By date
        by_date = (
            qs.values("date")
            .annotate(total=Coalesce(Sum("duration"), timedelta(0)))
            .order_by("-date")
        )
        by_date_list = [
            {
                "date": item["date"].isoformat(),
                "total_minutes": round(item["total"].total_seconds() / 60, 2)
                if item["total"]
                else 0,
            }
            for item in by_date
        ]

        return Response(
            {
                "total_entries": total_entries,
                "total_duration_minutes": total_minutes,
                "by_project": by_project_list,
                "by_date": by_date_list,
            }
        )
