"""Serializers for team invitations."""

from rest_framework import serializers

from apps.companies.models import RoleChoices, TeamInvitation


class InvitationOutputSerializer(serializers.ModelSerializer):
    """Public shape of an invitation. The token hash is never exposed."""

    role = serializers.CharField()
    status = serializers.CharField()
    invited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamInvitation
        fields = [
            "id",
            "email",
            "role",
            "status",
            "invited_by",
            "invited_by_name",
            "created_at",
            "expires_at",
        ]
        read_only_fields = fields

    def get_invited_by_name(self, obj) -> str | None:
        if obj.invited_by is None:
            return None
        return obj.invited_by.get_full_name() or obj.invited_by.email


class InvitationCreateSerializer(serializers.Serializer):
    """Request body for inviting a member by email."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=RoleChoices.choices)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class InvitationAcceptExistingSerializer(serializers.Serializer):
    """Accept an invitation for an already-registered user (token only)."""

    token = serializers.CharField()

    def validate_token(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("A token is required.")
        return value


class InvitationRegisterAcceptSerializer(serializers.Serializer):
    """Accept an invitation by registering the invitee as a new user."""

    token = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_token(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("A token is required.")
        return value


class InvitationValidateSerializer(serializers.Serializer):
    """Public token pre-flight: is it valid, and which flow applies?"""

    token = serializers.CharField()
    email = serializers.EmailField(read_only=True)
    company_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    user_exists = serializers.BooleanField(read_only=True)
