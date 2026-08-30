"""Serializers for the notifications API."""

from rest_framework import serializers

from apps.notifications.models import Notification


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
            "actor_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor is None:
            return "System"
        return obj.actor.get_full_name() or obj.actor.email
