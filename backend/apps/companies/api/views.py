"""Company API views."""

from rest_framework.generics import RetrieveUpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.api.serializers import CompanySerializer, MembershipSerializer
from apps.companies.models import Membership, RoleChoices
from apps.core.api.permissions import IsCompanyMember, role_required


class CurrentCompanyView(RetrieveUpdateAPIView):
    """
    Retrieve or update the company the current request operates on.

    Reads are available to every member; updates are restricted to ADMIN.
    """

    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_object(self):
        return self.request.company

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.request.method in ("PUT", "PATCH"):
            permissions.append(role_required(RoleChoices.ADMIN)())
        return permissions


class MemberRoleUpdateView(APIView):
    """Change a member's role within the active company (ADMIN only).

    Tenant-scoped: the membership is looked up strictly within
    ``request.company``, so an admin can never alter another company's members.
    Saving via ``Membership.save`` lets the audit signal record a
    ``team.role_changed`` activity without any per-view audit logic. A guard
    prevents removing the company's last active admin (avoids lock-out).
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(role_required(RoleChoices.ADMIN)())
        return permissions

    def patch(self, request, membership_id):
        new_role = request.data.get("role")
        valid_roles = {choice for choice, _label in RoleChoices.choices}
        if new_role not in valid_roles:
            return Response(
                {"detail": f"Invalid role. Choose from: {', '.join(sorted(valid_roles))}."},
                status=400,
            )

        membership = get_object_or_404(
            Membership,
            id=membership_id,
            company=request.company,
        )

        if membership.role == new_role:
            return Response(MembershipSerializer(membership).data)

        demoting_admin = membership.role == RoleChoices.ADMIN and new_role != RoleChoices.ADMIN
        if demoting_admin:
            other_admins = (
                Membership.objects.filter(
                    company=request.company,
                    role=RoleChoices.ADMIN,
                    is_active=True,
                )
                .exclude(pk=membership.pk)
                .exists()
            )
            if not other_admins:
                return Response(
                    {"detail": "Cannot remove the last active admin of the company."},
                    status=400,
                )

        membership.role = new_role
        membership.save(update_fields=["role", "updated_at"])
        return Response(MembershipSerializer(membership).data)
