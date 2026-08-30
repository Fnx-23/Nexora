from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.activities.api.serializers import ActivitySerializer
from apps.activities.models import Activity
from apps.core.api.views import TenantScopedReadOnlyModelViewSet


@extend_schema_view(
    list=extend_schema(description="List audit-log activities for the active company."),
    retrieve=extend_schema(description="Retrieve a single activity record."),
)
class ActivityViewSet(TenantScopedReadOnlyModelViewSet):
    """Read-only, tenant-scoped access to the company's audit log.

    Available to every company member. Write verbs are intentionally absent —
    the log is append-only and produced by signals — so POST/PUT/PATCH/DELETE
    all answer ``405 Method Not Allowed``.
    """

    queryset = Activity.objects.select_related("actor")
    serializer_class = ActivitySerializer
    filterset_fields = ["action", "entity_type", "entity_id", "actor"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]
