"""Model-level tests for customers."""

import pytest
from apps.customers.models import Customer


@pytest.mark.django_db
def test_customer_defaults_and_str(customer_factory, company_factory):
    company = company_factory()
    customer = customer_factory(company, name="Globex")

    assert str(customer) == "Globex"
    assert customer.is_active is True
    assert customer.email == ""
    assert customer.created_at is not None
    assert customer.updated_at is not None


@pytest.mark.django_db
def test_deleting_company_removes_customers(customer_factory, company_factory):
    company = company_factory(slug="doomed")
    customer_factory(company)

    company.delete()

    assert Customer.objects.count() == 0
