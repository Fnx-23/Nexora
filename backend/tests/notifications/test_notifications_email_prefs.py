"""Email notification preference tests for the Settings > Notifications page."""

import pytest
from apps.companies.models import Membership, RoleChoices
from apps.notifications.models import NotificationPreference

NOTIFICATIONS_URL = "/api/v1/notifications/"
PREFERENCES_URL = f"{NOTIFICATIONS_URL}preferences/"

EMAIL_FIELDS = [
    "email_task_assigned",
    "email_task_comment",
    "email_task_due_soon",
    "email_task_overdue",
    "email_project_assigned",
    "email_project_deadline",
    "email_invitation_received",
    "email_role_changed",
]


@pytest.mark.django_db
def test_email_preferences_default_true(auth_client, tenant):
    resp = auth_client(tenant.employee, tenant.company).get(PREFERENCES_URL)

    assert resp.status_code == 200
    for field in EMAIL_FIELDS:
        assert resp.data[field] is True


@pytest.mark.django_db
def test_patch_disables_email_preference(auth_client, tenant):
    client = auth_client(tenant.employee, tenant.company)
    resp = client.patch(PREFERENCES_URL, {"email_task_overdue": False}, format="json")

    assert resp.status_code == 200
    assert resp.data["email_task_overdue"] is False
    pref = NotificationPreference.objects.get(company=tenant.company, user=tenant.employee)
    assert pref.email_task_overdue is False
    assert pref.email_task_assigned is True


@pytest.mark.django_db
def test_email_preferences_isolated_per_company(auth_client, tenant, company_factory):
    company_b = company_factory(name="Company B", slug="company-email-b")
    Membership.objects.create(user=tenant.employee, company=company_b, role=RoleChoices.EMPLOYEE)
    auth_client(tenant.employee, company_b).patch(
        PREFERENCES_URL, {"email_invitation_received": False}, format="json"
    )

    pref_b = NotificationPreference.objects.get(company=company_b, user=tenant.employee)
    assert pref_b.email_invitation_received is False
    assert (
        NotificationPreference.objects.filter(company=tenant.company, user=tenant.employee).exists()
        is False
    )


@pytest.mark.django_db
def test_unknown_email_preference_is_rejected(auth_client, tenant):
    resp = auth_client(tenant.employee, tenant.company).patch(
        PREFERENCES_URL, {"email_not_a_real_pref": True}, format="json"
    )

    assert resp.status_code == 200
    assert "email_not_a_real_pref" not in resp.data
