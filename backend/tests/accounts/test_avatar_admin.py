"""
H-5 defense-in-depth: the Django admin change form must not be a bypass around
avatar validation. Staff-side uploads are checked with the very same
``validate_avatar_image`` used by the API, so there is one definition of a
valid avatar regardless of entry point.
"""

from io import BytesIO

import pytest
from apps.accounts.admin import AvatarValidatingUserChangeForm
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def test_admin_form_rejects_non_image_upload():
    form = AvatarValidatingUserChangeForm()
    form.cleaned_data = {
        "avatar": SimpleUploadedFile(
            "payload.png", b"<html><script>alert(1)</script></html>", content_type="image/png"
        )
    }
    with pytest.raises(ValidationError):
        form.clean_avatar()


def test_admin_form_accepts_valid_image_upload():
    form = AvatarValidatingUserChangeForm()
    upload = SimpleUploadedFile("ok.png", _png_bytes(), content_type="image/png")
    form.cleaned_data = {"avatar": upload}
    assert form.clean_avatar() is upload


@pytest.mark.django_db
def test_admin_form_leaves_stored_avatar_untouched(tenant):
    # An unchanged stored value is a FieldFile, not an UploadedFile: it must
    # pass through without re-validation (and without raising).
    form = AvatarValidatingUserChangeForm()
    form.cleaned_data = {"avatar": tenant.admin.avatar}
    assert form.clean_avatar() is tenant.admin.avatar
