"""API-level tests for the Task CRUD + status-change endpoints."""

import pytest
from apps.companies.models import Membership, RoleChoices
from apps.tasks.models import Task, TaskPriority, TaskStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(**overrides):
    data = {
        "title": "Fix login bug",
        "description": "Users cannot log in with SSO",
        "status": "TODO",
        "priority": "HIGH",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# List & Retrieve
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListTasks:
    def test_returns_paginated_list(self, tenant, auth_client, task_factory):
        for i in range(3):
            task_factory(tenant.company, title=f"Task {i}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/tasks/")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 3
        assert len(body["results"]) == 3

    def test_empty_list(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/tasks/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


@pytest.mark.django_db
class TestRetrieveTask:
    def test_retrieve_own_task(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="My Task")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")

        assert resp.status_code == 200
        assert resp.json()["title"] == "My Task"
        assert resp.json()["id"] == str(t.id)

    def test_retrieve_includes_project_name(
        self,
        tenant,
        auth_client,
        project_factory,
        task_factory,
    ):
        p = project_factory(tenant.company, name="Sprint 1")
        t = task_factory(tenant.company, title="Do stuff", project=p)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")

        assert resp.status_code == 200
        assert resp.json()["project_name"] == "Sprint 1"

    def test_retrieve_includes_created_by_name(
        self,
        tenant,
        auth_client,
        task_factory,
    ):
        t = task_factory(tenant.company, title="By admin", created_by=tenant.admin)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")

        assert resp.status_code == 200
        assert resp.json()["created_by_name"] is not None

    def test_retrieve_includes_assignee_name(
        self,
        tenant,
        auth_client,
        task_factory,
    ):
        t = task_factory(tenant.company, title="Assigned", assignee=tenant.employee)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")

        assert resp.status_code == 200
        assert resp.json()["assignee_name"] is not None

    def test_retrieve_no_project(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="Unlinked")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/tasks/{t.id}/")

        assert resp.status_code == 200
        assert resp.json()["project_name"] is None
        assert resp.json()["project"] is None


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateTask:
    def test_create_with_valid_data(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Fix login bug"
        assert body["status"] == "TODO"
        assert body["priority"] == "HIGH"

    def test_create_auto_stamps_company(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        t = Task.objects.get(pk=resp.json()["id"])
        assert t.company_id == tenant.company.id

    def test_create_auto_stamps_created_by(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        t = Task.objects.get(pk=resp.json()["id"])
        assert t.created_by_id == tenant.admin.id

    def test_create_with_valid_project(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="Sprint 1")
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(project=str(p.id)),
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["project"] == str(p.id)

    def test_create_with_valid_assignee(
        self,
        tenant,
        auth_client,
        membership_factory,
        user_factory,
    ):
        u = user_factory(email="dev@test.com")
        membership_factory(u, tenant.company, RoleChoices.EMPLOYEE)
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(assignee=str(u.id)),
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["assignee"] == str(u.id)

    def test_create_with_valid_status(self, tenant, auth_client):
        for status_val in ("TODO", "IN_PROGRESS", "IN_REVIEW", "DONE", "CANCELLED"):
            resp = auth_client(tenant.admin, tenant.company).post(
                "/api/v1/tasks/",
                _payload(title=f"Task-{status_val}", status=status_val),
                format="json",
            )
            assert resp.status_code == 201

    def test_create_requires_title(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            {},
            format="json",
        )
        assert resp.status_code == 400
        assert "title" in resp.json()

    def test_create_minimal_fields(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            {"title": "Minimal"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "TODO"
        assert body["priority"] == "MEDIUM"
        assert body["assignee"] is None
        assert body["project"] is None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateTask:
    def test_partial_update(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="Old Title")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"title": "New Title", "status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_full_update(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="Original")
        resp = auth_client(tenant.admin, tenant.company).put(
            f"/api/v1/tasks/{t.id}/",
            _payload(title="Replaced", status="DONE", priority="LOW"),
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Replaced"
        assert body["status"] == "DONE"
        assert body["priority"] == "LOW"

    def test_update_project_cross_tenant_rejected(
        self,
        two_tenants,
        auth_client,
        task_factory,
        project_factory,
    ):
        t = task_factory(two_tenants["a"]["company"], title="T")
        foreign_p = project_factory(two_tenants["b"]["company"], name="B Proj")

        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/tasks/{t.id}/",
            {"project": str(foreign_p.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "project" in resp.json()

    def test_update_assignee_must_be_company_member(
        self,
        tenant,
        auth_client,
        task_factory,
        user_factory,
        company_factory,
    ):
        t = task_factory(tenant.company, title="T")
        outsider = user_factory(email="outsider@test.com")
        other_co = company_factory(name="Other Co", slug="other-co")
        Membership.objects.create(user=outsider, company=other_co, role=RoleChoices.EMPLOYEE)

        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/",
            {"assignee": str(outsider.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "assignee" in resp.json()


# ---------------------------------------------------------------------------
# Delete (permanent)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeleteTask:
    def test_delete_removes_task(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).delete(
            f"/api/v1/tasks/{t.id}/",
        )
        assert resp.status_code == 204
        assert not Task.objects.filter(pk=t.id).exists()

    def test_delete_requires_manager_or_admin(self, tenant, auth_client, task_factory):
        employee = tenant.employee
        t = task_factory(tenant.company)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/tasks/{t.id}/",
        )
        assert resp.status_code == 403

        Membership.objects.filter(user=employee).update(role=RoleChoices.ADMIN)
        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/tasks/{t.id}/",
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Status Change
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestChangeStatus:
    def test_admin_can_change_status(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, status=TaskStatus.TODO)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {"status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"
        t.refresh_from_db()
        assert t.status == TaskStatus.IN_PROGRESS

    def test_employee_can_change_own_task_status(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, assignee=tenant.employee, status=TaskStatus.TODO)
        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {"status": "IN_REVIEW"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_REVIEW"

    def test_employee_can_change_status_of_task_they_created(
        self,
        tenant,
        auth_client,
        task_factory,
    ):
        t = task_factory(
            tenant.company,
            created_by=tenant.employee,
            status=TaskStatus.TODO,
        )
        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {"status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200

    def test_employee_cannot_change_others_task_status(
        self,
        tenant,
        auth_client,
        task_factory,
    ):
        t = task_factory(
            tenant.company,
            created_by=tenant.admin,
            assignee=tenant.admin,
            status=TaskStatus.TODO,
        )
        resp = auth_client(tenant.employee, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {"status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 403

    def test_change_status_missing_status_field(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {},
            format="json",
        )
        assert resp.status_code == 400

    def test_change_status_invalid_value(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/",
            {"status": "BOGUS"},
            format="json",
        )
        assert resp.status_code == 400

    def test_all_valid_statuses_accepted(self, tenant, auth_client, task_factory):
        for new_status in ("TODO", "IN_PROGRESS", "IN_REVIEW", "DONE", "CANCELLED"):
            t = task_factory(tenant.company, title=f"s-{new_status}", status=TaskStatus.TODO)
            resp = auth_client(tenant.admin, tenant.company).post(
                f"/api/v1/tasks/{t.id}/change-status/",
                {"status": new_status},
                format="json",
            )
            assert resp.status_code == 200, f"Failed for {new_status}"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidation:
    def test_invalid_status_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(status="BOGUS"),
            format="json",
        )
        assert resp.status_code == 400
        assert "status" in resp.json()

    def test_invalid_priority_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(priority="EXTREME"),
            format="json",
        )
        assert resp.status_code == 400
        assert "priority" in resp.json()

    def test_title_max_length_enforced(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(title="X" * 201),
            format="json",
        )
        assert resp.status_code == 400
        assert "title" in resp.json()

    def test_project_cross_tenant_rejected_on_create(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        foreign_p = project_factory(two_tenants["b"]["company"], name="Foreign")
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/tasks/",
            _payload(project=str(foreign_p.id)),
            format="json",
        )
        assert resp.status_code == 400
        assert "project" in resp.json()

    def test_assignee_cross_tenant_rejected_on_create(
        self,
        two_tenants,
        auth_client,
        user_factory,
        company_factory,
        membership_factory,
    ):
        outsider = user_factory(email="foreign-member@test.com")
        other_co = company_factory(name="Other", slug="other-val")
        membership_factory(outsider, other_co, RoleChoices.EMPLOYEE)

        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/tasks/",
            _payload(assignee=str(outsider.id)),
            format="json",
        )
        assert resp.status_code == 400
        assert "assignee" in resp.json()

    def test_nonexistent_project_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/tasks/",
            _payload(project="00000000-0000-0000-0000-000000000000"),
            format="json",
        )
        assert resp.status_code == 400
        assert "project" in resp.json()

    def test_valid_priority_values(self, tenant, auth_client):
        for prio in ("LOW", "MEDIUM", "HIGH", "URGENT"):
            resp = auth_client(tenant.admin, tenant.company).post(
                "/api/v1/tasks/",
                _payload(title=f"Task-{prio}", priority=prio),
                format="json",
            )
            assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSearch:
    def test_search_by_title(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="Login bug")
        task_factory(tenant.company, title="Payment error")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"search": "Login"},
        )
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.json()["results"]]
        assert titles == ["Login bug"]

    def test_search_by_description(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="A", description="SSO integration")
        task_factory(tenant.company, title="B", description="Email sending")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"search": "SSO"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "A"


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFiltering:
    def test_filter_by_status(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="Todo", status=TaskStatus.TODO)
        task_factory(tenant.company, title="Done", status=TaskStatus.DONE)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"status": "TODO"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "Todo"

    def test_filter_by_priority(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="Low", priority=TaskPriority.LOW)
        task_factory(tenant.company, title="Urgent", priority=TaskPriority.URGENT)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"priority": "URGENT"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "Urgent"

    def test_filter_by_project(self, tenant, auth_client, project_factory, task_factory):
        p = project_factory(tenant.company, name="Sprint 1")
        task_factory(tenant.company, title="In sprint", project=p)
        task_factory(tenant.company, title="Not in sprint")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"project": str(p.id)},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "In sprint"

    def test_filter_by_assignee(
        self,
        tenant,
        auth_client,
        task_factory,
        user_factory,
        membership_factory,
    ):
        u = user_factory(email="dev@test.com")
        membership_factory(u, tenant.company, RoleChoices.EMPLOYEE)
        task_factory(tenant.company, title="Mine", assignee=u)
        task_factory(tenant.company, title="Not mine")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"assignee": str(u.id)},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "Mine"

    def test_combined_filters(
        self,
        tenant,
        auth_client,
        project_factory,
        task_factory,
        user_factory,
        membership_factory,
    ):
        p = project_factory(tenant.company, name="Sprint 1")
        u = user_factory(email="dev2@test.com")
        membership_factory(u, tenant.company, RoleChoices.EMPLOYEE)

        task_factory(
            tenant.company,
            title="Match",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            project=p,
            assignee=u,
        )
        task_factory(
            tenant.company,
            title="Wrong status",
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            project=p,
            assignee=u,
        )
        task_factory(
            tenant.company,
            title="Wrong priority",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            project=p,
            assignee=u,
        )

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"status": "TODO", "priority": "HIGH", "project": str(p.id)},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["title"] == "Match"


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrdering:
    def test_order_by_title(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="Zebra")
        task_factory(tenant.company, title="Alpha")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"ordering": "title"},
        )
        titles = [r["title"] for r in resp.json()["results"]]
        assert titles == ["Alpha", "Zebra"]

    def test_order_by_created_at_desc(self, tenant, auth_client, task_factory):
        task_factory(tenant.company, title="First")
        task_factory(tenant.company, title="Second")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"ordering": "-created_at"},
        )
        titles = [r["title"] for r in resp.json()["results"]]
        assert titles == ["Second", "First"]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPagination:
    def test_default_page_size(self, tenant, auth_client, task_factory):
        for i in range(30):
            task_factory(tenant.company, title=f"T{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/tasks/")
        body = resp.json()
        assert body["count"] == 30
        assert len(body["results"]) == 25
        assert body["next"] is not None

    def test_custom_page_size(self, tenant, auth_client, task_factory):
        for i in range(5):
            task_factory(tenant.company, title=f"T{i}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"page_size": 2},
        )
        body = resp.json()
        assert body["count"] == 5
        assert len(body["results"]) == 2
        assert body["next"] is not None

    def test_second_page(self, tenant, auth_client, task_factory):
        for i in range(30):
            task_factory(tenant.company, title=f"T{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/tasks/",
            {"page": 2},
        )
        body = resp.json()
        assert len(body["results"]) == 5
        assert body["previous"] is not None


# ---------------------------------------------------------------------------
# Tenant Isolation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantIsolation:
    def test_cannot_list_other_company_tasks(
        self,
        two_tenants,
        auth_client,
        task_factory,
    ):
        own = task_factory(two_tenants["a"]["company"], title="Mine")
        foreign = task_factory(two_tenants["b"]["company"], title="Theirs")

        resp = auth_client(two_tenants["a"]["user"]).get("/api/v1/tasks/")
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()["results"]}
        assert str(own.id) in ids
        assert str(foreign.id) not in ids

    def test_cannot_retrieve_other_company_task(
        self,
        two_tenants,
        auth_client,
        task_factory,
    ):
        foreign = task_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).get(
            f"/api/v1/tasks/{foreign.id}/",
        )
        assert resp.status_code == 404

    def test_cannot_update_other_company_task(
        self,
        two_tenants,
        auth_client,
        task_factory,
    ):
        foreign = task_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/tasks/{foreign.id}/",
            {"title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404
        foreign.refresh_from_db()
        assert str(foreign) != "Hacked"

    def test_cannot_delete_other_company_task(
        self,
        two_tenants,
        auth_client,
        task_factory,
    ):
        foreign = task_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).delete(
            f"/api/v1/tasks/{foreign.id}/",
        )
        assert resp.status_code == 404

    def test_cannot_change_status_of_other_company_task(
        self,
        two_tenants,
        auth_client,
        task_factory,
    ):
        foreign = task_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/tasks/{foreign.id}/change-status/",
            {"status": "DONE"},
            format="json",
        )
        assert resp.status_code == 404

    def test_created_task_belongs_to_request_company(
        self,
        two_tenants,
        auth_client,
    ):
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/tasks/",
            {"title": "Local Only"},
            format="json",
        )
        assert resp.status_code == 201
        t = Task.objects.get(pk=resp.json()["id"])
        assert t.company_id == two_tenants["a"]["company"].id


# ---------------------------------------------------------------------------
# Fixtures: two_tenants (independent for this test file)
# ---------------------------------------------------------------------------


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    admin_a = user_factory(email="admin@a-tasks.test")
    admin_b = user_factory(email="admin@b-tasks.test")
    company_a = company_factory(name="Company A Tasks", slug="company-a-tasks")
    company_b = company_factory(name="Company B Tasks", slug="company-b-tasks")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
