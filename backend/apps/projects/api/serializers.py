from rest_framework import serializers

from apps.projects.models import Project, ProjectPriority, ProjectStatus


class ProjectSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
        default=None,
    )
    manager_name = serializers.SerializerMethodField()

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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
            from apps.companies.models import Membership

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
