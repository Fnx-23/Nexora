"""Tests for the ``seed_demo`` management command."""

from io import StringIO

import pytest
from apps.accounts.models import User
from apps.activities.models import Activity
from apps.companies.models import Company, Membership
from apps.customers.models import Customer
from apps.notifications.models import Notification
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.time_tracking.models import TimeEntry
from django.core.management import call_command

SEED_COMMAND = "seed_demo"
DEMO_PASSWORD = "demo-2025!"


def _run_seed(stdout=None):
    call_command(SEED_COMMAND, stdout=stdout or StringIO())


@pytest.mark.django_db
class TestSeedCreatesExpectedData:
    """First run of seed_demo should create all demo records."""

    @pytest.fixture(autouse=True)
    def _seed(self):
        _run_seed()

    def test_creates_demo_company(self):
        assert Company.objects.filter(slug="nexora-demo").count() == 1
        company = Company.objects.get(slug="nexora-demo")
        assert company.name == "Nexora Demo"

    def test_creates_four_users(self):
        emails = [
            "admin@nexora.demo",
            "manager@nexora.demo",
            "employee1@nexora.demo",
            "employee2@nexora.demo",
        ]
        for email in emails:
            assert User.objects.filter(email=email).exists(), f"Missing user: {email}"

    def test_creates_four_memberships(self):
        company = Company.objects.get(slug="nexora-demo")
        assert Membership.objects.filter(company=company).count() == 4

    def test_membership_roles(self):
        company = Company.objects.get(slug="nexora-demo")
        role_map = {
            "admin@nexora.demo": "ADMIN",
            "manager@nexora.demo": "MANAGER",
            "employee1@nexora.demo": "EMPLOYEE",
            "employee2@nexora.demo": "EMPLOYEE",
        }
        for email, expected_role in role_map.items():
            user = User.objects.get(email=email)
            assert Membership.objects.get(
                company=company, user=user
            ).role == expected_role

    def test_creates_four_customers(self):
        company = Company.objects.get(slug="nexora-demo")
        names = {
            c.company_name
            for c in Customer.objects.filter(company=company)
        }
        expected = {"Atlas Logistics", "Nova Retail", "Horizon Labs", "Maghreb Digital"}
        assert names == expected

    def test_creates_three_projects(self):
        company = Company.objects.get(slug="nexora-demo")
        assert Project.objects.filter(company=company).count() == 3
        project_names = set(
            Project.objects.filter(company=company).values_list("name", flat=True)
        )
        expected = {
            "Cloud Infrastructure Migration",
            "E-commerce Platform",
            "Internal IT Portal",
        }
        assert project_names == expected

    def test_creates_fifteen_tasks(self):
        company = Company.objects.get(slug="nexora-demo")
        assert Task.objects.filter(company=company).count() == 15

    def test_tasks_cover_all_kanban_states(self):
        company = Company.objects.get(slug="nexora-demo")
        statuses = set(
            Task.objects.filter(company=company).values_list("status", flat=True)
        )
        expected = {"TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"}
        assert statuses == expected

    def test_creates_five_time_entries(self):
        company = Company.objects.get(slug="nexora-demo")
        assert TimeEntry.objects.filter(company=company).count() == 5

    def test_creates_notifications(self):
        company = Company.objects.get(slug="nexora-demo")
        assert Notification.objects.filter(company=company).count() > 0

    def test_creates_activities(self):
        company = Company.objects.get(slug="nexora-demo")
        assert Activity.objects.filter(company=company).count() > 0

    def test_demo_users_can_authenticate(self):
        for spec in [
            {"email": "admin@nexora.demo", "first_name": "Sara"},
            {"email": "manager@nexora.demo", "first_name": "Youssef"},
            {"email": "employee1@nexora.demo", "first_name": "Amina"},
            {"email": "employee2@nexora.demo", "first_name": "Omar"},
        ]:
            user = User.objects.get(email=spec["email"])
            assert user.check_password(DEMO_PASSWORD), f"{spec['email']} password mismatch"
            assert user.first_name == spec["first_name"]


@pytest.mark.django_db
class TestSeedIdempotency:
    """Running seed_demo twice must not create duplicates."""

    def test_second_run_creates_nothing(self):
        _run_seed()
        first_counts = {
            "companies": Company.objects.count(),
            "users": User.objects.count(),
            "memberships": Membership.objects.count(),
            "customers": Customer.objects.count(),
            "projects": Project.objects.count(),
            "tasks": Task.objects.count(),
            "time_entries": TimeEntry.objects.count(),
        }

        _run_seed()

        assert Company.objects.count() == first_counts["companies"]
        assert User.objects.count() == first_counts["users"]
        assert Membership.objects.count() == first_counts["memberships"]
        assert Customer.objects.count() == first_counts["customers"]
        assert Project.objects.count() == first_counts["projects"]
        assert Task.objects.count() == first_counts["tasks"]
        assert TimeEntry.objects.count() == first_counts["time_entries"]

    def test_second_run_preserves_existing_user_email(self):
        _run_seed()
        _run_seed()
        assert User.objects.filter(email="admin@nexora.demo").count() == 1


@pytest.mark.django_db
class TestSeedDoesNotTouchExistingData:
    """Existing records must not be modified or deleted by seed_demo."""

    def test_existing_company_survives(self, company_factory):
        existing = company_factory(name="Acme", slug="acme-existing")
        original_id = existing.id

        _run_seed()

        assert Company.objects.filter(pk=original_id).exists()
        existing.refresh_from_db()
        assert existing.name == "Acme"

    def test_existing_user_survives(self, user_factory):
        existing = user_factory(email="existing@real.test")
        original_id = existing.id

        _run_seed()

        assert User.objects.filter(pk=original_id).exists()
        existing.refresh_from_db()
        assert existing.email == "existing@real.test"
