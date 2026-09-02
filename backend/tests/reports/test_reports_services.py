"""Unit and integration tests for Business Reporting services."""

from datetime import date, time, timedelta

import pytest
from apps.customers.models import CustomerStatus
from apps.projects.models import ProjectStatus
from apps.reports.services import (
    get_customer_overview_report,
    get_executive_summary,
    get_project_performance_report,
    get_team_workload_report,
    get_time_report,
)
from apps.tasks.models import TaskStatus
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestProjectPerformanceReport:
    def test_calculation_accuracy(
        self,
        tenant,
        customer_factory,
        project_factory,
        task_factory,
        time_entry_factory,
    ):
        company = tenant.company
        customer = customer_factory(company, name="Acme Corp", company_name="Acme International")
        project = project_factory(
            company, name="Website Redesign", customer=customer, manager=tenant.admin
        )

        today = timezone.localdate()

        # Tasks: 2 DONE, 1 IN_PROGRESS, 1 TODO (overdue), 1 TODO (future)
        task_factory(company, title="Task 1", project=project, status=TaskStatus.DONE)
        task_factory(company, title="Task 2", project=project, status=TaskStatus.DONE)
        task_factory(company, title="Task 3", project=project, status=TaskStatus.IN_PROGRESS)
        task_factory(
            company,
            title="Task 4 Overdue",
            project=project,
            status=TaskStatus.TODO,
            due_date=today - timedelta(days=2),
        )
        task_factory(
            company,
            title="Task 5 Future",
            project=project,
            status=TaskStatus.TODO,
            due_date=today + timedelta(days=5),
        )

        # Time entries: 2h 30m (2.5h) and 1h 45m (1.75h) => 4.25h
        time_entry_factory(
            company,
            tenant.admin,
            project,
            date=today,
            start_time=time(9, 0),
            end_time=time(11, 30),
        )
        time_entry_factory(
            company,
            tenant.employee,
            project,
            date=today,
            start_time=time(13, 0),
            end_time=time(14, 45),
        )

        report = get_project_performance_report(company)

        assert report["summary"]["total_projects"] == 1
        assert report["summary"]["total_tasks"] == 5
        assert report["summary"]["total_completed_tasks"] == 2
        assert report["summary"]["total_open_tasks"] == 3
        assert report["summary"]["total_overdue_tasks"] == 1
        assert report["summary"]["total_tracked_hours"] == 4.25
        # Progress: 2 / 5 = 40%
        assert report["summary"]["average_progress"] == 40.0

        p_result = report["results"][0]
        assert p_result["project_id"] == str(project.id)
        assert p_result["project_name"] == "Website Redesign"
        assert p_result["progress"] == 40
        assert p_result["completed_tasks"] == 2
        assert p_result["open_tasks"] == 3
        assert p_result["total_tasks"] == 5
        assert p_result["overdue_tasks"] == 1
        assert p_result["tracked_hours"] == 4.25
        assert p_result["customer_name"] == "Acme International"

    def test_project_filters(
        self,
        tenant,
        customer_factory,
        project_factory,
        task_factory,
        time_entry_factory,
    ):
        company = tenant.company
        c1 = customer_factory(company, name="Customer 1")
        c2 = customer_factory(company, name="Customer 2")

        p1 = project_factory(
            company, name="Project Alpha", customer=c1, status=ProjectStatus.IN_PROGRESS
        )
        p2 = project_factory(
            company, name="Project Beta", customer=c2, status=ProjectStatus.COMPLETED
        )

        today = timezone.localdate()
        time_entry_factory(
            company,
            tenant.admin,
            p1,
            date=today - timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(11, 0),  # 2.0h
        )
        time_entry_factory(
            company,
            tenant.admin,
            p2,
            date=today,
            start_time=time(9, 0),
            end_time=time(12, 0),  # 3.0h
        )

        # Filter by project
        rep_p1 = get_project_performance_report(company, {"project": str(p1.id)})
        assert rep_p1["summary"]["total_projects"] == 1
        assert rep_p1["results"][0]["project_id"] == str(p1.id)

        # Filter by customer
        rep_c2 = get_project_performance_report(company, {"customer": str(c2.id)})
        assert rep_c2["summary"]["total_projects"] == 1
        assert rep_c2["results"][0]["project_name"] == "Project Beta"

        # Filter by status
        rep_status = get_project_performance_report(company, {"status": ProjectStatus.COMPLETED})
        assert rep_status["summary"]["total_projects"] == 1
        assert rep_status["results"][0]["status"] == ProjectStatus.COMPLETED

        # Filter by date_from
        rep_date = get_project_performance_report(
            company,
            {"date_from": (today - timedelta(days=1)).isoformat()},
        )
        # P1 tracked hours should be 0 in this range, P2 should have 3.0h
        p1_item = next(x for x in rep_date["results"] if x["project_id"] == str(p1.id))
        p2_item = next(x for x in rep_date["results"] if x["project_id"] == str(p2.id))
        assert p1_item["tracked_hours"] == 0.0
        assert p2_item["tracked_hours"] == 3.0


class TestTeamWorkloadReport:
    def test_calculation_accuracy(
        self,
        tenant,
        project_factory,
        task_factory,
        time_entry_factory,
    ):
        company = tenant.company
        project = project_factory(company, name="Core App")
        today = timezone.localdate()

        # Admin: 3 tasks (1 DONE, 1 IN_PROGRESS, 1 TODO overdue)
        task_factory(
            company, title="A1", project=project, assignee=tenant.admin, status=TaskStatus.DONE
        )
        task_factory(
            company,
            title="A2",
            project=project,
            assignee=tenant.admin,
            status=TaskStatus.IN_PROGRESS,
        )
        task_factory(
            company,
            title="A3",
            project=project,
            assignee=tenant.admin,
            status=TaskStatus.TODO,
            due_date=today - timedelta(days=1),
        )

        # Employee: 2 tasks (2 DONE)
        task_factory(
            company, title="E1", project=project, assignee=tenant.employee, status=TaskStatus.DONE
        )
        task_factory(
            company, title="E2", project=project, assignee=tenant.employee, status=TaskStatus.DONE
        )

        # Time: Admin logs 3 hours, Employee logs 5 hours
        time_entry_factory(
            company,
            tenant.admin,
            project,
            date=today,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        time_entry_factory(
            company,
            tenant.employee,
            project,
            date=today,
            start_time=time(9, 0),
            end_time=time(14, 0),
        )

        report = get_team_workload_report(company)

        assert report["summary"]["total_members"] == 2
        assert report["summary"]["total_assigned_tasks"] == 5
        assert report["summary"]["total_completed_tasks"] == 3
        assert report["summary"]["total_open_tasks"] == 2
        assert report["summary"]["total_overdue_tasks"] == 1
        assert report["summary"]["total_tracked_hours"] == 8.0
        # Completion rate: 3/5 = 60%
        assert report["summary"]["overall_completion_rate"] == 60

        admin_row = next(r for r in report["results"] if r["user_id"] == str(tenant.admin.id))
        assert admin_row["assigned_tasks"] == 3
        assert admin_row["completed_tasks"] == 1
        assert admin_row["open_tasks"] == 2
        assert admin_row["overdue_tasks"] == 1
        assert admin_row["tracked_hours"] == 3.0
        assert admin_row["completion_rate"] == 33  # 1/3 = 33%

        employee_row = next(r for r in report["results"] if r["user_id"] == str(tenant.employee.id))
        assert employee_row["assigned_tasks"] == 2
        assert employee_row["completed_tasks"] == 2
        assert employee_row["open_tasks"] == 0
        assert employee_row["overdue_tasks"] == 0
        assert employee_row["tracked_hours"] == 5.0
        assert employee_row["completion_rate"] == 100

    def test_team_workload_filters(
        self,
        tenant,
        project_factory,
        task_factory,
    ):
        company = tenant.company
        p1 = project_factory(company, name="Project 1")
        p2 = project_factory(company, name="Project 2")

        task_factory(company, title="T1", project=p1, assignee=tenant.admin)
        task_factory(company, title="T2", project=p2, assignee=tenant.admin)

        # Filter by project
        rep_p1 = get_team_workload_report(company, {"project": str(p1.id)})
        admin_row = next(r for r in rep_p1["results"] if r["user_id"] == str(tenant.admin.id))
        assert admin_row["assigned_tasks"] == 1

        # Filter by user
        rep_user = get_team_workload_report(company, {"user": str(tenant.admin.id)})
        assert len(rep_user["results"]) == 1
        assert rep_user["results"][0]["user_id"] == str(tenant.admin.id)


class TestTimeReport:
    def test_calculation_accuracy(
        self,
        tenant,
        customer_factory,
        project_factory,
        time_entry_factory,
    ):
        company = tenant.company
        cust = customer_factory(company, name="TechCorp", company_name="TechCorp Inc")
        p1 = project_factory(company, name="Cloud Migration", customer=cust)
        p2 = project_factory(company, name="Mobile App")

        d1 = date(2025, 6, 1)
        d2 = date(2025, 6, 2)

        # Entry 1: Admin, P1, 2.5 hours
        time_entry_factory(
            company,
            tenant.admin,
            p1,
            date=d1,
            start_time=time(9, 0),
            end_time=time(11, 30),
            description="VPC setup",
        )
        # Entry 2: Employee, P1, 1.5 hours
        time_entry_factory(
            company,
            tenant.employee,
            p1,
            date=d1,
            start_time=time(13, 0),
            end_time=time(14, 30),
            description="RDS config",
        )
        # Entry 3: Employee, P2, 3.0 hours
        time_entry_factory(
            company,
            tenant.employee,
            p2,
            date=d2,
            start_time=time(10, 0),
            end_time=time(13, 0),
            description="App screens",
        )

        report = get_time_report(company)

        # Total hours: 2.5 + 1.5 + 3.0 = 7.0
        assert report["summary"]["total_hours"] == 7.0
        assert report["summary"]["total_entries"] == 3
        assert report["summary"]["active_projects_count"] == 2
        assert report["summary"]["active_users_count"] == 2
        assert report["summary"]["days_with_activity"] == 2

        # Hours by project
        p1_stats = next(p for p in report["hours_by_project"] if p["project_id"] == str(p1.id))
        assert p1_stats["hours"] == 4.0
        assert p1_stats["entry_count"] == 2
        assert p1_stats["percentage"] == 57.1  # 4/7 = 57.1%
        assert p1_stats["customer_name"] == "TechCorp Inc"

        p2_stats = next(p for p in report["hours_by_project"] if p["project_id"] == str(p2.id))
        assert p2_stats["hours"] == 3.0
        assert p2_stats["entry_count"] == 1
        assert p2_stats["percentage"] == 42.9

        # Hours by user
        emp_stats = next(
            u for u in report["hours_by_user"] if u["user_id"] == str(tenant.employee.id)
        )
        assert emp_stats["hours"] == 4.5  # 1.5 + 3.0 = 4.5
        assert emp_stats["entry_count"] == 2

        admin_stats = next(
            u for u in report["hours_by_user"] if u["user_id"] == str(tenant.admin.id)
        )
        assert admin_stats["hours"] == 2.5
        assert admin_stats["entry_count"] == 1

        # Timeline
        assert len(report["timeline"]) == 2
        assert report["timeline"][0]["date"] == "2025-06-01"
        assert report["timeline"][0]["hours"] == 4.0
        assert report["timeline"][1]["date"] == "2025-06-02"
        assert report["timeline"][1]["hours"] == 3.0

    def test_time_report_filters(
        self,
        tenant,
        customer_factory,
        project_factory,
        time_entry_factory,
    ):
        company = tenant.company
        c1 = customer_factory(company, name="C1")
        p1 = project_factory(company, name="P1", customer=c1)
        p2 = project_factory(company, name="P2")

        d1 = date(2025, 6, 1)
        d2 = date(2025, 6, 15)

        time_entry_factory(
            company, tenant.admin, p1, date=d1, start_time=time(9, 0), end_time=time(11, 0)
        )
        time_entry_factory(
            company, tenant.employee, p2, date=d2, start_time=time(9, 0), end_time=time(12, 0)
        )

        # Date range filter
        rep_date = get_time_report(company, {"date_from": "2025-06-10", "date_to": "2025-06-20"})
        assert rep_date["summary"]["total_hours"] == 3.0
        assert rep_date["summary"]["total_entries"] == 1

        # User filter
        rep_user = get_time_report(company, {"user": str(tenant.admin.id)})
        assert rep_user["summary"]["total_hours"] == 2.0
        assert rep_user["summary"]["active_users_count"] == 1

        # Customer filter
        rep_cust = get_time_report(company, {"customer": str(c1.id)})
        assert rep_cust["summary"]["total_hours"] == 2.0
        assert rep_cust["hours_by_project"][0]["project_id"] == str(p1.id)


class TestCustomerOverviewReport:
    def test_calculation_accuracy(
        self,
        tenant,
        customer_factory,
        project_factory,
        task_factory,
        time_entry_factory,
    ):
        company = tenant.company
        c1 = customer_factory(
            company, name="Alice", company_name="Alice Media", status=CustomerStatus.ACTIVE
        )
        c2 = customer_factory(
            company, name="Bob", company_name="Bob Logistics", status=CustomerStatus.INACTIVE
        )

        # C1 has 1 IN_PROGRESS, 1 PLANNING, 1 COMPLETED project
        p1 = project_factory(company, name="Site", customer=c1, status=ProjectStatus.IN_PROGRESS)
        project_factory(company, name="Marketing", customer=c1, status=ProjectStatus.PLANNING)
        project_factory(company, name="Branding", customer=c1, status=ProjectStatus.COMPLETED)

        # C2 has 1 COMPLETED project
        p4 = project_factory(
            company, name="Shipping API", customer=c2, status=ProjectStatus.COMPLETED
        )

        # Tasks on C1
        task_factory(company, title="Design", project=p1, status=TaskStatus.TODO)
        task_factory(company, title="Code", project=p1, status=TaskStatus.IN_PROGRESS)
        task_factory(company, title="Deploy", project=p1, status=TaskStatus.DONE)

        # Time on C1: 6 hours; on C2: 4 hours
        time_entry_factory(
            company,
            tenant.admin,
            p1,
            date=date(2025, 6, 1),
            start_time=time(9, 0),
            end_time=time(15, 0),
        )
        time_entry_factory(
            company,
            tenant.employee,
            p4,
            date=date(2025, 6, 1),
            start_time=time(10, 0),
            end_time=time(14, 0),
        )

        report = get_customer_overview_report(company)

        assert report["summary"]["total_customers"] == 2
        assert report["summary"]["active_customers"] == 1
        assert report["summary"]["total_active_projects"] == 2  # PLANNING + IN_PROGRESS
        assert report["summary"]["total_completed_projects"] == 2  # p3 and p4
        assert report["summary"]["total_tracked_hours"] == 10.0

        c1_item = next(c for c in report["results"] if c["customer_id"] == str(c1.id))
        assert c1_item["active_projects"] == 2
        assert c1_item["completed_projects"] == 1
        assert c1_item["total_projects"] == 3
        assert c1_item["open_tasks"] == 2  # TODO + IN_PROGRESS
        assert c1_item["hours_tracked"] == 6.0

        c2_item = next(c for c in report["results"] if c["customer_id"] == str(c2.id))
        assert c2_item["active_projects"] == 0
        assert c2_item["completed_projects"] == 1
        assert c2_item["hours_tracked"] == 4.0

    def test_customer_filters(
        self,
        tenant,
        customer_factory,
    ):
        company = tenant.company
        c1 = customer_factory(company, name="Alpha", status=CustomerStatus.ACTIVE)
        customer_factory(company, name="Beta", status=CustomerStatus.INACTIVE)

        # Filter by customer ID
        rep_id = get_customer_overview_report(company, {"customer": str(c1.id)})
        assert rep_id["summary"]["total_customers"] == 1
        assert rep_id["results"][0]["customer_id"] == str(c1.id)

        # Filter by status
        rep_active = get_customer_overview_report(company, {"status": CustomerStatus.ACTIVE})
        assert rep_active["summary"]["total_customers"] == 1
        assert rep_active["results"][0]["status"] == CustomerStatus.ACTIVE


class TestExecutiveSummary:
    def test_executive_summary_combines_modules(
        self,
        tenant,
        customer_factory,
        project_factory,
        task_factory,
        time_entry_factory,
    ):
        company = tenant.company
        cust = customer_factory(company, name="Client")
        proj = project_factory(
            company, name="Proj", customer=cust, status=ProjectStatus.IN_PROGRESS
        )
        task_factory(company, title="T1", project=proj, status=TaskStatus.DONE)
        time_entry_factory(
            company,
            tenant.admin,
            proj,
            date=date(2025, 6, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        summary = get_executive_summary(company)
        assert "project_performance" in summary
        assert "team_workload" in summary
        assert "time_report" in summary
        assert "customer_overview" in summary
        assert summary["project_performance"]["total_projects"] == 1
        assert summary["time_report"]["total_hours"] == 2.0
