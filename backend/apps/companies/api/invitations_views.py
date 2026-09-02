"""API views for team invitations and membership management.

Two distinct surfaces live here:

* **Admin/manager surface** (tenant-scoped): create, list, revoke and resend
  invitations, plus deactivate/reactivate/remove members. Governance is
  enforced with the ``role_required`` permission classes and the role-safety
  helpers in :mod:`scripts`/the service layer.
* **Public invitee surface** (token-based, not tenant-scoped): validating an
  invite token and accepting it, either for an existing user or by registering
  a brand-new one.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.api.invitations_serializers import (
    InvitationAcceptExistingSerializer,
    InvitationCreateSerializer,
    InvitationOutputSerializer,
    InvitationRegisterAcceptSerializer,
    InvitationValidateSerializer,
)
from apps.companies.api.serializers import MembershipSerializer
from apps.companies.models import InvitationStatus, Membership, RoleChoices, TeamInvitation
from apps.companies.services import (
    INVITATION_INVALID_MESSAGE,
    InvitationError,
    accept_invitation_for_existing_user,
    accept_invitation_for_new_user,
    create_invitation,
    resend_invitation,
    revoke_invitation,
    safe_role_for_inviter,
)
from apps.core.api.permissions import IsCompanyMember, role_required

User = get_user_model()

_invite_roles = role_required(RoleChoices.ADMIN, RoleChoices.MANAGER)
_admin_only = role_required(RoleChoices.ADMIN)


def _invitation_error(exc: InvitationError) -> Response:
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class InvitationListCreateView(APIView):
    """Create and list team invitations for the active company."""

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(_invite_roles())
        return permissions

    def get(self, request):
        invitations = TeamInvitation.objects.filter(
            company=request.company,
            status=InvitationStatus.PENDING,
        ).select_related("invited_by")
        serializer = InvitationOutputSerializer(invitations, many=True)
        return Response({"results": serializer.data})

    def post(self, request):
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            role = safe_role_for_inviter(request.company_role, data["role"])
            invitation, _raw = create_invitation(
                company=request.company,
                email=data["email"],
                role=role,
                invited_by=request.user,
            )
        except InvitationError as exc:
            return _invitation_error(exc)

        return Response(
            InvitationOutputSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class InvitationDetailActionView(APIView):
    """Revoke or resend a single pending invitation (tenant-scoped)."""

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(_invite_roles())
        return permissions

    def _get_invitation(self, request, invitation_id) -> TeamInvitation:
        return get_object_or_404(
            TeamInvitation,
            id=invitation_id,
            company=request.company,
        )

    def post(self, request, invitation_id):
        action = request.resolver_match.url_name
        invitation = self._get_invitation(request, invitation_id)

        try:
            if action == "invitation-revoke":
                revoke_invitation(request.company, invitation)
            elif action == "invitation-resend":
                resend_invitation(request.company, invitation)
            else:
                return Response({"detail": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST)
        except InvitationError as exc:
            return _invitation_error(exc)

        invitation.refresh_from_db()
        return Response(InvitationOutputSerializer(invitation).data)


class MemberStatusActionView(APIView):
    """Deactivate or reactivate a member within the active company (ADMIN only)."""

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(_admin_only())
        return permissions

    def _get_membership(self, request, membership_id) -> Membership:
        return get_object_or_404(
            Membership,
            id=membership_id,
            company=request.company,
        )

    def post(self, request, membership_id):
        action = request.resolver_match.url_name
        membership = self._get_membership(request, membership_id)

        if action == "member-deactivate":
            has_other_active_admin = (
                Membership.objects.filter(
                    company=request.company,
                    role=RoleChoices.ADMIN,
                    is_active=True,
                )
                .exclude(pk=membership.pk)
                .exists()
            )
            if membership.role == RoleChoices.ADMIN and not has_other_active_admin:
                return Response(
                    {"detail": "Cannot deactivate the last active admin of the company."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not membership.is_active:
                return Response(MembershipSerializer(membership).data)
            membership.is_active = False
        elif action == "member-reactivate":
            if membership.is_active:
                return Response(MembershipSerializer(membership).data)
            membership.is_active = True
        else:
            return Response({"detail": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST)

        membership.save(update_fields=["is_active", "updated_at"])
        return Response(MembershipSerializer(membership).data)


class MemberRemoveView(APIView):
    """Remove a member from the active company (ADMIN only)."""

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(_admin_only())
        return permissions

    def delete(self, request, membership_id):
        membership = get_object_or_404(
            Membership,
            id=membership_id,
            company=request.company,
        )

        if membership.user_id == request.user.pk:
            other_admins = Membership.objects.filter(
                company=request.company,
                role=RoleChoices.ADMIN,
                is_active=True,
            ).exclude(pk=membership.pk)
            if membership.role == RoleChoices.ADMIN and not other_admins.exists():
                return Response(
                    {"detail": "Cannot remove the last active admin of the company."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        has_other_active_admin = Membership.objects.filter(
            company=request.company,
            role=RoleChoices.ADMIN,
            is_active=True,
        ).exclude(pk=membership.pk)
        if membership.role == RoleChoices.ADMIN and not has_other_active_admin.exists():
            return Response(
                {"detail": "Cannot remove the last active admin of the company."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationValidateView(APIView):
    """Pre-flight an invitation token so the client can pick login vs. register."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]

        try:
            invitation = TeamInvitation.objects.get(token_hash=_hash_for(token))
        except TeamInvitation.DoesNotExist:
            return Response(
                {"detail": INVITATION_INVALID_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.status != InvitationStatus.PENDING or invitation.is_expired:
            if invitation.is_expired and invitation.status == InvitationStatus.PENDING:
                invitation.mark_expired()
            return Response(
                {"detail": INVITATION_INVALID_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_exists = User.objects.filter(email__iexact=invitation.email).exists()
        return Response(
            {
                "email": invitation.email,
                "company_name": invitation.company.name,
                "role": invitation.role,
                "user_exists": user_exists,
            }
        )


class InvitationAcceptExistingView(APIView):
    """Accept an invitation as an already-registered user (must match email)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        serializer = InvitationAcceptExistingSerializer(data={"token": token})
        serializer.is_valid(raise_exception=True)

        try:
            invitation = TeamInvitation.objects.select_related("company").get(
                token_hash=_hash_for(token)
            )
        except TeamInvitation.DoesNotExist:
            return _invitation_error(InvitationError(INVITATION_INVALID_MESSAGE))

        try:
            membership = accept_invitation_for_existing_user(
                company=invitation.company,
                token=token,
                user=request.user,
            )
        except InvitationError as exc:
            return _invitation_error(exc)

        return Response(MembershipSerializer(membership, context={"request": request}).data)


class InvitationRegisterAcceptView(APIView):
    """Accept an invitation by registering the invitee as a new user."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationRegisterAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invitation = TeamInvitation.objects.select_related("company").get(
                token_hash=_hash_for(data["token"])
            )
        except TeamInvitation.DoesNotExist:
            return _invitation_error(InvitationError(INVITATION_INVALID_MESSAGE))

        try:
            membership = accept_invitation_for_new_user(
                company=invitation.company,
                token=data["token"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                password=data["password"],
            )
        except InvitationError as exc:
            return _invitation_error(exc)

        refresh = _refresh_for(membership.user)
        return Response(
            {
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
                "membership": MembershipSerializer(membership, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


def _hash_for(token: str) -> str:
    from apps.companies.services import hash_token

    return hash_token(token)


def _refresh_for(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    return RefreshToken.for_user(user)
