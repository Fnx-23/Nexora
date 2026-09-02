"""Serializers for companies and memberships."""

from rest_framework import serializers

from apps.companies.models import Company, Membership
from apps.companies.validators import validate_company_logo


class CompanySerializer(serializers.ModelSerializer):
    """
    Public shape of a company on the settings endpoint.

    ``is_active`` is intentionally read-only: activation is part of company
    lifecycle control (tenant resolver depends on it), so members — including
    admins — cannot deactivate their own workspace through this endpoint.

    ``timezone`` is validated against the IANA time zone database, and
    ``locale`` against the curated option list in ``COMPANY_LOCALES``.
    """

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "timezone",
            "locale",
            "logo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]

    def validate_timezone(self, value):
        if value is None:
            return value
        try:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            ZoneInfo(value)
        except (ZoneInfoNotFoundError, KeyError, ValueError):
            raise serializers.ValidationError("Invalid timezone.") from None
        return value

    def validate_logo(self, value):
        return validate_company_logo(value)


class MembershipSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "company", "role", "is_active", "created_at"]
