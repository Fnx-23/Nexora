"""API tests for Business Reporting and Exports: endpoints, permissions, isolation, CSV."""

from datetime import date, time

import pytest
from apps.companies.models import RoleChoices
from apps.projects.models import ProjectStatus
from apps.tasks.models import TaskStatus
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestReportsEndpoints:
    def test_project_performance_api(self, tenant, auth_client, project_factory, task_factory):
        proj = project_factory(tenant.company, name="Alpha", status=ProjectStatus.IN_PROGRESS)
        task_factory(tenant.company, title="T1", project=proj, status=TaskStatus.DONE)

        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/project-performance/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "summary" in data
        assert "results" in data
        assert "status_distribution" in data
        assert data["summary"]["total_projects"] == 1
        assert data["results"][0]["project_name"] == "Alpha"

    def test_team_workload_api(self, tenant, auth_client, project_factory, task_factory):
        proj = project_factory(tenant.company, name="Beta")
        task_factory(tenant.company, title="T1", project=proj, assignee=tenant.admin)

        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/team-workload/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "summary" in data
        assert "results" in data
        assert data["summary"]["total_members"] == 2
        admin_row = next(r for r in data["results"] if r["user_id"] == str(tenant.admin.id))
        assert admin_row["assigned_tasks"] == 1

    def test_time_report_api(self, tenant, auth_client, project_factory, time_entry_factory):
        proj = project_factory(tenant.company, name="Gamma")
        time_entry_factory(
            tenant.company,
            tenant.admin,
            proj,
            date=date(2025, 6, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/time/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["summary"]["total_hours"] == 2.0
        assert len(data["hours_by_project"]) == 1
        assert len(data["hours_by_user"]) == 1

    def test_customer_overview_api(self, tenant, auth_client, customer_factory, project_factory):
        cust = customer_factory(tenant.company, name="Customer One", company_name="One Inc")
        project_factory(
            tenant.company, name="Delivery", customer=cust, status=ProjectStatus.IN_PROGRESS
        )

        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/customer-overview/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["summary"]["total_customers"] == 1
        assert data["results"][0]["customer_name"] == "Customer One"
        assert data["results"][0]["active_projects"] == 1

    def test_executive_summary_api(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/summary/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "project_performance" in data
        assert "team_workload" in data
        assert "time_report" in data
        assert "customer_overview" in data


class TestReportsExports:
    def test_project_performance_csv_export(self, tenant, auth_client, project_factory):
        project_factory(tenant.company, name="Project Export Test")
        client = auth_client(tenant.admin, tenant.company)

        # Via dedicated export endpoint
        resp = client.get("/api/v1/reports/project-performance/export/")
        assert resp.status_code == status.HTTP_200_OK
        assert "text/csv" in resp.headers["Content-Type"]
        assert 'attachment; filename="project-performance-' in resp.headers["Content-Disposition"]
        content = resp.content.decode("utf-8-sig")
        assert "Project Name" in content
        assert "Project Export Test" in content

        # Via ?export=csv parameter
        resp2 = client.get("/api/v1/reports/project-performance/?export=csv")
        assert resp2.status_code == status.HTTP_200_OK
        assert "text/csv" in resp2.headers["Content-Type"]

    def test_team_workload_csv_export(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/team-workload/export/")
        assert resp.status_code == status.HTTP_200_OK
        assert "text/csv" in resp.headers["Content-Type"]
        content = resp.content.decode("utf-8-sig")
        assert "Team Member" in content
        assert tenant.admin.email in content

    def test_time_report_csv_export(self, tenant, auth_client, project_factory, time_entry_factory):
        proj = project_factory(tenant.company, name="Time Test Project")
        time_entry_factory(tenant.company, tenant.admin, proj, description="Testing CSV output")

        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/time/export/")
        assert resp.status_code == status.HTTP_200_OK
        assert "text/csv" in resp.headers["Content-Type"]
        content = resp.content.decode("utf-8-sig")
        assert "Date" in content
        assert "Time Test Project" in content
        assert "Testing CSV output" in content

    def test_customer_overview_csv_export(self, tenant, auth_client, customer_factory):
        customer_factory(tenant.company, name="Exported Customer", company_name="Export Co")
        client = auth_client(tenant.admin, tenant.company)
        resp = client.get("/api/v1/reports/customer-overview/export/")
        assert resp.status_code == status.HTTP_200_OK
        assert "text/csv" in resp.headers["Content-Type"]
        content = resp.content.decode("utf-8-sig")
        assert "Customer / Contact" in content
        assert "Exported Customer" in content
        assert "Export Co" in content


class TestReportsTenantIsolation:
    def test_tenant_isolation_projects_and_customers(
        self,
        tenant,
        user_factory,
        company_factory,
        membership_factory,
        customer_factory,
        project_factory,
        auth_client,
    ):
        # Company A (tenant)
        project_factory(tenant.company, name="Company A Project")
        customer_factory(tenant.company, name="Company A Customer")

        # Company B
        user_b = user_factory(email="user@companyb.test")
        company_b = company_factory(name="Company B", slug="company-b")
        membership_factory(user_b, company_b, RoleChoices.ADMIN)
        project_factory(company_b, name="Company B Secret Project")
        customer_factory(company_b, name="Company B Secret Customer")

        # User A calls reports
        client_a = auth_client(tenant.admin, tenant.company)

        # 1. Project performance report
        resp_p = client_a.get("/api/v1/reports/project-performance/")
        assert resp_p.status_code == status.HTTP_200_OK
        project_names = [p["project_name"] for p in resp_p.json()["results"]]
        assert "Company A Project" in project_names
        assert "Company B Secret Project" not in project_names

        # 2. Customer overview report
        resp_c = client_a.get("/api/v1/reports/customer-overview/")
        assert resp_c.status_code == status.HTTP_200_OK
        cust_names = [c["customer_name"] for c in resp_c.json()["results"]]
        assert "Company A Customer" in cust_names
        assert "Company B Secret Customer" not in cust_names

    def test_tenant_isolation_time_and_workload(
        self,
        tenant,
        user_factory,
        company_factory,
        membership_factory,
        project_factory,
        time_entry_factory,
        task_factory,
        auth_client,
    ):
        p_a = project_factory(tenant.company, name="Proj A")
        time_entry_factory(
            tenant.company,
            tenant.admin,
            p_a,
            date=date(2025, 6, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        # Company B
        user_b = user_factory(email="user_b@companyb.test")
        company_b = company_factory(name="Company B", slug="company-b-2")
        membership_factory(user_b, company_b, RoleChoices.ADMIN)
        p_b = project_factory(company_b, name="Proj B")
        time_entry_factory(
            company_b,
            user_b,
            p_b,
            date=date(2025, 6, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )  # 8h
        task_factory(company_b, title="Secret B Task", project=p_b, assignee=user_b)

        client_a = auth_client(tenant.admin, tenant.company)

        # Time report: tenant A only sees 2 hours, not 8 hours from B
        resp_t = client_a.get("/api/v1/reports/time/")
        assert resp_t.status_code == status.HTTP_200_OK
        assert resp_t.json()["summary"]["total_hours"] == 2.0
        assert "Proj B" not in [x["project_name"] for x in resp_t.json()["hours_by_project"]]

        # Team workload: tenant A only sees members of tenant A
        resp_w = client_a.get("/api/v1/reports/team-workload/")
        assert resp_w.status_code == status.HTTP_200_OK
        user_ids = [m["user_id"] for m in resp_w.json()["results"]]
        assert str(user_b.id) not in user_ids


class TestReportsPermissions:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/v1/reports/project-performance/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_without_company_returns_403(self, api_client, user_factory):
        user_no_company = user_factory(email="lonely@example.com")
        api_client.force_authenticate(user=user_no_company)
        resp = api_client.get("/api/v1/reports/project-performance/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_inactive_membership_returns_403(
        self,
        api_client,
        user_factory,
        company_factory,
        membership_factory,
    ):
        user = user_factory(email="inactive@example.com")
        company = company_factory()
        membership_factory(user, company, RoleChoices.EMPLOYEE, is_active=False)

        api_client.force_authenticate(user=user)
        api_client.credentials(HTTP_X_COMPANY_ID=str(company.id))
        resp = api_client.get("/api/v1/reports/project-performance/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_and_admin_both_can_access(self, tenant, auth_client):
        # Admin access
        client_admin = auth_client(tenant.admin, tenant.company)
        resp_admin = client_admin.get("/api/v1/reports/project-performance/")
        assert resp_admin.status_code == status.HTTP_200_OK

        # Employee access
        client_emp = auth_client(tenant.employee, tenant.company)
        resp_emp = client_emp.get("/api/v1/reports/project-performance/")
        assert resp_emp.status_code == status.HTTP_200_OK
