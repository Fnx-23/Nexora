"""Document model for file management with tenant isolation."""

from __future__ import annotations

import os
import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.db.models import TenantedModel

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "text/plain",
    "text/csv",
    "application/zip",
    "application/x-zip-compressed",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".txt",
    ".csv",
    ".zip",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _sanitize_filename(filename: str) -> str:
    """Strip path components and dangerous characters."""
    filename = os.path.basename(filename)
    filename = filename.replace("\x00", "")
    filename = filename.lstrip(". ")
    for ch in ("/", "\\", "..", "~"):
        filename = filename.replace(ch, "_")
    return filename or "unnamed"


def document_upload_path(
    instance: Document,
    filename: str,
) -> str:
    """Generate a safe, UUID-based storage path."""
    safe_name = _sanitize_filename(filename)
    ext = os.path.splitext(safe_name)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"documents/{instance.company_id}/{unique_name}"


class EntityKind(models.TextChoices):
    COMPANY = "COMPANY", "Company"
    PROJECT = "PROJECT", "Project"
    CUSTOMER = "CUSTOMER", "Customer"
    TASK = "TASK", "Task"


class Document(TenantedModel):
    """A file uploaded by a user, scoped to a company."""

    file = models.FileField(
        upload_to=document_upload_path,
        max_length=500,
        validators=[
            FileExtensionValidator(
                allowed_extensions=sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS),
            ),
        ],
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(
        max_length=127,
        blank=True,
        default="",
    )
    size = models.PositiveBigIntegerField(
        help_text="File size in bytes.",
    )
    entity_kind = models.CharField(
        max_length=20,
        choices=EntityKind.choices,
        default=EntityKind.COMPANY,
    )
    entity_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="PK of linked project or customer.",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["company", "entity_kind", "entity_id"],
            ),
            models.Index(
                fields=["company", "-created_at"],
            ),
        ]

    def __str__(self) -> str:
        return self.original_filename
