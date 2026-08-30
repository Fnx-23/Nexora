from rest_framework import serializers

from apps.customers.models import Customer, CustomerStatus


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "company_name",
            "email",
            "phone",
            "address",
            "notes",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_status(self, value):
        allowed = {choice for choice, _label in CustomerStatus.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status.")
        return value
