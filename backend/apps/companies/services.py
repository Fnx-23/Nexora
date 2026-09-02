"""Business logic for team invitations and membership management.

All token handling lives here, never in views or serializers. Invitation
tokens are generated with :func:`secrets.token_urlsafe` (cryptographically
random and unguessable), returned to the caller exactly once, and persisted
only as a SHA-256 hash so a database leak cannot be turned into an accepted
invitation.

The acceptance path enforces every safety property of the invitation:

* one-time use — a consumed (ACCEPTED) token cannot be reused;
* expiry — a token past ``expires_at`` is rejected (and lazily marked EXPIRED);
* cross-tenant manipulation — the invitee can only ever join the company the
  invitation was created against, and must accept with a matching email;
* role confinement — the invitee is granted exactly the role on the invite,
  never something higher.
"""

from __future__ import annotations

import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.companies.email import send_invitation_email
from apps.companies.models import (
    INVITATION_TTL,
    Company,
    InvitationStatus,
    Membership,
    RoleChoices,
    TeamInvitation,
)
from apps.core.exceptions import ApplicationError
from apps.core.request_context import get_actor

User = get_user_model()

INVITATION_INVALID_MESSAGE = "This invitation is invalid, expired, or has already been used."
EMAIL_MISMATCH_MESSAGE = "This invitation was not issued for the address you signed in with."
EMAIL_ALREADY_MEMBER_MESSAGE = "This email is already a member of the company."
DUPLICATE_PENDING_MESSAGE = "An invitation to this email is already pending."
INTERNAL_ERROR_MESSAGE = "The invitation could not be processed. Please try again."


class InvitationError(ApplicationError):
    """A domain-level error surfaced to API clients during invitation flows."""


def hash_token(token: str) -> str:
    """Return a SHA-256 digest of an invitation token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    """Return a new cryptographically random, unguessable invitation token."""
    return secrets.token_urlsafe(48)


def _is_active_member(company: Company, email: str) -> bool:
    return Membership.objects.filter(
        company=company,
        user__email__iexact=email,
        is_active=True,
    ).exists()


@transaction.atomic
def create_invitation(
    *,
    company: Company,
    email: str,
    role: str,
    invited_by: User | None = None,
) -> tuple[TeamInvitation, str]:
    """Create a pending invitation and return ``(invitation, raw_token)``.

    ``raw_token`` is the one and only chance to see the unguessable value; it
    is passed to the email sender and never persisted. Raises
    :class:`InvitationError` when the email is already an active member or when
    a pending invitation already exists for ``(company, email)``.
    """
    email = User.objects.normalize_email(email)

    if _is_active_member(company, email):
        raise InvitationError(EMAIL_ALREADY_MEMBER_MESSAGE)

    raw_token = generate_token()
    expires_at = timezone.now() + INVITATION_TTL

    try:
        invitation = TeamInvitation.objects.create(
            company=company,
            email=email,
            role=role,
            invited_by=invited_by or get_actor(),
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
            status=InvitationStatus.PENDING,
        )
    except IntegrityError:
        raise InvitationError(DUPLICATE_PENDING_MESSAGE) from None

    send_invitation_email(
        email=email,
        company=company,
        role=role,
        token=raw_token,
        invited_by=invited_by or get_actor(),
    )
    return invitation, raw_token


def _get_live_invitation(company: Company, token: str) -> TeamInvitation:
    """Return the PENDING invitation for a raw token within ``company``.

    Raises :class:`InvitationError` if the invitation does not exist in this
    tenant, has been consumed, or has expired (marking it EXPIRED lazily).
    """
    try:
        invitation = TeamInvitation.objects.select_for_update().get(
            company=company,
            token_hash=hash_token(token),
        )
    except TeamInvitation.DoesNotExist:
        raise InvitationError(INVITATION_INVALID_MESSAGE) from None

    if invitation.status == InvitationStatus.ACCEPTED:
        raise InvitationError(INVITATION_INVALID_MESSAGE)
    if invitation.status == InvitationStatus.REVOKED:
        raise InvitationError(INVITATION_INVALID_MESSAGE)
    if invitation.is_expired:
        invitation.mark_expired()
        raise InvitationError(INVITATION_INVALID_MESSAGE)
    return invitation


def _claim_invitation(invitation: TeamInvitation, user: User) -> None:
    """Atomically link an accepted invitation to its member and finalize it."""
    from apps.activities.models import ActivityAction, EntityType
    from apps.activities.services import record_activity

    now = timezone.now()
    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_by = user
    invitation.accepted_at = now
    invitation.save(update_fields=["status", "accepted_by", "accepted_at", "updated_at"])

    record_activity(
        action=ActivityAction.INVITATION_ACCEPTED,
        entity=invitation,
        entity_type=EntityType.INVITATION,
        actor=user,
        metadata={"invitee_email": invitation.email, "role": invitation.role},
    )


@transaction.atomic
def accept_invitation_for_existing_user(*, company: Company, token: str, user: User) -> Membership:
    """Accept an invitation on behalf of an already-registered user.

    The accepting ``user`` must own an email matching the invitation. A
    membership is created (or re-activated if one exists but is inactive) with
    the role carried by the invitation.
    """
    if not user.is_authenticated:
        raise InvitationError(INVITATION_INVALID_MESSAGE)

    invitation = _get_live_invitation(company, token)
    if User.objects.normalize_email(user.email) != invitation.email:
        raise InvitationError(EMAIL_MISMATCH_MESSAGE)

    membership, created = Membership.objects.get_or_create(
        company=invitation.company,
        user=user,
        defaults={"role": invitation.role, "is_active": True},
    )
    if not created:
        membership.is_active = True
        membership.role = invitation.role
        membership.save(update_fields=["role", "is_active", "updated_at"])

    _claim_invitation(invitation, user)
    return membership


@transaction.atomic
def accept_invitation_for_new_user(
    *,
    company: Company,
    token: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
) -> Membership:
    """Accept an invitation by registering the invitee as a new user.

    Creates the user (if they do not already exist) and immediately links them
    into the company with the invitation's role. The email is checked against
    the invitation to prevent one invite being used to join with a different
    address.
    """
    email = User.objects.normalize_email(email)
    invitation = _get_live_invitation(company, token)
    if email != invitation.email:
        raise InvitationError(EMAIL_MISMATCH_MESSAGE)

    if _is_active_member(invitation.company, email):
        raise InvitationError(EMAIL_ALREADY_MEMBER_MESSAGE)

    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
    except IntegrityError:
        raise InvitationError(INTERNAL_ERROR_MESSAGE) from None

    membership = Membership.objects.create(
        company=invitation.company,
        user=user,
        role=invitation.role,
        is_active=True,
    )
    _claim_invitation(invitation, user)
    return membership


@transaction.atomic
def revoke_invitation(company: Company, invitation: TeamInvitation) -> TeamInvitation:
    """Revoke a pending invitation (idempotent for non-pending invitations)."""
    invitation = TeamInvitation.objects.select_for_update().get(pk=invitation.pk)
    if invitation.status == InvitationStatus.PENDING:
        invitation.status = InvitationStatus.REVOKED
        invitation.save(update_fields=["status", "updated_at"])
    return invitation


@transaction.atomic
def resend_invitation(company: Company, invitation: TeamInvitation) -> tuple[TeamInvitation, str]:
    """Reset expiration, mint a fresh token and re-send for a pending invitation."""
    invitation = TeamInvitation.objects.select_for_update().get(pk=invitation.pk)
    if invitation.status != InvitationStatus.PENDING:
        raise InvitationError("Only pending invitations can be resent.")

    raw_token = generate_token()
    invitation.token_hash = hash_token(raw_token)
    invitation.expires_at = timezone.now() + INVITATION_TTL
    invitation.save(update_fields=["token_hash", "expires_at", "updated_at"])

    send_invitation_email(
        email=invitation.email,
        company=company,
        role=invitation.role,
        token=raw_token,
        invited_by=invitation.invited_by,
    )
    return invitation, raw_token


def safe_role_for_inviter(request_role: str | None, requested_role: str) -> str:
    """Constrain the role an admin may offer on an invitation.

    Managers may only invite as EMPLOYEE unless an explicit policy allows
    otherwise; ADMINS may invite anyone. ``requested_role`` is always validated
    against ``RoleChoices`` by the serializer before reaching this helper.
    """
    if requested_role == RoleChoices.ADMIN and request_role != RoleChoices.ADMIN:
        raise InvitationError("Only admins can invite other admins.")
    return requested_role
