"""Shared pytest fixtures for the Nexora backend test suite."""

from types import SimpleNamespace

import pytest
from apps.companies.models import Company, Membership, RoleChoices
from apps.customers.models import Customer
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.time_tracking.models import TimeEntry
from django.core.cache import cache
from django.utils.text import slugify
from rest_framework.test import APIClient

DEFAULT_PASSWORD = "Str0ng-Passw0rd!"


@pytest.fixture(autouse=True)
def _reset_throttle_counters():
    """Start every test with empty rate-limit buckets.

    Throttle counters persist in the cache backend across requests (by design),
    so without this they would leak between tests sharing one minute window.
    """
    cache.clear()
    yield


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_factory(django_user_model):
    def make(email="user@example.com", password=DEFAULT_PASSWORD, **kwargs):
        return django_user_model.objects.create_user(email=email, password=password, **kwargs)

    return make


@pytest.fixture
def company_factory():
    def make(name="Acme Inc", **kwargs):
        kwargs.setdefault("slug", slugify(name))
        return Company.objects.create(name=name, **kwargs)

    return make


@pytest.fixture
def membership_factory():
    def make(user, company, role=RoleChoices.EMPLOYEE, **kwargs):
        return Membership.objects.create(user=user, company=company, role=role, **kwargs)

    return make


@pytest.fixture
def customer_factory():
    def make(company, name="Customer", **kwargs):
        return Customer.objects.create(company=company, name=name, **kwargs)

    return make


@pytest.fixture
def project_factory():
    def make(company, name="Project", customer=None, **kwargs):
        return Project.objects.create(company=company, name=name, customer=customer, **kwargs)

    return make


@pytest.fixture
def task_factory():
    def make(company, title="Task", project=None, assignee=None, **kwargs):
        return Task.objects.create(
            company=company, title=title, project=project, assignee=assignee, **kwargs
        )

    return make


@pytest.fixture
def tenant(user_factory, company_factory, membership_factory) -> SimpleNamespace:
    """A workspace with one ADMIN and one EMPLOYEE member."""
    admin = user_factory(email="admin@acme.test")
    employee = user_factory(email="employee@acme.test")
    company = company_factory(name="Acme Inc", slug="acme")
    membership_factory(admin, company, RoleChoices.ADMIN)
    membership_factory(employee, company, RoleChoices.EMPLOYEE)
    return SimpleNamespace(company=company, admin=admin, employee=employee)


@pytest.fixture
def auth_client(api_client):
    """Authenticate a client as a user within a specific company context."""

    def _auth(user, company=None):
        api_client.force_authenticate(user=user)
        if company is not None:
            api_client.credentials(HTTP_X_COMPANY_ID=str(company.id))
        return api_client

    return _auth


@pytest.fixture
def time_entry_factory():
    def make(company, user, project, task=None, **kwargs):
        from datetime import time

        kwargs.setdefault("date", "2025-06-15")
        kwargs.setdefault("start_time", time(9, 0))
        kwargs.setdefault("end_time", time(10, 0))
        return TimeEntry.objects.create(
            company=company,
            user=user,
            project=project,
            task=task,
            **kwargs,
        )

    return make
