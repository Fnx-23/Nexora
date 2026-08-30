"""Serializers for companies and memberships."""

from rest_framework import serializers

from apps.companies.models import Company, Membership


class CompanySerializer(serializers.ModelSerializer):
    """
    Public shape of a company on the settings endpoint.

    ``is_active`` is intentionally read-only: activation is part of company
    lifecycle control (tenant resolver depends on it), so members — including
    admins — cannot deactivate their own workspace through this endpoint.
    """

    class Meta:
        model = Company
        fields = ["id", "name", "slug", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]


class MembershipSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "company", "role", "is_active", "created_at"]
