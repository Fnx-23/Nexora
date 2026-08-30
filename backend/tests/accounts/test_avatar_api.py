"""
H-5 tests: avatar upload validation through PATCH /api/v1/auth/me/.

Uploads are sent with a deliberately wrong Content-Type to prove the server
sniffs actual bytes (Pillow) instead of trusting client metadata.
"""

import re
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from tests.conftest import DEFAULT_PASSWORD  # noqa: F401 - documents password source

ME_URL = "/api/v1/auth/me/"
STORED_NAME_PATTERN = re.compile(r"^avatars/[0-9a-f-]{36}/[0-9a-f]{32}\.(jpg|png|webp)$")


def _image_bytes(fmt: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (90, 120, 200)).save(buffer, fmt)
    return buffer.getvalue()


def _upload(client, filename: str, content: bytes):
    # Wrong declared MIME on purpose: server must not trust it.
    upload = SimpleUploadedFile(filename, content, content_type="application/octet-stream")
    return client.patch(ME_URL, {"avatar": upload}, format="multipart")


@pytest.mark.django_db
def test_valid_jpeg_upload(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "photo.jpg", _image_bytes("JPEG"))

    assert response.status_code == 200
    assert "/media/avatars/" in response.json()["avatar"]
    tenant.admin.refresh_from_db()
    assert STORED_NAME_PATTERN.match(tenant.admin.avatar.name)


@pytest.mark.django_db
def test_valid_png_upload(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "photo.png", _image_bytes("PNG"))

    assert response.status_code == 200
    tenant.admin.refresh_from_db()
    assert STORED_NAME_PATTERN.match(tenant.admin.avatar.name)


@pytest.mark.django_db
def test_valid_webp_upload(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "photo.webp", _image_bytes("WEBP"))

    assert response.status_code == 200
    tenant.admin.refresh_from_db()
    assert STORED_NAME_PATTERN.match(tenant.admin.avatar.name)


@pytest.mark.django_db
def test_traversal_style_filename_is_neutralized(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "../../etc/passwd.png", _image_bytes("PNG"))

    assert response.status_code == 200
    tenant.admin.refresh_from_db()
    assert STORED_NAME_PATTERN.match(tenant.admin.avatar.name)
    assert ".." not in tenant.admin.avatar.name


@pytest.mark.django_db
def test_html_content_rejected_even_with_image_extension(auth_client, tenant):
    response = _upload(
        auth_client(tenant.admin),
        "payload.png",
        b"<html><script>alert('xss')</script></html>",
    )

    assert response.status_code == 400
    assert "avatar" in response.json()
    tenant.admin.refresh_from_db()
    assert not tenant.admin.avatar


@pytest.mark.django_db
def test_svg_content_rejected(auth_client, tenant):
    svg = (
        b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">'
        b"<script>alert(1)</script></svg>"
    )
    response = _upload(auth_client(tenant.admin), "vector.svg", svg)

    assert response.status_code == 400


@pytest.mark.django_db
def test_executable_magic_rejected_despite_image_extension(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "binary.png", b"MZ\x90\x00\x03\x00\x00\x00")

    assert response.status_code == 400


@pytest.mark.django_db
def test_content_extension_mismatch_rejected(auth_client, tenant):
    # PNG bytes inside a .jpg name: each format is individually allowed,
    # so this exercises the strict content<->extension agreement rule.
    response = _upload(auth_client(tenant.admin), "declared-jpg.jpg", _image_bytes("PNG"))

    assert response.status_code == 400
    assert "match its extension" in str(response.json())


@pytest.mark.django_db
@override_settings(AVATAR_MAX_SIZE_MB=0)  # force every payload over the limit
def test_oversized_file_rejected(auth_client, tenant):
    response = _upload(auth_client(tenant.admin), "big.png", _image_bytes("PNG"))

    assert response.status_code == 400
    assert "MB" in str(response.json()["avatar"][0])


@pytest.mark.django_db
def test_failed_upload_preserves_existing_avatar(auth_client, tenant):
    client = auth_client(tenant.admin)
    ok = _upload(client, "first.png", _image_bytes("PNG"))
    assert ok.status_code == 200
    tenant.admin.refresh_from_db()
    original_name = tenant.admin.avatar.name

    bad = _upload(client, "bad.png", b"<html>nope</html>")
    assert bad.status_code == 400

    tenant.admin.refresh_from_db()
    assert tenant.admin.avatar.name == original_name
