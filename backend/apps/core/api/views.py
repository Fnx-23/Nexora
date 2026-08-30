"""Shared API views: tenant-scoped viewsets and operational endpoints."""

import redis as redis_lib
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.models import RoleChoices
from apps.core.api.permissions import IsCompanyMember, role_required


class TenantScopedModelViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet hard-scoped to the request's active company.

    * Reads are filtered to ``company=request.company``.
    * Writes are stamped with ``request.company`` on create.

    Requires ``IsCompanyMember`` (included by default) so ``request.company``
    is guaranteed to be resolved before any query executes. Destructive
    actions require MANAGER or ADMIN; extend per-viewset as domains mature.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        if self.queryset is None:
            raise ImproperlyConfigured(f"{type(self).__name__} must define a `queryset` attribute.")
        company = getattr(self.request, "company", None)
        if company is None:  # pragma: no cover - guarded by IsCompanyMember
            return self.queryset.none()
        return super().get_queryset().filter(company=company)

    def perform_create(self, serializer) -> None:
        serializer.save(company=self.request.company)

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action == "destroy":
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions


class TenantScopedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only counterpart of :class:`TenantScopedModelViewSet`.

    Exposes only ``list`` and ``retrieve``, both hard-scoped to
    ``company=request.company``. Suitable for resources that must never be
    mutated through the API (e.g. the append-only audit log), where write
    verbs should answer ``405 Method Not Allowed``.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        if self.queryset is None:
            raise ImproperlyConfigured(f"{type(self).__name__} must define a `queryset` attribute.")
        company = getattr(self.request, "company", None)
        if company is None:  # pragma: no cover - guarded by IsCompanyMember
            return self.queryset.none()
        return super().get_queryset().filter(company=company)


class HealthCheckView(APIView):
    """Liveness/readiness probe covering database and (optional) Redis."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT})
    def get(self, request):
        components = {
            "database": self._check_database(),
        }
        if settings.REDIS_URL:
            components["redis"] = self._check_redis(settings.REDIS_URL)

        healthy = all(component["healthy"] for component in components.values())
        return Response(
            {"status": "ok" if healthy else "unhealthy", "components": components},
            status=200 if healthy else 503,
        )

    @staticmethod
    def _check_database() -> dict[str, bool]:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return {"healthy": False}
        return {"healthy": True}

    @staticmethod
    def _check_redis(url: str) -> dict[str, bool]:
        try:
            client = redis_lib.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
            client.ping()
        except Exception:
            return {"healthy": False}
        return {"healthy": True}
