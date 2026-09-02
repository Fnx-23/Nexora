from rest_framework import serializers

from apps.activities.api.serializers import ActivitySerializer
from apps.companies.models import Membership
from apps.tasks.models import (
    Task,
    TaskChecklistItem,
    TaskComment,
    TaskLabel,
    TaskPriority,
    TaskStatus,
    TaskSubtask,
)


def _display_name(user) -> str | None:
    if user is None:
        return None
    return user.get_full_name() or user.email


class TaskLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLabel
        fields = ["id", "name", "color", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        queryset = TaskLabel.objects.filter(
            company=self.context["request"].company,
            name__iexact=value,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "A label with this name already exists in your company.",
            )
        return value


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "author_name", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "task", "author", "author_name", "created_at", "updated_at"]

    def get_author_name(self, obj):
        return _display_name(obj.author)


class TaskChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChecklistItem
        fields = ["id", "task", "text", "completed", "position", "created_at"]
        read_only_fields = ["id", "task", "created_at"]
        extra_kwargs = {"text": {"trim_whitespace": True, "max_length": 255}}


class TaskSubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubtask
        fields = ["id", "task", "title", "completed", "position", "created_at"]
        read_only_fields = ["id", "task", "created_at"]
        extra_kwargs = {"title": {"trim_whitespace": True, "max_length": 200}}


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        default=None,
    )
    labels = TaskLabelSerializer(many=True, read_only=True, required=False)
    label_ids = serializers.PrimaryKeyRelatedField(
        source="labels",
        queryset=TaskLabel.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )
    checklist_total = serializers.SerializerMethodField()
    checklist_done = serializers.SerializerMethodField()
    subtask_total = serializers.SerializerMethodField()
    subtask_done = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "project",
            "project_name",
            "status",
            "priority",
            "assignee",
            "assignee_name",
            "created_by",
            "created_by_name",
            "due_date",
            "labels",
            "label_ids",
            "checklist_total",
            "checklist_done",
            "subtask_total",
            "subtask_done",
            "comments_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_assignee_name(self, obj):
        return _display_name(obj.assignee)

    def get_created_by_name(self, obj):
        return _display_name(obj.created_by)

    def get_checklist_total(self, obj) -> int:
        count = getattr(obj, "_checklist_total", None)
        return count if count is not None else obj.checklist_items.count()

    def get_checklist_done(self, obj) -> int:
        count = getattr(obj, "_checklist_done", None)
        if count is not None:
            return count
        return obj.checklist_items.filter(completed=True).count()

    def get_subtask_total(self, obj) -> int:
        count = getattr(obj, "_subtask_total", None)
        return count if count is not None else obj.subtasks.count()

    def get_subtask_done(self, obj) -> int:
        count = getattr(obj, "_subtask_done", None)
        if count is not None:
            return count
        return obj.subtasks.filter(completed=True).count()

    def get_comments_count(self, obj) -> int:
        count = getattr(obj, "_comments_count", None)
        return count if count is not None else obj.comments.count()

    def validate_project(self, value):
        if value is not None and value.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Project belongs to another company.")
        return value

    def validate_assignee(self, value):
        if value is None:
            return value
        company = self.context["request"].company
        is_member = Membership.objects.filter(
            user=value,
            company=company,
            is_active=True,
        ).exists()
        if not is_member:
            raise serializers.ValidationError(
                "Assignee must be a member of this company.",
            )
        return value

    def validate_label_ids(self, value):
        company = self.context["request"].company
        ids = [label.id for label in value]
        if not ids:
            return value
        match_count = TaskLabel.objects.filter(company=company, id__in=ids).count()
        if match_count != len(ids):
            raise serializers.ValidationError(
                "One or more labels belong to another company.",
            )
        return value

    def validate_status(self, value):
        allowed = {c for c, _ in TaskStatus.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate_priority(self, value):
        allowed = {c for c, _ in TaskPriority.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid priority.")
        return value


class TaskDetailSerializer(TaskSerializer):
    """Rich task representation for the task-details workspace.

    Extends :class:`TaskSerializer` with the recent task-scoped activity feed.
    The view attaches ``recent_activity`` (or lazily fetches it) and is expected
    to prefetch ``labels`` on the queryset so no extra queries run here.
    """

    recent_activity = serializers.SerializerMethodField()

    class Meta(TaskSerializer.Meta):
        fields = [*TaskSerializer.Meta.fields, "recent_activity"]

    def get_recent_activity(self, obj):
        activities = getattr(obj, "_recent_activity", None)
        if activities is None:
            from apps.tasks.services import recent_activity_for_task

            activities = recent_activity_for_task(obj)
        return ActivitySerializer(activities, many=True, context=self.context).data
