"""Viewset for document management: upload, list, download, rename, delete."""

from __future__ import annotations

import logging
import os

from django.http import FileResponse, Http404
from rest_framework import decorators, parsers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import IsCompanyMember, role_required
from apps.documents.api.serializers import (
    DocumentRenameSerializer,
    DocumentSerializer,
)
from apps.documents.models import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    Document,
    EntityKind,
    _sanitize_filename,
)

logger = logging.getLogger("apps.documents")


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
    ]
    parser_classes = [
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    ]
    search_fields = ["original_filename"]
    ordering_fields = ["original_filename", "size", "created_at"]

    def get_queryset(self):
        qs = Document.objects.select_related("uploaded_by")
        company = getattr(self.request, "company", None)
        if company is None:
            return qs.none()
        qs = qs.filter(company=company)

        entity_kind = self.request.query_params.get("entity_kind")
        entity_id = self.request.query_params.get("entity_id")
        if entity_kind:
            qs = qs.filter(entity_kind=entity_kind)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        return qs

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action == "destroy":
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Security: file size ---
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            return Response(
                {"detail": f"File exceeds maximum size of {max_mb} MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Security: MIME type ---
        content_type = uploaded_file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            return Response(
                {"detail": f"File type '{content_type}' is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Security: extension ---
        _, ext = os.path.splitext(uploaded_file.name)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return Response(
                {"detail": f"File extension '{ext}' is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Security: sanitize filename ---
        safe_name = _sanitize_filename(uploaded_file.name)

        entity_kind = request.data.get("entity_kind", EntityKind.COMPANY)
        entity_id = request.data.get("entity_id") or None

        if entity_kind not in dict(EntityKind.choices):
            return Response(
                {"detail": f"Invalid entity_kind: '{entity_kind}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc = Document(
            company=request.company,
            original_filename=safe_name,
            mime_type=content_type,
            size=uploaded_file.size,
            entity_kind=entity_kind,
            entity_id=entity_id,
            uploaded_by=request.user,
        )
        doc.file = uploaded_file
        doc.save()

        return Response(
            DocumentSerializer(doc, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        doc = self.get_object()
        if not doc.file:
            raise Http404("File not found.")
        ct = doc.mime_type or "application/octet-stream"
        response = FileResponse(doc.file.open("rb"), content_type=ct)
        fn = doc.original_filename
        response["Content-Disposition"] = f'attachment; filename="{fn}"'
        return response

    @decorators.action(detail=True, methods=["patch"], url_path="rename")
    def rename(self, request, pk=None):
        doc = self.get_object()
        serializer = DocumentRenameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_name = _sanitize_filename(
            serializer.validated_data["filename"],
        )
        if not new_name:
            return Response(
                {"detail": "Invalid filename."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc.original_filename = new_name
        doc.save(update_fields=["original_filename", "updated_at"])
        return Response(
            DocumentSerializer(doc, context={"request": request}).data,
        )
