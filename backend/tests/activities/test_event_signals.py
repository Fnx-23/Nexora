"""Event-creation tests for the activity/audit log.

Every audited business event is exercised here — created through the real API
(so actor attribution is verified end-to-end) or through the ORM where that is
the clearer way to drive a specific transition. Also covered: actor capture,
the "no sensitive data in metadata" guarantee, append-only immutability, and the
reliability contract that a failing audit write never breaks the business op.
"""

import json

import pytest
from apps.activities.models import Activity, ActivityAction, EntityType
from apps.activities.services import record_activity
from apps.companies.models import Membership, RoleChoices
from apps.customers.models import Customer
from apps.tasks.models import TaskStatus


def _one(action, entity_id, company):
    """Fetch the single activity for (action, entity) within a company."""
    return Activity.objects.get(action=action, entity_id=entity_id, company=company)


# --------------------------------------------------------------------------- #
# Customer events
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestCustomerEvents:
    def test_customer_created(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.post("/api/v1/customers/", {"name": "Acme"}, format="json")
        assert resp.status_code == 201

        act = _one(ActivityAction.CUSTOMER_CREATED, resp.json()["id"], tenant.company)
        assert act.entity_type == EntityType.CUSTOMER
        assert act.actor_id == tenant.admin.id

    def test_customer_updated_records_field_names_only(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        cid = client.post("/api/v1/customers/", {"name": "Init"}, format="json").json()["id"]

        resp = client.patch(
            f"/api/v1/customers/{cid}/",
            {"name": "Renamed", "email": "new@example.com"},
            format="json",
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.CUSTOMER_UPDATED, cid, tenant.company)
        assert set(act.metadata["changed_fields"]) >= {"name", "email"}

    def test_customer_archived_is_distinct_from_updated(
        self, tenant, auth_client, customer_factory
    ):
        c = customer_factory(tenant.company)
        resp = auth_client(tenant.admin, tenant.company).post(f"/api/v1/customers/{c.id}/archive/")
        assert resp.status_code == 200

        assert Activity.objects.filter(
            action=ActivityAction.CUSTOMER_ARCHIVED, entity_id=c.id
        ).exists()
        assert not Activity.objects.filter(
            action=ActivityAction.CUSTOMER_UPDATED, entity_id=c.id
        ).exists()


# --------------------------------------------------------------------------- #
# Project events
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestProjectEvents:
    def test_project_created(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.post("/api/v1/projects/", {"name": "Launch"}, format="json")
        assert resp.status_code == 201

        act = _one(ActivityAction.PROJECT_CREATED, resp.json()["id"], tenant.company)
        assert act.entity_type == EntityType.PROJECT
        assert act.actor_id == tenant.admin.id

    def test_project_updated(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="P")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/projects/{p.id}/", {"description": "revised"}, format="json"
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.PROJECT_UPDATED, p.id, tenant.company)
        assert "description" in act.metadata["changed_fields"]

    def test_project_status_changed(self, tenant, auth_client, project_factory):
        p = project_factory(tenant.company, name="P")  # defaults to PLANNING
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/projects/{p.id}/", {"status": "IN_PROGRESS"}, format="json"
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.PROJECT_STATUS_CHANGED, p.id, tenant.company)
        assert act.metadata["old_status"] == "PLANNING"
        assert act.metadata["new_status"] == "IN_PROGRESS"
        # A pure status change must not also masquerade as a generic update.
        assert not Activity.objects.filter(
            action=ActivityAction.PROJECT_UPDATED, entity_id=p.id
        ).exists()


# --------------------------------------------------------------------------- #
# Task events
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestTaskEvents:
    def test_task_created(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        resp = client.post("/api/v1/tasks/", {"title": "Ship it"}, format="json")
        assert resp.status_code == 201

        act = _one(ActivityAction.TASK_CREATED, resp.json()["id"], tenant.company)
        assert act.entity_type == EntityType.TASK
        assert act.actor_id == tenant.admin.id

    def test_task_assigned(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T")
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/tasks/{t.id}/", {"assignee": str(tenant.employee.id)}, format="json"
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.TASK_ASSIGNED, t.id, tenant.company)
        assert act.metadata["new_assignee_id"] == str(tenant.employee.id)

    def test_task_status_changed(self, tenant, auth_client, task_factory):
        t = task_factory(tenant.company, title="T", assignee=tenant.admin)
        resp = auth_client(tenant.admin, tenant.company).post(
            f"/api/v1/tasks/{t.id}/change-status/", {"status": "IN_PROGRESS"}, format="json"
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.TASK_STATUS_CHANGED, t.id, tenant.company)
        assert act.metadata["old_status"] == "TODO"
        assert act.metadata["new_status"] == "IN_PROGRESS"

    def test_single_save_emits_both_assigned_and_status(self, tenant, task_factory):
        # Assignment and status change are distinct listed events; one save that
        # touches both must record both.
        t = task_factory(tenant.company, title="T")
        t.assignee = tenant.employee
        t.status = TaskStatus.DONE
        t.save()

        assert (
            Activity.objects.filter(action=ActivityAction.TASK_ASSIGNED, entity_id=t.id).count()
            == 1
        )
        assert (
            Activity.objects.filter(
                action=ActivityAction.TASK_STATUS_CHANGED, entity_id=t.id
            ).count()
            == 1
        )


# --------------------------------------------------------------------------- #
# Team role change
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestTeamRoleEvents:
    def test_team_role_changed(self, tenant, auth_client):
        membership = Membership.objects.get(user=tenant.employee, company=tenant.company)
        resp = auth_client(tenant.admin, tenant.company).patch(
            f"/api/v1/companies/members/{membership.id}/role/",
            {"role": "MANAGER"},
            format="json",
        )
        assert resp.status_code == 200

        act = _one(ActivityAction.TEAM_ROLE_CHANGED, membership.id, tenant.company)
        assert act.entity_type == EntityType.MEMBERSHIP
        assert act.actor_id == tenant.admin.id
        assert act.metadata["old_role"] == RoleChoices.EMPLOYEE
        assert act.metadata["new_role"] == RoleChoices.MANAGER

    def test_membership_creation_is_not_audited(self, tenant, user_factory, membership_factory):
        # Only role *changes* are audited, not the initial membership.
        before = Activity.objects.filter(action=ActivityAction.TEAM_ROLE_CHANGED).count()
        membership_factory(user_factory(email="fresh@acme.test"), tenant.company)
        after = Activity.objects.filter(action=ActivityAction.TEAM_ROLE_CHANGED).count()
        assert after == before


# --------------------------------------------------------------------------- #
# Actor attribution
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestActorAttribution:
    def test_api_write_attributes_requesting_user(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        cid = client.post("/api/v1/customers/", {"name": "By Admin"}, format="json").json()["id"]
        act = _one(ActivityAction.CUSTOMER_CREATED, cid, tenant.company)
        assert act.actor_id == tenant.admin.id

    def test_orm_write_has_no_actor(self, tenant, customer_factory):
        # A system-level write (no request context) is attributed to nobody.
        c = customer_factory(tenant.company)
        act = _one(ActivityAction.CUSTOMER_CREATED, c.id, tenant.company)
        assert act.actor_id is None


# --------------------------------------------------------------------------- #
# No sensitive data in metadata
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestMetadataNeverStoresSensitiveData:
    def test_customer_update_metadata_excludes_pii_values(self, tenant, auth_client):
        client = auth_client(tenant.admin, tenant.company)
        cid = client.post("/api/v1/customers/", {"name": "Init"}, format="json").json()["id"]

        secret_email = "topsecret@hidden.example"
        secret_note = "SSN 123-45-6789"
        client.patch(
            f"/api/v1/customers/{cid}/",
            {"email": secret_email, "notes": secret_note},
            format="json",
        )

        act = _one(ActivityAction.CUSTOMER_UPDATED, cid, tenant.company)
        blob = json.dumps(act.metadata)
        # Only the *names* of changed fields are kept, never their PII values.
        assert "email" in act.metadata["changed_fields"]
        assert "notes" in act.metadata["changed_fields"]
        assert secret_email not in blob
        assert "123-45-6789" not in blob

    def test_service_redacts_sensitive_keys(self, tenant):
        act = record_activity(
            action=ActivityAction.CUSTOMER_UPDATED,
            company=tenant.company,
            entity_type=EntityType.CUSTOMER,
            actor=None,
            metadata={"password": "hunter2", "name": "safe"},
        )
        assert act is not None
        assert act.metadata["password"] == "[REDACTED]"
        assert act.metadata["name"] == "safe"


# --------------------------------------------------------------------------- #
# Immutability & reliability
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestImmutabilityAndReliability:
    def test_activity_cannot_be_updated(self, tenant, customer_factory):
        c = customer_factory(tenant.company)
        act = _one(ActivityAction.CUSTOMER_CREATED, c.id, tenant.company)
        act.action = ActivityAction.CUSTOMER_UPDATED
        with pytest.raises(ValueError, match="immutable"):
            act.save()

    def test_no_op_save_records_nothing(self, tenant, customer_factory):
        c = customer_factory(tenant.company)
        before = Activity.objects.filter(entity_id=c.id).count()
        c.save()  # nothing changed
        assert Activity.objects.filter(entity_id=c.id).count() == before

    def test_record_activity_without_company_is_skipped(self):
        assert record_activity(action=ActivityAction.CUSTOMER_CREATED) is None

    def test_audit_failure_never_breaks_business_write(self, tenant, customer_factory, monkeypatch):
        def boom(_metadata):
            raise RuntimeError("audit backend unavailable")

        monkeypatch.setattr("apps.activities.services.sanitize_metadata", boom)

        c = customer_factory(tenant.company)  # signal fires; failure must be swallowed
        assert Customer.objects.filter(pk=c.id).exists()
        assert Activity.objects.filter(entity_id=c.id).count() == 0
