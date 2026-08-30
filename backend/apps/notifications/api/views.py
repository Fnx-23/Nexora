"""Viewset for listing, reading, and managing notifications."""

from rest_framework import decorators, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import IsCompanyMember
from apps.notifications.api.serializers import NotificationSerializer
from apps.notifications.models import Notification


class NotificationViewSet(viewsets.ModelViewSet):
    """Notifications are read-only for the recipient; admins/managers can also view all."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    http_method_names = ["get", "patch", "head", "options"]
    search_fields = ["verb", "entity_name"]
    ordering_fields = ["created_at", "is_read"]

    def get_queryset(self):
        qs = Notification.objects.select_related("actor")
        company = getattr(self.request, "company", None)
        if company is None:
            return qs.none()
        qs = qs.filter(company=company)

        user = self.request.user
        company_role = getattr(self.request, "company_role", None)
        if company_role not in (RoleChoices.ADMIN, RoleChoices.MANAGER):
            qs = qs.filter(recipient=user)

        unread_only = self.request.query_params.get("unread")
        if unread_only in ("true", "1"):
            qs = qs.filter(is_read=False)

        return qs

    @decorators.action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        qs = self.get_queryset().filter(is_read=False)
        return Response({"count": qs.count()})

    @decorators.action(detail=True, methods=["patch"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)

    @decorators.action(detail=False, methods=["patch"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})
