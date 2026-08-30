"""Comprehensive security and functionality tests for document management."""

import pytest
from apps.companies.models import RoleChoices
from apps.documents.models import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    Document,
    EntityKind,
    _sanitize_filename,
)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

pytestmark = pytest.mark.django_db

DOCUMENTS_URL = "/api/v1/documents/"


def _upload(
    client,
    company,
    file_content=b"test content",
    filename="test.pdf",
    content_type="application/pdf",
    **extra,
):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    f = SimpleUploadedFile(
        filename,
        file_content,
        content_type=content_type,
    )
    data = {"file": f, **extra}
    return client.post(DOCUMENTS_URL, data, format="multipart")


def _list(client, company, **params):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(DOCUMENTS_URL, params)


def _detail(client, company, doc_id):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(f"{DOCUMENTS_URL}{doc_id}/")


def _rename(client, company, doc_id, new_name):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.patch(
        f"{DOCUMENTS_URL}{doc_id}/rename/",
        {"filename": new_name},
        format="json",
    )


def _delete(client, company, doc_id):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.delete(f"{DOCUMENTS_URL}{doc_id}/")


def _download(client, company, doc_id):
    client.credentials(HTTP_X_COMPANY_ID=str(company.id))
    return client.get(f"{DOCUMENTS_URL}{doc_id}/download/")


def _create_doc(
    company,
    uploaded_by,
    filename="test.pdf",
    **kwargs,
):
    return Document.objects.create(
        company=company,
        original_filename=filename,
        mime_type="application/pdf",
        size=1024,
        uploaded_by=uploaded_by,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# Filename sanitization
# --------------------------------------------------------------------------- #
class TestSanitizeFilename:
    def test_strips_directory_components(self):
        assert _sanitize_filename("../../../etc/passwd") == "passwd"

    def test_strips_backslashes(self):
        result = _sanitize_filename("path\\to\\file.pdf")
        assert result == "path_to_file.pdf"

    def test_removes_null_bytes(self):
        assert _sanitize_filename("file\x00.pdf") == "file.pdf"

    def test_strips_leading_dots(self):
        assert _sanitize_filename("...hidden") == "hidden"

    def test_strips_leading_spaces(self):
        assert _sanitize_filename("   spaced.txt") == "spaced.txt"

    def test_replaces_double_dots(self):
        assert _sanitize_filename("file..name.pdf") == "file_name.pdf"

    def test_replaces_tilde(self):
        assert _sanitize_filename("~/.ssh/key") == "key"

    def test_empty_becomes_unnamed(self):
        assert _sanitize_filename("") == "unnamed"
        assert _sanitize_filename("...") == "unnamed"

    def test_normal_filename_unchanged(self):
        assert _sanitize_filename("report.pdf") == "report.pdf"

    def test_path_traversal_complex(self):
        path = "../../var/www/../../etc/shadow"
        assert _sanitize_filename(path) == "shadow"


# --------------------------------------------------------------------------- #
# Upload — success
# --------------------------------------------------------------------------- #
class TestUpload:
    def test_upload_creates_document(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
        )
        assert resp.status_code == 201
        q = Document.objects.filter(company=tenant.company)
        assert q.count() == 1
        doc = Document.objects.first()
        assert doc.original_filename == "test.pdf"
        assert doc.mime_type == "application/pdf"
        assert doc.size == len(b"test content")
        assert doc.uploaded_by == tenant.admin

    def test_upload_with_project_link(
        self,
        tenant,
        auth_client,
        project_factory,
    ):
        project = project_factory(tenant.company, name="P1")
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            entity_kind="PROJECT",
            entity_id=str(project.pk),
        )
        assert resp.status_code == 201
        doc = Document.objects.first()
        assert doc.entity_kind == "PROJECT"
        assert doc.entity_id == project.pk

    def test_upload_with_customer_link(
        self,
        tenant,
        auth_client,
        customer_factory,
    ):
        customer = customer_factory(tenant.company, name="C1")
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            entity_kind="CUSTOMER",
            entity_id=str(customer.pk),
        )
        assert resp.status_code == 201
        doc = Document.objects.first()
        assert doc.entity_kind == "CUSTOMER"

    def test_upload_allows_image(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"\x89PNG\r\n",
            filename="photo.png",
            content_type="image/png",
        )
        assert resp.status_code == 201

    def test_upload_allows_text(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"hello",
            filename="notes.txt",
            content_type="text/plain",
        )
        assert resp.status_code == 201


# --------------------------------------------------------------------------- #
# Upload — security: file type rejection
# --------------------------------------------------------------------------- #
class TestUploadSecurityFileTypes:
    def test_rejects_exe(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"MZ\x90\x00",
            filename="virus.exe",
            content_type="application/x-msdownload",
        )
        assert resp.status_code == 400
        assert "not allowed" in resp.data["detail"]

    def test_rejects_php(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"<?php echo 1; ?>",
            filename="shell.php",
            content_type="application/x-php",
        )
        assert resp.status_code == 400

    def test_rejects_html(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"<script>alert(1)</script>",
            filename="xss.html",
            content_type="text/html",
        )
        assert resp.status_code == 400

    def test_rejects_javascript(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"alert(1)",
            filename="script.js",
            content_type="application/javascript",
        )
        assert resp.status_code == 400

    def test_rejects_bash_script(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"#!/bin/bash\nrm -rf /",
            filename="evil.sh",
            content_type="application/x-sh",
        )
        assert resp.status_code == 400

    def test_rejects_unknown_mime(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"\x00\x01\x02",
            filename="mystery.bin",
            content_type="application/octet-stream",
        )
        assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Upload — security: file size
# --------------------------------------------------------------------------- #
class TestUploadSecurityFileSize:
    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=1024 * 1024 * 50)
    def test_rejects_oversized_file(self, tenant, auth_client):
        big = b"x" * (MAX_FILE_SIZE_BYTES + 1)
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=big,
            filename="huge.pdf",
            content_type="application/pdf",
        )
        assert resp.status_code == 400
        assert "exceeds maximum size" in resp.data["detail"]


# --------------------------------------------------------------------------- #
# Upload — security: no file
# --------------------------------------------------------------------------- #
class TestUploadSecurityNoFile:
    def test_rejects_missing_file(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        client.credentials(
            HTTP_X_COMPANY_ID=str(tenant.company.id),
        )
        resp = client.post(
            DOCUMENTS_URL,
            {"entity_kind": "COMPANY"},
            format="multipart",
        )
        assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Upload — security: filename sanitization
# --------------------------------------------------------------------------- #
class TestUploadSecurityFilename:
    def test_path_traversal_in_filename(
        self,
        tenant,
        auth_client,
    ):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"test",
            filename="../../../etc/passwd.pdf",
            content_type="application/pdf",
        )
        assert resp.status_code == 201
        doc = Document.objects.first()
        assert ".." not in doc.original_filename
        assert "/" not in doc.original_filename

    def test_null_byte_in_filename(self, tenant, auth_client):
        resp = _upload(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
            file_content=b"test",
            filename="file\x00.pdf",
            content_type="application/pdf",
        )
        assert resp.status_code == 201
        doc = Document.objects.first()
        assert "\x00" not in doc.original_filename


# --------------------------------------------------------------------------- #
# List & tenant isolation
# --------------------------------------------------------------------------- #
class TestListDocuments:
    def test_list_documents(self, tenant, auth_client):
        _create_doc(tenant.company, tenant.admin, filename="a.pdf")
        _create_doc(tenant.company, tenant.admin, filename="b.pdf")
        client = auth_client(tenant.admin, tenant.company)
        resp = _list(client, tenant.company)
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_filter_by_entity_kind(
        self,
        tenant,
        auth_client,
        project_factory,
    ):
        project = project_factory(tenant.company, name="P1")
        _create_doc(
            tenant.company,
            tenant.admin,
            filename="company.pdf",
        )
        _create_doc(
            tenant.company,
            tenant.admin,
            filename="project.pdf",
            entity_kind="PROJECT",
            entity_id=project.pk,
        )
        client = auth_client(tenant.admin, tenant.company)
        resp = _list(client, tenant.company, entity_kind="PROJECT")
        assert resp.data["count"] == 1
        fn = resp.data["results"][0]["original_filename"]
        assert fn == "project.pdf"

    def test_tenant_isolation(
        self,
        tenant,
        auth_client,
        company_factory,
        user_factory,
        membership_factory,
    ):
        company_b = company_factory(
            name="Company B",
            slug="company-b",
        )
        admin_b = user_factory(email="admin_b@test.com")
        membership_factory(
            admin_b,
            company_b,
            RoleChoices.ADMIN,
        )

        _create_doc(tenant.company, tenant.admin, filename="a.pdf")
        _create_doc(company_b, admin_b, filename="b.pdf")

        resp_a = _list(
            auth_client(tenant.admin, tenant.company),
            tenant.company,
        )
        resp_b = _list(
            auth_client(admin_b, company_b),
            company_b,
        )
        assert resp_a.data["count"] == 1
        assert resp_b.data["count"] == 1
        fn_a = resp_a.data["results"][0]["original_filename"]
        fn_b = resp_b.data["results"][0]["original_filename"]
        assert fn_a == "a.pdf"
        assert fn_b == "b.pdf"


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
class TestDownload:
    def test_download_returns_file(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        resp = _download(client, tenant.company, doc_id)
        assert resp.status_code == 200

    def test_download_sets_content_disposition(
        self,
        tenant,
        auth_client,
    ):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(
            client,
            tenant.company,
            filename="report.pdf",
        )
        doc_id = resp_upload.data["id"]
        resp = _download(client, tenant.company, doc_id)
        assert "report.pdf" in resp.get("Content-Disposition", "")


# --------------------------------------------------------------------------- #
# Rename
# --------------------------------------------------------------------------- #
class TestRename:
    def test_rename_document(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        resp = _rename(
            client,
            tenant.company,
            doc_id,
            "new_name.pdf",
        )
        assert resp.status_code == 200
        assert resp.data["original_filename"] == "new_name.pdf"

    def test_rename_sanitizes_path_traversal(
        self,
        tenant,
        auth_client,
    ):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        resp = _rename(
            client,
            tenant.company,
            doc_id,
            "../../../etc/shadow",
        )
        assert resp.status_code == 200
        fn = resp.data["original_filename"]
        assert ".." not in fn
        assert "/" not in fn

    def test_rename_empty_name_rejected(
        self,
        tenant,
        auth_client,
    ):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        resp = _rename(client, tenant.company, doc_id, "")
        assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Delete — permissions
# --------------------------------------------------------------------------- #
class TestDelete:
    def test_admin_can_delete(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        resp = _delete(client, tenant.company, doc_id)
        assert resp.status_code == 204
        assert not Document.objects.filter(pk=doc_id).exists()

    def test_employee_cannot_delete(
        self,
        tenant,
        auth_client,
        user_factory,
    ):
        employee = user_factory(email="emp@test.com")
        from apps.companies.models import Membership

        Membership.objects.create(
            user=employee,
            company=tenant.company,
            role=RoleChoices.EMPLOYEE,
        )
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        emp_client = auth_client(employee, tenant.company)
        resp = _delete(emp_client, tenant.company, doc_id)
        assert resp.status_code == 403

    def test_manager_can_delete(
        self,
        tenant,
        auth_client,
        user_factory,
    ):
        manager = user_factory(email="mgr@test.com")
        from apps.companies.models import Membership

        Membership.objects.create(
            user=manager,
            company=tenant.company,
            role=RoleChoices.MANAGER,
        )
        client = auth_client(tenant.admin, tenant.company)
        resp_upload = _upload(client, tenant.company)
        doc_id = resp_upload.data["id"]
        mgr_client = auth_client(manager, tenant.company)
        resp = _delete(mgr_client, tenant.company, doc_id)
        assert resp.status_code == 204


# --------------------------------------------------------------------------- #
# Permissions — unauthenticated / no membership
# --------------------------------------------------------------------------- #
class TestPermissions:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(DOCUMENTS_URL)
        assert resp.status_code in (401, 403)

    def test_no_membership_returns_403(
        self,
        api_client,
        user_factory,
    ):
        orphan = user_factory(email="orphan@test.com")
        api_client.force_authenticate(user=orphan)
        resp = api_client.get(DOCUMENTS_URL)
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
class TestDocumentModel:
    def test_str_representation(self, tenant):
        doc = _create_doc(
            tenant.company,
            tenant.admin,
            filename="report.pdf",
        )
        assert str(doc) == "report.pdf"

    def test_entity_kind_choices(self, tenant):
        assert EntityKind.COMPANY == "COMPANY"
        assert EntityKind.PROJECT == "PROJECT"
        assert EntityKind.CUSTOMER == "CUSTOMER"

    def test_upload_path_contains_company_id(
        self,
        tenant,
        auth_client,
    ):
        client = auth_client(tenant.admin, tenant.company)
        resp = _upload(client, tenant.company)
        doc = Document.objects.get(pk=resp.data["id"])
        assert str(tenant.company.id) in doc.file.name


# --------------------------------------------------------------------------- #
# Security constants validation
# --------------------------------------------------------------------------- #
class TestSecurityConstants:
    def test_pdf_in_allowed_types(self):
        assert "application/pdf" in ALLOWED_MIME_TYPES

    def test_exe_not_in_allowed_types(self):
        assert "application/x-msdownload" not in ALLOWED_MIME_TYPES

    def test_html_not_in_allowed_types(self):
        assert "text/html" not in ALLOWED_MIME_TYPES

    def test_pdf_in_allowed_extensions(self):
        assert ".pdf" in ALLOWED_EXTENSIONS

    def test_exe_not_in_allowed_extensions(self):
        assert ".exe" not in ALLOWED_EXTENSIONS

    def test_php_not_in_allowed_extensions(self):
        assert ".php" not in ALLOWED_EXTENSIONS

    def test_max_size_is_reasonable(self):
        assert MAX_FILE_SIZE_BYTES == 25 * 1024 * 1024
