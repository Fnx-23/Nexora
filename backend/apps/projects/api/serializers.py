from rest_framework import serializers

from apps.activities.api.serializers import ActivitySerializer
from apps.companies.models import Membership
from apps.projects.models import Project, ProjectMember, ProjectPriority, ProjectStatus
from apps.projects.services import metrics_from_annotated


class ProjectSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
        default=None,
    )
    manager_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    overdue_count = serializers.SerializerMethodField()
    tracked_hours = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "customer",
            "customer_name",
            "manager",
            "manager_name",
            "status",
            "priority",
            "start_date",
            "deadline",
            "progress",
            "health",
            "task_count",
            "overdue_count",
            "tracked_hours",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_metrics(self, obj) -> object | None:
        metrics = getattr(obj, "_metrics", None)
        if metrics is None:
            metrics = metrics_from_annotated(obj, None)
            obj._metrics = metrics
        return metrics

    def get_progress(self, obj) -> int:
        return self.get_metrics(obj).progress

    def get_health(self, obj) -> str:
        return self.get_metrics(obj).health

    def get_task_count(self, obj) -> int:
        return self.get_metrics(obj).task_count

    def get_overdue_count(self, obj) -> int:
        return self.get_metrics(obj).overdue_count

    def get_tracked_hours(self, obj) -> float:
        return self.get_metrics(obj).tracked_hours

    def get_member_count(self, obj) -> int:
        count = getattr(obj, "_member_count", None)
        if count is not None:
            return count
        return obj.members.count()

    def get_manager_name(self, obj):
        if obj.manager is None:
            return None
        return obj.manager.get_full_name() or obj.manager.email

    def validate_customer(self, value):
        if value is not None and value.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Customer belongs to another company.")
        return value

    def validate_manager(self, value):
        if value is not None:
            company = self.context["request"].company
            if not Membership.objects.filter(
                company=company,
                user=value,
                is_active=True,
            ).exists():
                raise serializers.ValidationError(
                    "Manager must be a member of this company.",
                )
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        deadline = attrs.get("deadline")
        if self.instance is not None and "start_date" not in attrs and "deadline" not in attrs:
            return attrs
        start_date = start_date or (self.instance.start_date if self.instance else None)
        deadline = deadline or (self.instance.deadline if self.instance else None)
        if start_date and deadline and deadline < start_date:
            raise serializers.ValidationError({"deadline": "Must not be before start date."})
        return attrs

    def validate_status(self, value):
        allowed = {choice for choice, _label in ProjectStatus.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate_priority(self, value):
        allowed = {choice for choice, _label in ProjectPriority.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid priority.")
        return value


class ProjectDetailSerializer(ProjectSerializer):
    """Rich project representation for the details workspace.

    Extends :class:`ProjectSerializer` with task breakdown, member roster and
    recent project-specific activity. The view is responsible for prefetching
    ``members__user`` and attaching ``recent_activity`` so no extra queries run
    here.
    """

    done_count = serializers.SerializerMethodField()
    in_progress_count = serializers.SerializerMethodField()
    todo_count = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "customer",
            "customer_name",
            "manager",
            "manager_name",
            "status",
            "priority",
            "start_date",
            "deadline",
            "progress",
            "health",
            "task_count",
            "done_count",
            "in_progress_count",
            "todo_count",
            "overdue_count",
            "tracked_hours",
            "member_count",
            "members",
            "recent_activity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_done_count(self, obj) -> int:
        return self.get_metrics(obj).done_count

    def get_in_progress_count(self, obj) -> int:
        return self.get_metrics(obj).in_progress_count

    def get_todo_count(self, obj) -> int:
        return self.get_metrics(obj).todo_count

    def get_members(self, obj):
        members = getattr(obj, "_members", None)
        if members is None:
            members = list(obj.members.select_related("user").all())
        return ProjectMemberSerializer(members, many=True, context=self.context).data

    def get_recent_activity(self, obj):
        activities = getattr(obj, "_recent_activity", None)
        if activities is None:
            from apps.projects.services import recent_activity_for_project

            activities = recent_activity_for_project(obj)
        return ActivitySerializer(activities, many=True, context=self.context).data


class ProjectMemberSerializer(serializers.ModelSerializer):
    """A company user assigned to a project.

    Assignment is tenant-isolated: the ``user`` must hold an active membership
    in the same company as the project. Cross-tenant assignment is rejected here
    (defense in depth beyond the DB constraint).
    """

    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "email",
            "full_name",
            "avatar",
            "created_at",
        ]
        read_only_fields = ["id", "project", "created_at"]

    def get_full_name(self, obj) -> str:
        name = obj.user.get_full_name()
        return name if name else obj.user.email

    def get_avatar(self, obj) -> str | None:
        if not obj.user.avatar:
            return None
        try:
            return obj.user.avatar.url
        except ValueError:  # pragma: no cover - file not resolvable
            return None

    def validate_user(self, value):
        company = self.context["request"].company
        is_member = Membership.objects.filter(
            user=value,
            company=company,
            is_active=True,
        ).exists()
        if not is_member:
            raise serializers.ValidationError(
                "User must be an active member of this company.",
            )
        return value

    def validate(self, attrs):
        project = self.context.get("project")
        user = attrs.get("user")
        if (
            project is not None
            and user is not None
            and ProjectMember.objects.filter(project=project, user=user).exists()
        ):
            raise serializers.ValidationError(
                {"user": "This user is already a member of the project."}
            )
        return attrs
