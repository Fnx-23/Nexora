"""Serializers for the notifications API."""

from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "verb",
            "entity_type",
            "entity_id",
            "entity_name",
            "link",
            "is_read",
            "category",
            "actor_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor is None:
            return "System"
        return obj.actor.get_full_name() or obj.actor.email


PREFERENCE_FIELDS = [
    "id",
    "task_assigned",
    "task_due_soon",
    "task_overdue",
    "task_comment",
    "project_assigned",
    "project_deadline",
    "invitation_received",
    "role_changed",
    "email_task_assigned",
    "email_task_due_soon",
    "email_task_overdue",
    "email_task_comment",
    "email_project_assigned",
    "email_project_deadline",
    "email_invitation_received",
    "email_role_changed",
]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = PREFERENCE_FIELDS
        read_only_fields = ["id"]
