from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators, status
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.projects.api.serializers import ProjectSerializer
from apps.projects.models import Project, ProjectStatus


@extend_schema_view(
    list=extend_schema(description="List projects for the active company."),
    retrieve=extend_schema(description="Retrieve a single project."),
    create=extend_schema(description="Create a new project."),
    update=extend_schema(description="Update a project."),
    partial_update=extend_schema(description="Partially update a project."),
    destroy=extend_schema(description="Permanently delete a project."),
    archive=extend_schema(description="Soft-archive a project (sets status to ARCHIVED)."),
)
class ProjectViewSet(TenantScopedModelViewSet):
    """CRUD + archive for the active company's projects."""

    queryset = Project.objects.select_related("customer", "manager")
    serializer_class = ProjectSerializer
    filterset_fields = ["status", "priority", "customer"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "status", "priority", "created_at", "deadline"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ("destroy", "archive"):
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    @decorators.action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Set project status to ARCHIVED."""
        project = self.get_object()
        if project.status == ProjectStatus.ARCHIVED:
            return Response(
                {"detail": "Project is already archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project.status = ProjectStatus.ARCHIVED
        project.save(update_fields=["status", "updated_at"])
        return Response(ProjectSerializer(project).data)
