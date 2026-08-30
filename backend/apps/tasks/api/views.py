from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators, status
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.tasks.api.serializers import TaskSerializer
from apps.tasks.models import Task, TaskStatus


@extend_schema_view(
    list=extend_schema(description="List tasks for the active company."),
    retrieve=extend_schema(description="Retrieve a single task."),
    create=extend_schema(description="Create a new task."),
    update=extend_schema(description="Update a task."),
    partial_update=extend_schema(description="Partially update a task."),
    destroy=extend_schema(description="Permanently delete a task."),
    change_status=extend_schema(description="Change a task's status."),
)
class TaskViewSet(TenantScopedModelViewSet):
    """CRUD + status change for the active company's tasks."""

    queryset = Task.objects.select_related("project", "assignee", "created_by")
    serializer_class = TaskSerializer
    filterset_fields = ["status", "priority", "project", "assignee"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "status", "priority", "due_date", "created_at"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action == "destroy":
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.company,
            created_by=self.request.user,
        )

    @decorators.action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        """Change a task's status. Employees can only move their own tasks."""
        task = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"detail": "status field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        allowed = {c for c, _ in TaskStatus.choices}
        if new_status not in allowed:
            return Response(
                {"detail": f"Invalid status. Choose from: {', '.join(sorted(allowed))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            request.company_role == RoleChoices.EMPLOYEE
            and task.assignee_id != request.user.id
            and task.created_by_id != request.user.id
        ):
            return Response(
                {"detail": "Employees can only change status of their own tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])
        return Response(TaskSerializer(task).data)
