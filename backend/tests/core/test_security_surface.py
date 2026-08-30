"""
HTTP surface hardening tests (audit L-10 / L-11 / requirement 6).

Covers the exposure flags for API documentation and the Django admin, and
pins HSTS to HTTPS-only responses so plain-HTTP development never advertises
it.
"""

import pytest
from django.test import Client, override_settings

DOCS_PATHS = ["/api/schema/", "/api/docs/", "/api/redoc/"]


@pytest.mark.django_db
class TestApiDocsGating:
    @pytest.mark.parametrize("path", DOCS_PATHS)
    def test_enabled_by_default_outside_production(self, api_client, path):
        assert api_client.get(path).status_code == 200

    @override_settings(API_DOCS_ENABLED=False)
    @pytest.mark.parametrize("path", DOCS_PATHS)
    def test_disabled_answers_404(self, api_client, path):
        assert api_client.get(path).status_code == 404


@pytest.mark.django_db
class TestAdminGating:
    def test_admin_available_by_default(self):
        response = Client().get("/admin/login/")

        assert response.status_code == 200

    @override_settings(ADMIN_ENABLED=False)
    def test_admin_disabled_answers_404_including_login(self, api_client):
        assert api_client.get("/admin/login/").status_code == 404
        assert api_client.get("/admin/").status_code == 404


@pytest.mark.django_db
class TestHstsSchemeConditional:
    """HSTS may be configured but must only be advertised over HTTPS."""

    @override_settings(SECURE_HSTS_SECONDS=31_536_000)
    @pytest.mark.parametrize("secure", [False, True])
    def test_hsts_only_on_secure_requests(self, secure):
        client = Client()
        response = client.get("/healthz/", secure=secure)

        header = response.headers.get("Strict-Transport-Security")
        if secure:
            assert header is not None
            assert "max-age" in header
        else:
            # Plain HTTP (development, internal probes) must never advertise HSTS.
            assert header is None


def test_security_headers_absence_is_edge_responsibility():
    """
    Documentation guard: Django deliberately does not set a CSP for API/admin
    HTML (the SPA edge nginx owns that policy); this test pins the headers it
    *does* own so regressions are visible.
    """
    response = Client().get("/admin/login/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
