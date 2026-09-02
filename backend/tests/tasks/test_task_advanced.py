"""API tests for advanced task management: comments, checklist, subtasks,
labels, attachments, task history and the rich detail endpoint."""

import pytest
from apps.activities.models import Activity, ActivityAction
from apps.companies.models import Membership, RoleChoices
from apps.tasks.models import (
    TaskChecklistItem,
    TaskComment,
    TaskLabel,
    TaskPriority,
    TaskSubtask,
)
from django.core.files.uploadedfile import SimpleUploadedFile

# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestComments:
    def test_list_comments_empty(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/comments/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_comment(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "First!"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["task"] == str(t.id)
        assert body["author"] == str(tenant.admin.id)
        assert body["author_name"] is not None

    def test_add_comment_requires_body(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": ""},
            format="json",
        )
        assert resp.status_code == 400
        assert "body" in resp.json()

    def test_list_comments_returns_creation_order(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        for text in ("one", "two", "three"):
            client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": text}, format="json")

        resp = client.get(f"/api/v1/tasks/{t.id}/comments/")
        bodies = [c["body"] for c in resp.json()]
        assert bodies == ["one", "two", "three"]

    def test_author_can_edit_own_comment(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "original"},
            format="json",
        )
        comment_id = resp.json()["id"]
        resp = auth_client(tenant.employee, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/comments/{comment_id}/",
            {"body": "edited"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "edited"

    def test_employee_cannot_edit_others_comment(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "admin says"},
            format="json",
        )
        comment_id = resp.json()["id"]
        resp = auth_client(tenant.employee, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/comments/{comment_id}/",
            {"body": "tampered"},
            format="json",
        )
        assert resp.status_code == 403

    def test_employee_cannot_delete_others_comment(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "admin says"},
            format="json",
        )
        comment_id = resp.json()["id"]
        resp = auth_client(tenant.employee, tenant.company).delete(
            f"/api/v1/tasks/{t.id}/comments/{comment_id}/",
        )
        assert resp.status_code == 403
        assert TaskComment.objects.filter(pk=comment_id).exists()

    def test_manager_can_edit_others_comment(
        self,
        tenant,
        auth_client,
        task_factory,
    ):
        Membership.objects.filter(user=tenant.employee, company=tenant.company).update(
            role=RoleChoices.MANAGER
        )
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "admin says"},
            format="json",
        )
        comment_id = resp.json()["id"]
        resp = auth_client(tenant.employee, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/comments/{comment_id}/",
            {"body": "moderated"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "moderated"

    def test_author_can_delete_own_comment(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "mine"},
            format="json",
        )
        comment_id = resp.json()["id"]
        resp = auth_client(tenant.employee, tenant.company).delete(
            f"/api/v1/tasks/{t.id}/comments/{comment_id}/",
        )
        assert resp.status_code == 204
        assert not TaskComment.objects.filter(pk=comment_id).exists()

    def test_comment_not_found(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/comments/00000000-0000-0000-0000-000000000000/",
            {"body": "nope"},
            format="json",
        )
        assert resp.status_code == 404

    def test_cross_tenant_add_comment_is_404(self, two_tenants, auth_client, task_factory):
        foreign = task_factory(two_tenants["b"]["company"], title="Their task")
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/tasks/{foreign.id}/comments/",
            {"body": "spam"},
            format="json",
        )
        assert resp.status_code == 404

    def test_cross_tenant_list_comments_is_404(self, two_tenants, auth_client, task_factory):
        foreign = task_factory(two_tenants["b"]["company"], title="Their task")
        resp = auth_client(two_tenants["a"]["user"]).get(f"/api/v1/tasks/{foreign.id}/comments/")
        assert resp.status_code == 404

    def test_comment_added_activity(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/comments/",
            {"body": "hi"},
            format="json",
        )
        assert Activity.objects.filter(
            action=ActivityAction.TASK_COMMENT_ADDED,
            entity_type="task",
            entity_id=t.id,
        ).exists()

    def test_comment_deleted_activity(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        cid = client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": "hi"}, format="json").json()[
            "id"
        ]
        client.delete(f"/api/v1/tasks/{t.id}/comments/{cid}/")
        assert Activity.objects.filter(
            action=ActivityAction.TASK_COMMENT_DELETED,
            entity_type="task",
            entity_id=t.id,
        ).exists()


# ---------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestChecklist:
    def test_empty_checklist(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/checklist/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_item_auto_positions(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        first = client.post(
            f"/api/v1/tasks/{t.id}/checklist/", {"text": "one"}, format="json"
        ).json()
        second = client.post(
            f"/api/v1/tasks/{t.id}/checklist/", {"text": "two"}, format="json"
        ).json()
        assert first["position"] == 0
        assert second["position"] == 1

    def test_add_item_explicit_position(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/checklist/",
            {"text": "five", "position": 5},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["position"] == 5

    def test_add_item_requires_text(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/checklist/",
            {"text": "   "},
            format="json",
        )
        assert resp.status_code == 400

    def test_toggle_completed(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        item = client.post(
            f"/api/v1/tasks/{t.id}/checklist/", {"text": "task"}, format="json"
        ).json()
        resp = client.patch(
            f"/api/v1/tasks/{t.id}/checklist/{item['id']}/",
            {"completed": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

    def test_delete_item(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        item = client.post(f"/api/v1/tasks/{t.id}/checklist/", {"text": "x"}, format="json").json()
        resp = client.delete(f"/api/v1/tasks/{t.id}/checklist/{item['id']}/")
        assert resp.status_code == 204
        assert not TaskChecklistItem.objects.filter(pk=item["id"]).exists()

    def test_employee_can_toggle_checklist(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.employee, tenant.company)
        item = client.post(f"/api/v1/tasks/{t.id}/checklist/", {"text": "x"}, format="json").json()
        resp = client.patch(
            f"/api/v1/tasks/{t.id}/checklist/{item['id']}/",
            {"completed": True},
            format="json",
        )
        assert resp.status_code == 200

    def test_cross_tenant_checklist_is_404(self, two_tenants, auth_client, task_factory):
        foreign = task_factory(two_tenants["b"]["company"], title="Their")
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/tasks/{foreign.id}/checklist/",
            {"text": "spam"},
            format="json",
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Subtasks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSubtasks:
    def test_add_and_auto_position(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        first = client.post(
            f"/api/v1/tasks/{t.id}/subtasks/", {"title": "sub one"}, format="json"
        ).json()
        second = client.post(
            f"/api/v1/tasks/{t.id}/subtasks/", {"title": "sub two"}, format="json"
        ).json()
        assert first["position"] == 0
        assert second["position"] == 1

    def test_list_subtasks(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        client.post(f"/api/v1/tasks/{t.id}/subtasks/", {"title": "a"}, format="json")
        resp = client.get(f"/api/v1/tasks/{t.id}/subtasks/")
        assert resp.status_code == 200
        assert [s["title"] for s in resp.json()] == ["a"]

    def test_toggle_subtask(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        sub = client.post(f"/api/v1/tasks/{t.id}/subtasks/", {"title": "a"}, format="json").json()
        resp = client.patch(
            f"/api/v1/tasks/{t.id}/subtasks/{sub['id']}/",
            {"completed": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

    def test_subtask_requires_title(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/subtasks/",
            {"title": ""},
            format="json",
        )
        assert resp.status_code == 400

    def test_delete_subtask(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        sub = client.post(f"/api/v1/tasks/{t.id}/subtasks/", {"title": "a"}, format="json").json()
        resp = client.delete(f"/api/v1/tasks/{t.id}/subtasks/{sub['id']}/")
        assert resp.status_code == 204
        assert not TaskSubtask.objects.filter(pk=sub["id"]).exists()


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLabels:
    def test_admin_can_create_label(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/labels/",
            {"name": "Backend", "color": "#3b82f6"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Backend"

    def test_list_labels(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        client.post("/api/v1/labels/", {"name": "Backend"}, format="json")
        client.post("/api/v1/labels/", {"name": "Frontend"}, format="json")
        resp = client.get("/api/v1/labels/")
        assert resp.status_code == 200
        assert {r["name"] for r in resp.json()["results"]} == {"Backend", "Frontend"}

    def test_employee_cannot_create_label(self, tenant, auth_client):
        resp = auth_client(tenant.employee, tenant.company).post(
            "/api/v1/labels/",
            {"name": "Sneaky"},
            format="json",
        )
        assert resp.status_code == 403

    def test_employee_can_list_labels(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        client.post("/api/v1/labels/", {"name": "Backend"}, format="json")
        resp = auth_client(tenant.employee, tenant.company).get("/api/v1/labels/")
        assert resp.status_code == 200

    def test_employee_cannot_delete_label(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        label = client.post("/api/v1/labels/", {"name": "Backend"}, format="json").json()
        resp = auth_client(tenant.employee, tenant.company).delete(f"/api/v1/labels/{label['id']}/")
        assert resp.status_code == 403

    def test_duplicate_label_name_rejected(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        client.post("/api/v1/labels/", {"name": "Backend"}, format="json")
        resp = client.post("/api/v1/labels/", {"name": "backend"}, format="json")
        assert resp.status_code == 400
        assert "name" in resp.json()

    def test_label_cross_tenant_isolated(self, two_tenants, auth_client):
        client_a = auth_client(two_tenants["a"]["user"])
        client_a.post("/api/v1/labels/", {"name": "Alpha"}, format="json")
        resp = auth_client(two_tenants["b"]["user"]).get("/api/v1/labels/")
        assert resp.json()["count"] == 0


@pytest.mark.django_db
class TestTaskLabels:
    def test_create_task_with_label_ids(self, tenant, auth_client):
        label = TaskLabel.objects.create(company=tenant.company, name="Backend")
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            {"title": "T", "label_ids": [str(label.id)]},
            format="json",
        )
        assert resp.status_code == 201
        assert [label["name"] for label in resp.json()["labels"]] == ["Backend"]

    def test_update_task_labels(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        label_a = TaskLabel.objects.create(company=tenant.company, name="A")
        label_b = TaskLabel.objects.create(company=tenant.company, name="B")
        client = auth_client(tenant.admin, tenant.company)
        resp = client.patch(
            f"/api/v1/tasks/{t.id}/",
            {"label_ids": [str(label_a.id), str(label_b.id)]},
            format="json",
        )
        assert resp.status_code == 200
        assert {label["name"] for label in resp.json()["labels"]} == {"A", "B"}

    def test_clear_task_labels(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        label = TaskLabel.objects.create(company=tenant.company, name="A")
        t.labels.add(label)
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"label_ids": []},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["labels"] == []

    def test_label_ids_cross_tenant_rejected(self, two_tenants, auth_client, task_factory):
        t = task_factory(two_tenants["a"]["company"], title="T")
        foreign_label = TaskLabel.objects.create(
            company=two_tenants["b"]["company"], name="Foreign"
        )
        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/tasks/{t.id}/",
            {"label_ids": [str(foreign_label.id)]},
            format="json",
        )
        assert resp.status_code == 400
        assert "label_ids" in resp.json()

    def test_list_task_includes_labels(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        label = TaskLabel.objects.create(company=tenant.company, name="Urgent")
        t.labels.add(label)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/?label={label.id!s}")
        assert resp.status_code == 200

    def test_employee_can_apply_labels(self, tenant, auth_client, task_factory):
        label = TaskLabel.objects.create(company=tenant.company, name="Backend")
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.employee, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"label_ids": [str(label.id)]},
            format="json",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Rich detail: counts + recent activity
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTaskDetail:
    def test_retrieve_includes_nested_counts(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": "c1"}, format="json")
        client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": "c2"}, format="json")
        item = client.post(f"/api/v1/tasks/{t.id}/checklist/", {"text": "x"}, format="json").json()
        client.patch(
            f"/api/v1/tasks/{t.id}/checklist/{item['id']}/",
            {"completed": True},
            format="json",
        )
        client.post(f"/api/v1/tasks/{t.id}/checklist/", {"text": "y"}, format="json")
        client.post(f"/api/v1/tasks/{t.id}/subtasks/", {"title": "s"}, format="json")

        resp = client.get(f"/api/v1/tasks/{t.id}/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["comments_count"] == 2
        assert body["checklist_total"] == 2
        assert body["checklist_done"] == 1
        assert body["subtask_total"] == 1
        assert body["subtask_done"] == 0

    def test_retrieve_includes_recent_activity(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="History task")
        auth_client(tenant.admin, tenant.company)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")
        assert resp.status_code == 200
        actions = {a["action"] for a in resp.json()["recent_activity"]}
        assert ActivityAction.TASK_CREATED in actions

    def test_list_includes_counts(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": "c"}, format="json")
        resp = client.get("/api/v1/tasks/")
        row = next(r for r in resp.json()["results"] if r["id"] == str(t.id))
        assert row["comments_count"] == 1
        assert row["checklist_total"] == 0


# ---------------------------------------------------------------------------
# History from activity signals
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTaskHistory:
    def test_priority_change_recorded(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T", priority=TaskPriority.LOW)
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"priority": "URGENT"},
            format="json",
        )
        assert resp.status_code == 200
        assert Activity.objects.filter(
            action=ActivityAction.TASK_PRIORITY_CHANGED,
            entity_type="task",
            entity_id=t.id,
            metadata__new_priority="URGENT",
        ).exists()

    def test_due_date_change_recorded(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"due_date": "2026-12-31"},
            format="json",
        )
        assert resp.status_code == 200
        assert Activity.objects.filter(
            action=ActivityAction.TASK_DUE_DATE_CHANGED,
            entity_type="task",
            entity_id=t.id,
        ).exists()

    def test_status_change_via_patch_recorded(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200
        assert Activity.objects.filter(
            action=ActivityAction.TASK_STATUS_CHANGED,
            entity_type="task",
            entity_id=t.id,
        ).exists()


# ---------------------------------------------------------------------------
# Attachments (documents bound to a task)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTaskAttachments:
    def test_upload_attached_to_task(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        upload = SimpleUploadedFile(
            "spec.txt",
            b"some spec content",
            content_type="text/plain",
        )
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/documents/",
            {
                "file": upload,
                "entity_kind": "TASK",
                "entity_id": str(t.id),
            },
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["entity_kind"] == "TASK"
        assert resp.json()["entity_id"] == str(t.id)

    def test_upload_to_foreign_task_rejected(self, two_tenants, auth_client, task_factory):
        foreign = task_factory(two_tenants["b"]["company"], title="Their")
        upload = SimpleUploadedFile(
            "leak.txt",
            b"data",
            content_type="text/plain",
        )
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/documents/",
            {
                "file": upload,
                "entity_kind": "TASK",
                "entity_id": str(foreign.id),
            },
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_missing_entity_id(self, tenant, auth_client, task_factory):
        upload = SimpleUploadedFile(
            "x.txt",
            b"data",
            content_type="text/plain",
        )
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/documents/",
            {"file": upload, "entity_kind": "TASK"},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_scan_task_attachments(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        upload = SimpleUploadedFile("spec.txt", b"data", content_type="text/plain")
        auth_client(tenant.admin, tenant.company).post(
            "/api/v1/documents/",
            {"file": upload, "entity_kind": "TASK", "entity_id": str(t.id)},
            format="multipart",
        )
        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/documents/", {"entity_kind": "TASK", "entity_id": str(t.id)}
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["entity_kind"] == "TASK"

    def test_attachment_added_activity(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        upload = SimpleUploadedFile("spec.txt", b"data", content_type="text/plain")
        auth_client(tenant.admin, tenant.company).post(
            "/api/v1/documents/",
            {"file": upload, "entity_kind": "TASK", "entity_id": str(t.id)},
            format="multipart",
        )
        assert Activity.objects.filter(
            action=ActivityAction.TASK_ATTACHMENT_ADDED,
            entity_type="task",
            entity_id=t.id,
        ).exists()

    def test_task_deleted_comments_and_checklist_removed(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        client = auth_client(tenant.admin, tenant.company)
        client.post(f"/api/v1/tasks/{t.id}/comments/", {"body": "c"}, format="json")
        client.post(f"/api/v1/tasks/{t.id}/checklist/", {"text": "x"}, format="json")
        client.post(f"/api/v1/tasks/{t.id}/subtasks/", {"title": "s"}, format="json")
        assert TaskComment.objects.filter(task_id=t.id).count() == 1
        resp = client.delete(f"/api/v1/tasks/{t.id}/")
        assert resp.status_code == 204
        assert TaskComment.objects.filter(task_id=t.id).count() == 0
        assert TaskChecklistItem.objects.filter(task_id=t.id).count() == 0
        assert TaskSubtask.objects.filter(task_id=t.id).count() == 0


# ---------------------------------------------------------------------------
# Fixture: two_tenants (independent for this test file)
# ---------------------------------------------------------------------------


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    admin_a = user_factory(email="admin@a-adv.test")
    admin_b = user_factory(email="admin@b-adv.test")
    company_a = company_factory(name="Company A Advanced", slug="company-a-adv")
    company_b = company_factory(name="Company B Advanced", slug="company-b-adv")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
