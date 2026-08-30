from django.contrib import admin

from apps.activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Read-only admin view of the audit log — records are never edited."""

    list_display = ["timestamp", "company", "action", "entity_type", "entity_id", "actor"]
    list_filter = ["action", "entity_type"]
    search_fields = ["entity_id", "actor__email"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
