"""Serializers for account security endpoints."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models_security import SecurityEvent
from apps.accounts.models_session import SessionDevice

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    token_id = serializers.UUIDField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class SessionDeviceSerializer(serializers.ModelSerializer):
    browser = serializers.CharField(read_only=True)
    device = serializers.CharField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = SessionDevice
        fields = [
            "id",
            "browser",
            "device",
            "ip_address",
            "created_at",
            "last_activity",
            "is_current",
        ]
        read_only_fields = fields


class SecurityEventSerializer(serializers.ModelSerializer):
    """Read-only shape of a single user security event."""

    class Meta:
        model = SecurityEvent
        fields = [
            "id",
            "event_type",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
