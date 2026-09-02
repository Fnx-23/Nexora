from django.urls import path

from apps.companies.api.invitations_views import (
    InvitationDetailActionView,
    InvitationListCreateView,
    MemberRemoveView,
    MemberStatusActionView,
)
from apps.companies.api.views import CurrentCompanyView, MemberRoleUpdateView

urlpatterns = [
    path("current/", CurrentCompanyView.as_view(), name="current-company"),
    path(
        "members/<uuid:membership_id>/role/",
        MemberRoleUpdateView.as_view(),
        name="member-role",
    ),
    path(
        "members/<uuid:membership_id>/deactivate/",
        MemberStatusActionView.as_view(),
        name="member-deactivate",
    ),
    path(
        "members/<uuid:membership_id>/reactivate/",
        MemberStatusActionView.as_view(),
        name="member-reactivate",
    ),
    path(
        "members/<uuid:membership_id>/",
        MemberRemoveView.as_view(),
        name="member-remove",
    ),
    path(
        "invitations/",
        InvitationListCreateView.as_view(),
        name="invitation-list",
    ),
    path(
        "invitations/<uuid:invitation_id>/revoke/",
        InvitationDetailActionView.as_view(),
        name="invitation-revoke",
    ),
    path(
        "invitations/<uuid:invitation_id>/resend/",
        InvitationDetailActionView.as_view(),
        name="invitation-resend",
    ),
]
