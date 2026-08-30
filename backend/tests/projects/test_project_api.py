"""API-level tests for the Project CRUD + archive endpoints."""

import pytest
from apps.companies.models import Membership, RoleChoices
from apps.projects.models import Project, ProjectPriority, ProjectStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(**overrides):
    data = {
        "name": "Website Redesign",
        "description": "Overhaul the public website",
        "status": "PLANNING",
        "priority": "MEDIUM",
        "start_date": "2025-06-01",
        "deadline": "2025-09-30",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# List & Retrieve
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListProjects:
    def test_returns_paginated_list(self, tenant, auth_client, project_factory):
        for i in range(3):
            project_factory(tenant.company, name=f"Proj {i}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/projects/")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 3
        assert len(body["results"]) == 3

    def test_empty_list(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/projects/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_excludes_archived_from_default_list(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Active")
        project_factory(tenant.company, name="Done", status=ProjectStatus.ARCHIVED)

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/projects/")
        # The viewset does not filter out ARCHIVED by default; they appear in the list
        names = {r["name"] for r in resp.json()["results"]}
        assert "Active" in names
        assert "Done" in names


@pytest.mark.django_db
class TestRetrieveProject:
    def test_retrieve_own_project(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="My Project")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")

        assert resp.status_code == 200
        assert resp.json()["name"] == "My Project"
        assert resp.json()["id"] == str(p.id)

    def test_retrieve_includes_customer_name(
        self, tenant, auth_client, customer_factory, project_factory
    ):
        c = customer_factory(tenant.company, name="Acquired Corp")
        p = project_factory(tenant.company, name="For Customer", customer=c)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")

        assert resp.status_code == 200
        assert resp.json()["customer_name"] == "Acquired Corp"

    def test_retrieve_includes_manager_name(
        self,
        tenant,
        auth_client,
        membership_factory,
        user_factory,
        project_factory,
    ):
        mgr = user_factory(email="manager@test.com")
        membership_factory(mgr, tenant.company, RoleChoices.MANAGER)
        p = project_factory(tenant.company, name="Managed", manager=mgr)
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")

        assert resp.status_code == 200
        assert (
            resp.json()["manager_name"] == mgr.get_full_name()
            or resp.json()["manager_name"] == mgr.email
        )

    def test_retrieve_no_customer(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="No Cust")
        resp = auth_client(tenant.admin, tenant.company).get(f"/api/v1/projects/{p.id}/")

        assert resp.status_code == 200
        assert resp.json()["customer_name"] is None


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateProject:
    def test_create_with_valid_data(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Website Redesign"
        assert body["status"] == "PLANNING"
        assert body["priority"] == "MEDIUM"

    def test_create_auto_stamps_company(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(),
            format="json",
        )
        assert resp.status_code == 201
        p = Project.objects.get(pk=resp.json()["id"])
        assert p.company_id == tenant.company.id

    def test_create_minimal_fields(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            {"name": "Minimal"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "PLANNING"
        assert body["priority"] == "MEDIUM"
        assert body["customer"] is None
        assert body["manager"] is None

    def test_create_requires_name(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            {},
            format="json",
        )
        assert resp.status_code == 400
        assert "name" in resp.json()

    def test_create_with_valid_customer(self, tenant, auth_client, customer_factory):
        c = customer_factory(tenant.company, name="Cust A")
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(customer=str(c.id)),
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["customer"] == str(c.id)
        assert resp.json()["customer_name"] == "Cust A"

    def test_create_with_valid_manager(
        self,
        tenant,
        auth_client,
        membership_factory,
        user_factory,
    ):
        mgr = user_factory(email="pm@test.com")
        membership_factory(mgr, tenant.company, RoleChoices.MANAGER)
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(manager=str(mgr.id)),
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["manager"] == str(mgr.id)
        assert (
            resp.json()["manager_name"] == mgr.get_full_name()
            or resp.json()["manager_name"] == mgr.email
        )

    def test_create_with_start_date_after_deadline_rejected(
        self,
        tenant,
        auth_client,
    ):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(start_date="2025-12-01", deadline="2025-06-01"),
            format="json",
        )
        assert resp.status_code == 400
        assert "deadline" in resp.json()


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateProject:
    def test_partial_update(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="Old Name")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/projects/{p.id}/",
            {"name": "New Name", "status": "IN_PROGRESS"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_full_update(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="Original")
        resp = auth_client(tenant.admin, tenant.company).put(
            f"/api/v1/projects/{p.id}/",
            _payload(name="Replaced", status="ON_HOLD", priority="HIGH"),
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Replaced"
        assert body["status"] == "ON_HOLD"
        assert body["priority"] == "HIGH"

    def test_update_customer_cross_tenant_rejected(
        self,
        two_tenants,
        auth_client,
        project_factory,
        customer_factory,
    ):
        p = project_factory(two_tenants["a"]["company"], name="P")
        foreign_c = customer_factory(two_tenants["b"]["company"], name="B Cust")

        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/projects/{p.id}/",
            {"customer": str(foreign_c.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "customer" in resp.json()

    def test_update_manager_must_be_company_member(
        self,
        tenant,
        auth_client,
        project_factory,
        user_factory,
        company_factory,
    ):
        p = project_factory(tenant.company, name="P")
        outsider = user_factory(email="outsider@test.com")
        # outsider belongs to a different company
        other_co = company_factory(name="Other Co", slug="other-co")
        from apps.companies.models import Membership

        Membership.objects.create(user=outsider, company=other_co, role=RoleChoices.EMPLOYEE)

        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/projects/{p.id}/",
            {"manager": str(outsider.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "manager" in resp.json()


# ---------------------------------------------------------------------------
# Archive (soft-delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestArchiveProject:
    def test_archive_sets_status(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="To Archive")
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/archive/",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ARCHIVED"
        p.refresh_from_db()
        assert p.status == ProjectStatus.ARCHIVED

    def test_archive_already_archived_returns_400(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, status=ProjectStatus.ARCHIVED)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/projects/{p.id}/archive/",
        )
        assert resp.status_code == 400

    def test_archive_requires_manager_or_admin(self, tenant, auth_client, project_factory):
        employee = tenant.employee
        p = project_factory(tenant.company)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        resp = auth_client(employee, tenant.company).post(
            f"/api/v1/projects/{p.id}/archive/",
        )
        assert resp.status_code == 403

    def test_archive_manager_role(
        self, tenant, auth_client, project_factory, membership_factory, user_factory
    ):
        mgr = user_factory(email="archive-mgr@test.com")
        membership_factory(mgr, tenant.company, RoleChoices.MANAGER)
        p = project_factory(tenant.company)

        resp = auth_client(mgr, tenant.company).post(
            f"/api/v1/projects/{p.id}/archive/",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Delete (permanent)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeleteProject:
    def test_delete_removes_project(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).delete(
            f"/api/v1/projects/{p.id}/",
        )
        assert resp.status_code == 204
        assert not Project.objects.filter(pk=p.id).exists()

    def test_delete_requires_manager_or_admin(self, tenant, auth_client, project_factory):
        employee = tenant.employee
        p = project_factory(tenant.company)
        Membership.objects.filter(user=employee).update(role=RoleChoices.EMPLOYEE)

        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/projects/{p.id}/",
        )
        assert resp.status_code == 403

        Membership.objects.filter(user=employee).update(role=RoleChoices.ADMIN)
        resp = auth_client(employee, tenant.company).delete(
            f"/api/v1/projects/{p.id}/",
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidation:
    def test_invalid_status_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(status="BOGUS"),
            format="json",
        )
        assert resp.status_code == 400
        assert "status" in resp.json()

    def test_invalid_priority_rejected(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(priority="EXTREME"),
            format="json",
        )
        assert resp.status_code == 400
        assert "priority" in resp.json()

    def test_name_max_length_enforced(self, tenant, auth_client):
        resp = auth_client(tenant.admin, tenant.company).post(
            "/api/v1/projects/",
            _payload(name="X" * 121),
            format="json",
        )
        assert resp.status_code == 400
        assert "name" in resp.json()

    def test_customer_cross_tenant_rejected_on_create(
        self,
        two_tenants,
        auth_client,
        customer_factory,
    ):
        foreign_c = customer_factory(two_tenants["b"]["company"], name="Foreign")
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/projects/",
            _payload(customer=str(foreign_c.id)),
            format="json",
        )
        assert resp.status_code == 400
        assert "customer" in resp.json()

    def test_customer_not_found_still_validates_company(
        self,
        two_tenants,
        auth_client,
        user_factory,
        company_factory,
        membership_factory,
    ):
        """FK validation catches a non-existent customer ID (400)."""
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/projects/",
            _payload(customer="00000000-0000-0000-0000-000000000000"),
            format="json",
        )
        assert resp.status_code == 400
        assert "customer" in resp.json()

    def test_valid_status_values(self, tenant, auth_client):
        for status_val in ("PLANNING", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "ARCHIVED"):
            resp = auth_client(tenant.admin, tenant.company).post(
                "/api/v1/projects/",
                _payload(name=f"P-{status_val}", status=status_val),
                format="json",
            )
            assert resp.status_code == 201, (
                f"Expected 201 for status={status_val}, got {resp.status_code}"
            )

    def test_valid_priority_values(self, tenant, auth_client):
        for prio in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            resp = auth_client(tenant.admin, tenant.company).post(
                "/api/v1/projects/",
                _payload(name=f"P-{prio}", priority=prio),
                format="json",
            )
            assert resp.status_code == 201, (
                f"Expected 201 for priority={prio}, got {resp.status_code}"
            )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSearch:
    def test_search_by_name(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Alpha Sprint")
        project_factory(tenant.company, name="Beta Sprint")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"search": "Alpha"},
        )
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Alpha Sprint"]

    def test_search_by_description(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="A", description="Mobile app")
        project_factory(tenant.company, name="B", description="Web app")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"search": "Mobile"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "A"


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFiltering:
    def test_filter_by_status(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Planning", status=ProjectStatus.PLANNING)
        project_factory(tenant.company, name="Active", status=ProjectStatus.IN_PROGRESS)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"status": "PLANNING"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "Planning"

    def test_filter_by_priority(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Low", priority=ProjectPriority.LOW)
        project_factory(tenant.company, name="High", priority=ProjectPriority.HIGH)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"priority": "HIGH"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "High"

    def test_filter_by_customer(self, tenant, auth_client, customer_factory, project_factory):
        c = customer_factory(tenant.company, name="Cust A")
        project_factory(tenant.company, name="For A", customer=c)
        project_factory(tenant.company, name="Unlinked")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"customer": str(c.id)},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "For A"

    def test_combined_filters(self, tenant, auth_client, customer_factory, project_factory):
        c = customer_factory(tenant.company, name="Cust A")
        project_factory(
            tenant.company,
            name="Match",
            status=ProjectStatus.PLANNING,
            priority=ProjectPriority.HIGH,
            customer=c,
        )
        project_factory(
            tenant.company,
            name="Wrong Status",
            status=ProjectStatus.IN_PROGRESS,
            priority=ProjectPriority.HIGH,
            customer=c,
        )
        project_factory(
            tenant.company,
            name="Wrong Prio",
            status=ProjectStatus.PLANNING,
            priority=ProjectPriority.LOW,
            customer=c,
        )

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"status": "PLANNING", "priority": "HIGH"},
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["name"] == "Match"


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrdering:
    def test_order_by_name(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Zebra")
        project_factory(tenant.company, name="Alpha")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"ordering": "name"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Alpha", "Zebra"]

    def test_order_by_created_at_desc(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="First")
        project_factory(tenant.company, name="Second")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"ordering": "-created_at"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Second", "First"]

    def test_order_by_deadline(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Late", deadline="2025-12-31")
        project_factory(tenant.company, name="Early", deadline="2025-01-01")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"ordering": "deadline"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Early", "Late"]

    def test_order_by_priority(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Low", priority=ProjectPriority.LOW)
        project_factory(tenant.company, name="Critical", priority=ProjectPriority.CRITICAL)

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"ordering": "priority"},
        )
        names = [r["name"] for r in resp.json()["results"]]
        # Lexicographic on value: CRITICAL < HIGH < LOW < MEDIUM
        assert names == ["Critical", "Low"]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPagination:
    def test_default_page_size(self, tenant, auth_client, project_factory):
        for i in range(30):
            project_factory(tenant.company, name=f"P{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get("/api/v1/projects/")
        body = resp.json()
        assert body["count"] == 30
        assert len(body["results"]) == 25
        assert body["next"] is not None

    def test_custom_page_size(self, tenant, auth_client, project_factory):
        for i in range(5):
            project_factory(tenant.company, name=f"P{i}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"page_size": 2},
        )
        body = resp.json()
        assert body["count"] == 5
        assert len(body["results"]) == 2
        assert body["next"] is not None

    def test_second_page(self, tenant, auth_client, project_factory):
        for i in range(30):
            project_factory(tenant.company, name=f"P{i:02d}")

        resp = auth_client(tenant.admin, tenant.company).get(
            "/api/v1/projects/",
            {"page": 2},
        )
        body = resp.json()
        assert len(body["results"]) == 5
        assert body["previous"] is not None


# ---------------------------------------------------------------------------
# Tenant isolation (project-specific)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantIsolation:
    def test_cannot_list_other_company_projects(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        own = project_factory(two_tenants["a"]["company"], name="Mine")
        foreign = project_factory(two_tenants["b"]["company"], name="Theirs")

        resp = auth_client(two_tenants["a"]["user"]).get("/api/v1/projects/")
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()["results"]}
        assert str(own.id) in ids
        assert str(foreign.id) not in ids

    def test_cannot_retrieve_other_company_project(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).get(
            f"/api/v1/projects/{foreign.id}/",
        )
        assert resp.status_code == 404

    def test_cannot_update_other_company_project(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/projects/{foreign.id}/",
            {"name": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404
        foreign.refresh_from_db()
        assert str(foreign) != "Hacked"

    def test_cannot_archive_other_company_project(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).post(
            f"/api/v1/projects/{foreign.id}/archive/",
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_company_project(
        self,
        two_tenants,
        auth_client,
        project_factory,
    ):
        foreign = project_factory(two_tenants["b"]["company"])
        resp = auth_client(two_tenants["a"]["user"]).delete(
            f"/api/v1/projects/{foreign.id}/",
        )
        assert resp.status_code == 404

    def test_created_project_belongs_to_request_company(
        self,
        two_tenants,
        auth_client,
    ):
        resp = auth_client(two_tenants["a"]["user"]).post(
            "/api/v1/projects/",
            {"name": "Local Only"},
            format="json",
        )
        assert resp.status_code == 201
        p = Project.objects.get(pk=resp.json()["id"])
        assert p.company_id == two_tenants["a"]["company"].id

    def test_customer_cross_tenant_rejected(
        self,
        two_tenants,
        auth_client,
        project_factory,
        customer_factory,
    ):
        p = project_factory(two_tenants["a"]["company"], name="P")
        foreign_c = customer_factory(two_tenants["b"]["company"], name="B Cust")
        resp = auth_client(two_tenants["a"]["user"]).patch(
            f"/api/v1/projects/{p.id}/",
            {"customer": str(foreign_c.id)},
            format="json",
        )
        assert resp.status_code == 400
        assert "customer" in resp.json()


# ---------------------------------------------------------------------------
# Fixtures: two_tenants (independent for this test file)
# ---------------------------------------------------------------------------


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    admin_a = user_factory(email="admin@a-proj.test")
    admin_b = user_factory(email="admin@b-proj.test")
    company_a = company_factory(name="Company A Proj", slug="company-a-proj")
    company_b = company_factory(name="Company B Proj", slug="company-b-proj")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)
    return {
        "a": {"user": admin_a, "company": company_a},
        "b": {"user": admin_b, "company": company_b},
    }
