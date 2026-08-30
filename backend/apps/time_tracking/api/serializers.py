from rest_framework import serializers

from apps.companies.models import Membership
from apps.time_tracking.models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        default=None,
    )
    task_title = serializers.CharField(
        source="task.title",
        read_only=True,
        default=None,
    )

    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "user",
            "user_name",
            "project",
            "project_name",
            "task",
            "task_title",
            "date",
            "start_time",
            "end_time",
            "duration",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "duration", "created_at", "updated_at"]

    def get_user_name(self, obj):
        name = obj.user.get_full_name()
        return name if name else obj.user.email

    def validate_project(self, value):
        if value.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Project belongs to another company.")
        return value

    def validate_task(self, value):
        if value is None:
            return value
        company = self.context["request"].company
        if value.company_id != company.id:
            raise serializers.ValidationError("Task belongs to another company.")
        project = self.initial_data.get("project")
        if project and value.project_id and str(value.project_id) != str(project):
            raise serializers.ValidationError("Task must belong to the selected project.")
        return value

    def validate_user(self, value):
        company = self.context["request"].company
        is_member = Membership.objects.filter(
            user=value,
            company=company,
            is_active=True,
        ).exists()
        if not is_member:
            raise serializers.ValidationError("User must be a member of this company.")
        return value

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        if end_time and start_time and end_time < start_time:
            raise serializers.ValidationError(
                {"end_time": "End time cannot precede start time."},
            )
        return attrs


class TimeEntrySummarySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    project = serializers.UUIDField(required=False)
    user = serializers.UUIDField(required=False)


class TimeEntrySummaryResponseSerializer(serializers.Serializer):
    total_entries = serializers.IntegerField()
    total_duration_minutes = serializers.FloatField()
    by_project = serializers.ListField(child=serializers.DictField())
    by_date = serializers.ListField(child=serializers.DictField())
