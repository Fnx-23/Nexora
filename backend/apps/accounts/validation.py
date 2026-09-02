"""
Server-side validation for uploaded avatars.

Defense layers, in order:

1. Size limit from configuration (``AVATAR_MAX_SIZE_MB``).
2. Extension allowlist on the uploaded name.
3. Content sniffing via Pillow — the real format is derived from magic
   bytes, never from the client-provided Content-Type or the filename.

Only safe raster formats are accepted (JPEG / PNG / WebP). SVG, HTML,
executables and arbitrary binaries are rejected because they either carry
active content or serve no avatar purpose. The file position is always
rewound before returning so Django storage reads the full payload.

The validator raises Django's ``ValidationError`` so a single implementation
can guard every write surface: DRF serializers convert Django validation
errors into 400 responses automatically, and Django ``ModelForm`` / admin
``clean`` methods consume them natively. One definition of "a valid avatar".
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

ALLOWED_AVATAR_FORMATS: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}
ALLOWED_AVATAR_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def _max_avatar_bytes() -> int:
    return int(settings.AVATAR_MAX_SIZE_MB) * 1024 * 1024


def validate_avatar_image(uploaded):
    """Return the upload unchanged when valid; raise ValidationError otherwise."""
    if uploaded is None:
        return None

    if uploaded.size > _max_avatar_bytes():
        raise ValidationError(
            _("Avatar must not exceed %(limit)s MB.") % {"limit": settings.AVATAR_MAX_SIZE_MB}
        )

    extension = os.path.splitext(uploaded.name or "")[1].lower()
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError(_("Avatar must be a JPEG, PNG or WebP image."))

    try:
        image_format: str | None
        with Image.open(uploaded) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(_("Uploaded file is not a valid image.")) from None

    if image_format not in ALLOWED_AVATAR_FORMATS:
        raise ValidationError(_("Only JPEG, PNG and WebP images are allowed."))

    acceptable = {ALLOWED_AVATAR_FORMATS[image_format]}
    if image_format == "JPEG":
        acceptable.add(".jpeg")
    if extension not in acceptable:
        raise ValidationError(_("File content does not match its extension."))

    uploaded.seek(0)
    return uploaded
