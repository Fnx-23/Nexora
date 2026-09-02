from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators, status
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.projects.api.serializers import (
    ProjectDetailSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
)
from apps.projects.models import Project, ProjectMember, ProjectStatus
from apps.projects.services import annotate_project_queryset, recent_activity_for_project


@extend_schema_view(
    list=extend_schema(description="List projects for the active company."),
    retrieve=extend_schema(description="Retrieve a single project with full metrics."),
    create=extend_schema(description="Create a new project."),
    update=extend_schema(description="Update a project."),
    partial_update=extend_schema(description="Partially update a project."),
    destroy=extend_schema(description="Permanently delete a project."),
    archive=extend_schema(description="Soft-archive a project (sets status to ARCHIVED)."),
    restore=extend_schema(description="Restore an archived project to its previous status."),
)
class ProjectViewSet(TenantScopedModelViewSet):
    """CRUD + archive/restore + members for the active company's projects."""

    queryset = Project.objects.select_related("customer", "manager")
    serializer_class = ProjectSerializer
    filterset_fields = ["status", "priority", "customer"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "status", "priority", "created_at", "deadline"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("retrieve", "members"):
            qs = qs.prefetch_related("members__user")
        return annotate_project_queryset(qs)

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ("destroy", "archive", "restore"):
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        if self.action == "members" and self.request.method != "GET":
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    def retrieve(self, request, pk=None):
        project = self.get_object()
        project._recent_activity = recent_activity_for_project(project)
        serializer = ProjectDetailSerializer(project, context=self.get_serializer_context())
        return Response(serializer.data)

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

    @decorators.action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restore an archived project back to an active status.

        The previous pre-archive status is not persisted, so restoration lands
        on ``PLANNING`` unless the caller specifies a target status.
        """
        project = self.get_object()
        if project.status != ProjectStatus.ARCHIVED:
            return Response(
                {"detail": "Only archived projects can be restored."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target = request.data.get("status")
        if target is None:
            target = ProjectStatus.PLANNING
        allowed = {c for c, _label in ProjectStatus.choices}
        if target not in allowed or target == ProjectStatus.ARCHIVED:
            return Response(
                {"detail": "Invalid restoration status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project.status = target
        project.save(update_fields=["status", "updated_at"])
        return Response(ProjectSerializer(project).data)

    @decorators.action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            rows = list(project.members.select_related("user").all())
            serializer = ProjectMemberSerializer(
                rows, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        serializer = ProjectMemberSerializer(
            data=request.data,
            context={**self.get_serializer_context(), "project": project},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project, company=request.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def member_remove(self, request, pk=None, member_id=None):
        """Remove a member from a project."""
        project = self.get_object()
        deleted, _ = ProjectMember.objects.filter(
            project=project,
            id=member_id,
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Member not found on this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
