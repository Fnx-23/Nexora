"""Reusable DRF permission classes. Role checks are centralized here."""

from rest_framework.permissions import BasePermission

from apps.core.api.context import apply_company_context


class IsCompanyMember(BasePermission):
    """
    Require an authenticated user with an active company membership.

    On success the resolved tenant context is exposed on the request as
    ``request.company`` / ``request.company_role`` for downstream layers.
    """

    message = "You do not belong to any active company."

    def has_permission(self, request, view) -> bool:
        return apply_company_context(request) is not None


class RolePermission(BasePermission):
    """Base class restricting access to specific roles within the active company."""

    allowed_roles: frozenset[str] = frozenset()
    message = "Your role in this company does not allow this action."

    def has_permission(self, request, view) -> bool:
        return getattr(request, "company_role", None) in self.allowed_roles


def role_required(*roles: str) -> type[RolePermission]:
    """Build a permission class allowing only the given company roles."""
    return type(
        f"RequireRoles_{'_'.join(roles) or 'None'}",
        (RolePermission,),
        {"allowed_roles": frozenset(roles)},
    )
