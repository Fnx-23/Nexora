"""
Server-side validation for uploaded company logos.

Logos are brand assets: they must be real raster images so they render
reliably and cannot smuggle active content (SVG) into the workspace.
The checks mirror the avatar defense layers:

1. Size limit from configuration (``AVATAR_MAX_SIZE_MB``).
2. Extension allowlist on the uploaded name.
3. Content sniffing via Pillow — the real format is derived from magic
   bytes, never from the client-provided Content-Type or the filename.

The validator raises Django's ``ValidationError`` so a single implementation
guards every write surface (DRF serializer validation here).
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

ALLOWED_LOGO_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def validate_company_logo(uploaded):
    """Return the upload unchanged when valid; raise ValidationError otherwise."""
    if uploaded is None:
        return None

    if uploaded.size > int(settings.AVATAR_MAX_SIZE_MB) * 1024 * 1024:
        raise ValidationError(
            _("Logo must not exceed %(limit)s MB.") % {"limit": settings.AVATAR_MAX_SIZE_MB}
        )

    extension = os.path.splitext(uploaded.name or "")[1].lower()
    if extension not in ALLOWED_LOGO_EXTENSIONS:
        raise ValidationError(_("Logo must be a JPEG, PNG or WebP image."))

    try:
        image_format: str | None
        with Image.open(uploaded) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(_("Uploaded file is not a valid image.")) from None

    if image_format not in ("JPEG", "PNG", "WEBP"):
        raise ValidationError(_("Only JPEG, PNG and WebP images are allowed."))

    uploaded.seek(0)
    return uploaded
