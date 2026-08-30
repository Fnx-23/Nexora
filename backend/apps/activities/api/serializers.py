from rest_framework import serializers

from apps.activities.models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    """Read-only representation of an audit-log entry.

    Every field is read-only: the audit log is append-only and is never written
    through the API (records are produced by model signals). ``actor_name`` and
    ``action_display`` are convenience fields for the UI.
    """

    actor_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "action",
            "action_display",
            "entity_type",
            "entity_id",
            "actor",
            "actor_name",
            "metadata",
            "timestamp",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj) -> str | None:
        if obj.actor is None:
            return None
        return obj.actor.get_full_name() or obj.actor.email
