from rest_framework import serializers

from apps.companies.models import Membership
from apps.tasks.models import Task, TaskPriority, TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        default=None,
    )

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_assignee_name(self, obj):
        if obj.assignee is None:
            return None
        name = obj.assignee.get_full_name()
        return name if name else obj.assignee.email

    def get_created_by_name(self, obj):
        if obj.created_by is None:
            return None
        name = obj.created_by.get_full_name()
        return name if name else obj.created_by.email

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
