"""Workspace settings tests: timezone, locale, and logo update flows.

These cover the Settings > Workspace page contract: admin-only writes,
IANA timezone validation, curated locale choices, and server-side logo
image sniffing.
"""

import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.accounts.test_avatar_api import _image_bytes

COMPANY_URL = "/api/v1/companies/current/"
STORED_LOGO_PATTERN = re.compile(r"^logos/[0-9a-f-]{36}/[0-9a-f]{32}\.(jpg|png|webp)$")


@pytest.mark.django_db
def test_admin_can_update_timezone_and_locale(auth_client, tenant):
    response = auth_client(tenant.admin).patch(
        COMPANY_URL,
        {"timezone": "Europe/Paris", "locale": "fr"},
        format="json",
    )

    assert response.status_code == 200
    tenant.company.refresh_from_db()
    assert tenant.company.timezone == "Europe/Paris"
    assert tenant.company.locale == "fr"


@pytest.mark.django_db
def test_defaults_are_utc_and_english(company_factory):
    company = company_factory(name="Defaults Co", slug="defaults")

    assert company.timezone == "UTC"
    assert company.locale == "en"


@pytest.mark.django_db
def test_invalid_timezone_is_rejected(auth_client, tenant):
    response = auth_client(tenant.admin).patch(
        COMPANY_URL,
        {"timezone": "Not/AZone"},
        format="json",
    )

    assert response.status_code == 400
    assert "timezone" in response.json()
    tenant.company.refresh_from_db()
    assert tenant.company.timezone == "UTC"


@pytest.mark.django_db
def test_invalid_locale_is_rejected(auth_client, tenant):
    response = auth_client(tenant.admin).patch(
        COMPANY_URL,
        {"locale": "xx"},
        format="json",
    )

    assert response.status_code == 400
    assert "locale" in response.json()
    tenant.company.refresh_from_db()
    assert tenant.company.locale == "en"


@pytest.mark.django_db
def test_employee_cannot_update_workspace_settings(auth_client, tenant):
    response = auth_client(tenant.employee).patch(
        COMPANY_URL,
        {"timezone": "America/New_York"},
        format="json",
    )

    assert response.status_code == 403
    tenant.company.refresh_from_db()
    assert tenant.company.timezone == "UTC"


@pytest.mark.django_db
def test_member_can_read_workspace_settings(auth_client, tenant):
    response = auth_client(tenant.employee).get(COMPANY_URL)

    assert response.status_code == 200
    body = response.json()
    assert {"timezone", "locale", "logo"} <= set(body)
    assert body["timezone"] == "UTC"


@pytest.mark.django_db
def test_admin_can_upload_logo(auth_client, tenant):
    upload = SimpleUploadedFile(
        "logo.png", _image_bytes("PNG"), content_type="application/octet-stream"
    )
    response = auth_client(tenant.admin).patch(COMPANY_URL, {"logo": upload}, format="multipart")

    assert response.status_code == 200
    tenant.company.refresh_from_db()
    assert STORED_LOGO_PATTERN.match(tenant.company.logo.name)
    assert "/media/logos/" in response.json()["logo"]


@pytest.mark.django_db
def test_non_image_logo_is_rejected(auth_client, tenant):
    upload = SimpleUploadedFile("logo.svg", b"<svg></svg>", content_type="image/svg+xml")
    response = auth_client(tenant.admin).patch(COMPANY_URL, {"logo": upload}, format="multipart")

    assert response.status_code == 400
    assert "logo" in response.json()
    tenant.company.refresh_from_db()
    assert not tenant.company.logo


@pytest.mark.django_db
def test_name_change_preserves_other_workspace_fields(auth_client, tenant):
    tenant.company.timezone = "Europe/London"
    tenant.company.locale = "de"
    tenant.company.save(update_fields=["timezone", "locale", "updated_at"])

    response = auth_client(tenant.admin).patch(
        COMPANY_URL, {"name": "Renamed Workspace"}, format="json"
    )

    assert response.status_code == 200
    tenant.company.refresh_from_db()
    assert tenant.company.name == "Renamed Workspace"
    assert tenant.company.timezone == "Europe/London"
    assert tenant.company.locale == "de"
