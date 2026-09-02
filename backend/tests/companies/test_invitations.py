"""Tests for team invitations and membership management."""

from __future__ import annotations

from datetime import timedelta

import pytest
from apps.activities.models import Activity, ActivityAction
from apps.companies.models import (
    InvitationStatus,
    Membership,
    RoleChoices,
    TeamInvitation,
)
from apps.companies.services import create_invitation, hash_token
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework import status

User = get_user_model()
PASSWORD = "Str0ng-Passw0rd!"


@pytest.fixture
def two_tenants(user_factory, company_factory, membership_factory):
    """Company A (admin + employee) and Company B (admin)."""
    from types import SimpleNamespace

    admin_a = user_factory(email="admin@a.test", password=PASSWORD)
    employee_a = user_factory(email="emp@a.test", password=PASSWORD)
    admin_b = user_factory(email="admin@b.test", password=PASSWORD)
    company_a = company_factory(name="Company A", slug="company-a")
    company_b = company_factory(name="Company B", slug="company-b")
    membership_factory(admin_a, company_a, RoleChoices.ADMIN)
    membership_factory(employee_a, company_a, RoleChoices.EMPLOYEE)
    membership_factory(admin_b, company_b, RoleChoices.ADMIN)

    return SimpleNamespace(
        a_company=company_a,
        b_company=company_b,
        admin_a=admin_a,
        employee_a=employee_a,
        admin_b=admin_b,
    )


# --------------------------------------------------------------------------- #
# Invite member (admin-side)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestInviteMember:
    def test_admin_can_invite_existing_user(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "invitee@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["email"] == "invitee@a.test"
        assert resp.data["role"] == "EMPLOYEE"
        assert resp.data["status"] == InvitationStatus.PENDING
        assert "token" not in resp.data  # token must never be exposed in responses
        assert TeamInvitation.objects.filter(company=two_tenants.a_company).count() == 1

    def test_invitation_sends_email(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "newbie@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert "newbie@a.test" in mail.outbox[0].to

    def test_employee_cannot_invite(self, two_tenants, auth_client):
        client = auth_client(two_tenants.employee_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "x@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_pending_invite_rejected(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        first = client.post(
            "/api/v1/companies/invitations/",
            {"email": "dup@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert first.status_code == status.HTTP_201_CREATED
        second = client.post(
            "/api/v1/companies/invitations/",
            {"email": "dup@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert second.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_invite_existing_active_member(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": two_tenants.employee_a.email, "role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invite_email_normalized_to_lowercase(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "MixedCase@Test.Com", "role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["email"] == "mixedcase@test.com"

    def test_manager_cannot_invite_admin(self, two_tenants, auth_client, membership_factory):
        manager = User.objects.create_user(email="mgr@a.test", password=PASSWORD)
        membership_factory(manager, two_tenants.a_company, RoleChoices.MANAGER)
        client = auth_client(manager, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "target@a.test", "role": "ADMIN"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_can_invite_admin(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(
            "/api/v1/companies/invitations/",
            {"email": "future-admin@a.test", "role": "ADMIN"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["role"] == "ADMIN"


# --------------------------------------------------------------------------- #
# Validation / acceptance
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestValidateInvitation:
    def test_validate_pending_returns_flow(self, two_tenants, auth_client):
        invitation, raw = create_invitation(
            company=two_tenants.a_company,
            email="someone@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        resp = auth_client(two_tenants.admin_a, two_tenants.a_company).post(
            "/api/v1/invitations/validate/", {"token": raw}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == "someone@a.test"
        assert resp.data["company_name"] == "Company A"
        assert resp.data["user_exists"] is False

    def test_validate_invalid_token(self, two_tenants, auth_client):
        resp = auth_client(two_tenants.admin_a, two_tenants.a_company).post(
            "/api/v1/invitations/validate/", {"token": "garbage"}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_validate_expired_token(self, two_tenants, auth_client):
        token = "expired-tok"
        TeamInvitation.objects.create(
            company=two_tenants.a_company,
            email="late@a.test",
            role="EMPLOYEE",
            token_hash=hash_token(token),
            expires_at=timezone.now() - timedelta(days=1),
        )
        resp = auth_client(two_tenants.admin_a, two_tenants.a_company).post(
            "/api/v1/invitations/validate/", {"token": token}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        # Lazily marked expired.
        assert TeamInvitation.objects.get(email="late@a.test").status == InvitationStatus.EXPIRED


@pytest.mark.django_db
class TestAcceptExistingUser:
    def test_existing_user_accepts(self, two_tenants, auth_client, user_factory):
        invitee = user_factory(email="existing@a.test", password=PASSWORD)
        invitation, raw = create_invitation(
            company=two_tenants.a_company,
            email="existing@a.test",
            role="MANAGER",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(invitee)
        resp = client.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["role"] == "MANAGER"
        membership = Membership.objects.get(company=two_tenants.a_company, user=invitee)
        assert membership.role == "MANAGER"
        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.ACCEPTED
        assert invitation.accepted_by == invitee

    def test_email_mismatch_rejected(self, two_tenants, auth_client, user_factory):
        other = user_factory(email="other@a.test", password=PASSWORD)
        _inv, raw = create_invitation(
            company=two_tenants.a_company,
            email="intended@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(other)
        resp = client.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert not Membership.objects.filter(company=two_tenants.a_company, user=other).exists()

    def test_expired_token_rejected(self, two_tenants, auth_client, user_factory):
        invitee = user_factory(email="expired@a.test", password=PASSWORD)
        token = "expired-raw"
        TeamInvitation.objects.create(
            company=two_tenants.a_company,
            email="expired@a.test",
            role="EMPLOYEE",
            token_hash=hash_token(token),
            expires_at=timezone.now() - timedelta(hours=1),
        )
        client = auth_client(invitee)
        resp = client.post(f"/api/v1/invitations/accept/{token}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert not Membership.objects.filter(company=two_tenants.a_company, user=invitee).exists()

    def test_reused_token_rejected(self, two_tenants, auth_client, user_factory):
        invitee = user_factory(email="one@a.test", password=PASSWORD)
        invitation, raw = create_invitation(
            company=two_tenants.a_company,
            email="one@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(invitee)
        assert client.post(f"/api/v1/invitations/accept/{raw}/").status_code == status.HTTP_200_OK
        second = auth_client(User.objects.create_user(email="other2@a.test", password=PASSWORD))
        resp = second.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_foreign_tenant_token_cannot_be_used(self, two_tenants, auth_client, user_factory):
        # An invitation issued for Company A's email must not let an arbitrary
        # authenticated user (from another tenant) accept it.
        _inv, raw = create_invitation(
            company=two_tenants.a_company,
            email="target@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        # Someone from Company B attempts to consume Company A's invitation.
        b_member = auth_client(two_tenants.admin_b, two_tenants.b_company)
        resp = b_member.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            not Membership.objects.filter(company=two_tenants.a_company)
            .exclude(user__in=[two_tenants.admin_a, two_tenants.employee_a])
            .exists()
        )

    def test_foreign_user_with_different_email_rejected(
        self, two_tenants, auth_client, user_factory
    ):
        _inv, raw = create_invitation(
            company=two_tenants.a_company,
            email="legit@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        intruder = user_factory(email="legit@a.test".replace("@a.test", "@evil.test"))
        client = auth_client(intruder)
        resp = client.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert not Membership.objects.filter(company=two_tenants.a_company, user=intruder).exists()


@pytest.mark.django_db
class TestRegisterAccept:
    def test_new_user_registers_and_joins(self, two_tenants, auth_client):
        invitation, raw = create_invitation(
            company=two_tenants.a_company,
            email="fresh@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        resp = auth_client(two_tenants.admin_a, two_tenants.a_company).post(
            "/api/v1/invitations/register/",
            {
                "token": raw,
                "email": "fresh@a.test",
                "first_name": "Fresh",
                "last_name": "Face",
                "password": "Str0ngPassw0rd!",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert "tokens" in resp.data
        user = User.objects.get(email="fresh@a.test")
        membership = Membership.objects.get(company=two_tenants.a_company, user=user)
        assert membership.role == "EMPLOYEE"
        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.ACCEPTED

    def test_register_accept_email_mismatch_rejected(self, two_tenants):
        invitation, raw = create_invitation(
            company=two_tenants.a_company,
            email="correct@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        from rest_framework.test import APIClient

        resp = APIClient().post(
            "/api/v1/invitations/register/",
            {
                "token": raw,
                "email": "wrong@a.test",
                "first_name": "Wrong",
                "last_name": "Email",
                "password": "Str0ngPassw0rd!",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(email="wrong@a.test").exists()

    def test_register_accept_expired_rejected(self, two_tenants):
        from rest_framework.test import APIClient

        token = "reg-expired"
        TeamInvitation.objects.create(
            company=two_tenants.a_company,
            email="late@a.test",
            role="EMPLOYEE",
            token_hash=hash_token(token),
            expires_at=timezone.now() - timedelta(days=2),
        )
        resp = APIClient().post(
            "/api/v1/invitations/register/",
            {
                "token": token,
                "email": "late@a.test",
                "first_name": "Late",
                "last_name": "Joiner",
                "password": "Str0ngPassw0rd!",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# --------------------------------------------------------------------------- #
# Revoke / resend
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestRevokeResend:
    def test_admin_can_revoke_pending(self, two_tenants, auth_client):
        invitation, _ = create_invitation(
            company=two_tenants.a_company,
            email="rev@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(f"/api/v1/companies/invitations/{invitation.id}/revoke/")
        assert resp.status_code == status.HTTP_200_OK
        invitation.refresh_from_db()
        assert invitation.status == InvitationStatus.REVOKED

    def test_revoked_token_cannot_be_used(self, two_tenants, auth_client, user_factory):
        _inv, raw = create_invitation(
            company=two_tenants.a_company,
            email="rev2@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        auth_client(two_tenants.admin_a, two_tenants.a_company).post(
            f"/api/v1/companies/invitations/{_inv.id}/revoke/"
        )
        invitee = user_factory(email="rev2@a.test", password=PASSWORD)
        client = auth_client(invitee)
        resp = client.post(f"/api/v1/invitations/accept/{raw}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_rotates_token_and_sends_email(self, two_tenants, auth_client):
        invitation, _ = create_invitation(
            company=two_tenants.a_company,
            email="again@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        old_hash = invitation.token_hash
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        resp = client.post(f"/api/v1/companies/invitations/{invitation.id}/resend/")
        assert resp.status_code == status.HTTP_200_OK
        invitation.refresh_from_db()
        assert invitation.token_hash != old_hash
        assert len(mail.outbox) == 2

    def test_resend_revoked_rejected(self, two_tenants, auth_client):
        invitation, _ = create_invitation(
            company=two_tenants.a_company,
            email="rev3@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        client.post(f"/api/v1/companies/invitations/{invitation.id}/revoke/")
        resp = client.post(f"/api/v1/companies/invitations/{invitation.id}/resend/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# --------------------------------------------------------------------------- #
# Member management + role safety
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestMemberManagement:
    def test_deactivate_and_reactivate(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        deact = client.post(f"/api/v1/companies/members/{membership.id}/deactivate/")
        assert deact.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.is_active is False
        react = client.post(f"/api/v1/companies/members/{membership.id}/reactivate/")
        assert react.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.is_active is True

    def test_deactivated_member_still_visible_with_status(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        client.post(f"/api/v1/companies/members/{membership.id}/deactivate/")
        resp = client.get("/api/v1/users/")
        rows = {row["email"]: row for row in resp.json()["results"]}
        assert two_tenants.employee_a.email in rows
        assert rows[two_tenants.employee_a.email]["membership_active"] is False

    def test_employee_cannot_deactivate(self, two_tenants, auth_client):
        client = auth_client(two_tenants.employee_a, two_tenants.a_company)
        membership = Membership.objects.get(company=two_tenants.a_company, user=two_tenants.admin_a)
        resp = client.post(f"/api/v1/companies/members/{membership.id}/deactivate/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_deactivate_last_admin(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(company=two_tenants.a_company, user=two_tenants.admin_a)
        resp = client.post(f"/api/v1/companies/members/{membership.id}/deactivate/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        membership.refresh_from_db()
        assert membership.is_active is True

    def test_cannot_remove_last_admin(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(company=two_tenants.a_company, user=two_tenants.admin_a)
        resp = client.delete(f"/api/v1/companies/members/{membership.id}/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert Membership.objects.filter(user=two_tenants.admin_a).exists()

    def test_remove_allows_if_other_admin_exists(
        self, two_tenants, auth_client, membership_factory
    ):
        second_admin = User.objects.create_user(email="admin2@a.test", password=PASSWORD)
        membership_factory(second_admin, two_tenants.a_company, RoleChoices.ADMIN)
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        resp = client.delete(f"/api/v1/companies/members/{membership.id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Membership.objects.filter(
            company=two_tenants.a_company, user=two_tenants.employee_a
        ).exists()

    def test_remove_foreign_company_member_404(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        foreign_membership = Membership.objects.get(
            company=two_tenants.b_company, user=two_tenants.admin_b
        )
        resp = client.delete(f"/api/v1/companies/members/{foreign_membership.id}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_employee_cannot_change_role(self, two_tenants, auth_client):
        client = auth_client(two_tenants.employee_a, two_tenants.a_company)
        membership = Membership.objects.get(company=two_tenants.a_company, user=two_tenants.admin_a)
        resp = client.patch(
            f"/api/v1/companies/members/{membership.id}/role/",
            {"role": "MANAGER"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_last_admin_cannot_be_demoted(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(company=two_tenants.a_company, user=two_tenants.admin_a)
        resp = client.patch(
            f"/api/v1/companies/members/{membership.id}/role/",
            {"role": "EMPLOYEE"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_role_change_allowed_with_other_admin(
        self, two_tenants, auth_client, membership_factory
    ):
        second_admin = User.objects.create_user(email="admin3@a.test", password=PASSWORD)
        membership_factory(second_admin, two_tenants.a_company, RoleChoices.ADMIN)
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        resp = client.patch(
            f"/api/v1/companies/members/{membership.id}/role/",
            {"role": "MANAGER"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.role == "MANAGER"


# --------------------------------------------------------------------------- #
# Activity logging
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
class TestInvitationActivity:
    def test_invitation_sent_logged(self, two_tenants, auth_client):
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        client.post(
            "/api/v1/companies/invitations/",
            {"email": "audit@a.test", "role": "EMPLOYEE"},
            format="json",
        )
        assert Activity.objects.filter(
            company=two_tenants.a_company, action=ActivityAction.INVITATION_SENT
        ).exists()

    def test_invitation_revoked_logged(self, two_tenants, auth_client):
        invitation, _ = create_invitation(
            company=two_tenants.a_company,
            email="audit2@a.test",
            role="EMPLOYEE",
            invited_by=two_tenants.admin_a,
        )
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        client.post(f"/api/v1/companies/invitations/{invitation.id}/revoke/")
        assert Activity.objects.filter(
            company=two_tenants.a_company, action=ActivityAction.INVITATION_REVOKED
        ).exists()

    def test_role_changed_logged(self, two_tenants, auth_client, membership_factory):
        second_admin = User.objects.create_user(email="admin4@a.test", password=PASSWORD)
        membership_factory(second_admin, two_tenants.a_company, RoleChoices.ADMIN)
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        client.patch(
            f"/api/v1/companies/members/{membership.id}/role/",
            {"role": "MANAGER"},
            format="json",
        )
        assert Activity.objects.filter(
            company=two_tenants.a_company, action=ActivityAction.TEAM_ROLE_CHANGED
        ).exists()

    def test_deactivated_and_removed_logged(self, two_tenants, auth_client, membership_factory):
        second_admin = User.objects.create_user(email="admin5@a.test", password=PASSWORD)
        membership_factory(second_admin, two_tenants.a_company, RoleChoices.ADMIN)
        client = auth_client(two_tenants.admin_a, two_tenants.a_company)
        membership = Membership.objects.get(
            company=two_tenants.a_company, user=two_tenants.employee_a
        )
        client.post(f"/api/v1/companies/members/{membership.id}/deactivate/")
        assert Activity.objects.filter(
            company=two_tenants.a_company, action=ActivityAction.TEAM_MEMBER_DEACTIVATED
        ).exists()
        client.delete(f"/api/v1/companies/members/{membership.id}/")
        assert Activity.objects.filter(
            company=two_tenants.a_company, action=ActivityAction.TEAM_MEMBER_REMOVED
        ).exists()
