from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators, status
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.tasks.api.serializers import (
    TaskChecklistItemSerializer,
    TaskCommentSerializer,
    TaskDetailSerializer,
    TaskLabelSerializer,
    TaskSerializer,
    TaskSubtaskSerializer,
)
from apps.tasks.models import (
    Task,
    TaskChecklistItem,
    TaskComment,
    TaskLabel,
    TaskStatus,
    TaskSubtask,
)
from apps.tasks.services import annotate_task_queryset, recent_activity_for_task


@extend_schema_view(
    list=extend_schema(description="List tasks for the active company."),
    retrieve=extend_schema(description="Retrieve a single task with its activity feed."),
    create=extend_schema(description="Create a new task."),
    update=extend_schema(description="Update a task."),
    partial_update=extend_schema(description="Partially update a task."),
    destroy=extend_schema(description="Permanently delete a task."),
    change_status=extend_schema(description="Change a task's status."),
    comments=extend_schema(description="List or add comments to a task."),
    comment_detail=extend_schema(
        description="Edit or delete a single task comment (author or MANAGER/ADMIN)."
    ),
    checklist=extend_schema(description="List or add checklist items to a task."),
    checklist_item=extend_schema(description="Edit or delete a single checklist item."),
    subtasks=extend_schema(description="List or add subtasks to a task."),
    subtask_detail=extend_schema(description="Edit or delete a single subtask."),
)
class TaskViewSet(TenantScopedModelViewSet):
    """CRUD + status change + nested comments/checklist/subtasks for tasks."""

    queryset = Task.objects.select_related("project", "assignee", "created_by")
    serializer_class = TaskSerializer
    filterset_fields = ["status", "priority", "project", "assignee"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "status", "priority", "due_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.prefetch_related("labels")
        qs = annotate_task_queryset(qs)
        label_id = self.request.query_params.get("label")
        if label_id:
            qs = qs.filter(labels__id=label_id)
        return qs

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

    def retrieve(self, request, pk=None):
        task = self.get_object()
        task._recent_activity = recent_activity_for_task(task)
        serializer = TaskDetailSerializer(task, context=self.get_serializer_context())
        return Response(serializer.data)

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

    @decorators.action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        """List a task's comments (oldest first) or add a new one."""
        task = self.get_object()
        if request.method == "GET":
            rows = list(task.comments.select_related("author").all())
            serializer = TaskCommentSerializer(
                rows, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        serializer = TaskCommentSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(
            task=task,
            author=request.user,
            company=request.company,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"comments/(?P<comment_id>[^/.]+)",
    )
    def comment_detail(self, request, pk=None, comment_id=None):
        """Edit (patch) or delete a comment. Author or MANAGER/ADMIN only."""
        task = self.get_object()
        try:
            comment = task.comments.get(pk=comment_id)
        except TaskComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found on this task."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_author = comment.author_id == request.user.id
        is_manager = request.company_role in (RoleChoices.MANAGER, RoleChoices.ADMIN)
        if not (is_author or is_manager):
            return Response(
                {"detail": "Only the author or a manager can edit this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "DELETE":
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = TaskCommentSerializer(
            comment, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["get", "post"], url_path="checklist")
    def checklist(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            rows = list(task.checklist_items.all())
            serializer = TaskChecklistItemSerializer(
                rows, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        data = request.data.copy()
        if "position" not in data:
            last = (
                task.checklist_items.order_by("-position")
                .values_list("position", flat=True)
                .first()
            )
            data["position"] = (last + 1) if last is not None else 0
        serializer = TaskChecklistItemSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, company=request.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"checklist/(?P<item_id>[^/.]+)",
    )
    def checklist_item(self, request, pk=None, item_id=None):
        """Toggle completion (patch) or delete a single checklist item."""
        task = self.get_object()
        try:
            item = task.checklist_items.get(pk=item_id)
        except TaskChecklistItem.DoesNotExist:
            return Response(
                {"detail": "Checklist item not found on this task."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = TaskChecklistItemSerializer(
            item, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["get", "post"], url_path="subtasks")
    def subtasks(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            rows = list(task.subtasks.all())
            serializer = TaskSubtaskSerializer(
                rows, many=True, context=self.get_serializer_context()
            )
            return Response(serializer.data)

        data = request.data.copy()
        if "position" not in data:
            last = task.subtasks.order_by("-position").values_list("position", flat=True).first()
            data["position"] = (last + 1) if last is not None else 0
        serializer = TaskSubtaskSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, company=request.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"subtasks/(?P<subtask_id>[^/.]+)",
    )
    def subtask_detail(self, request, pk=None, subtask_id=None):
        """Toggle completion (patch) or delete a single subtask."""
        task = self.get_object()
        try:
            item = task.subtasks.get(pk=subtask_id)
        except TaskSubtask.DoesNotExist:
            return Response(
                {"detail": "Subtask not found on this task."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = TaskSubtaskSerializer(
            item, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List task labels for the active company."),
    create=extend_schema(description="Create a task label."),
    update=extend_schema(description="Update a task label."),
    partial_update=extend_schema(description="Partially update a task label."),
    destroy=extend_schema(description="Delete a task label."),
)
class TaskLabelViewSet(TenantScopedModelViewSet):
    """Company-scoped labels. Writes are MANAGER/ADMIN-only."""

    queryset = TaskLabel.objects.all()
    serializer_class = TaskLabelSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ("create", "update", "partial_update", "destroy"):
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions
