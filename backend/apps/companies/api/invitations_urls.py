"""Public invitee-facing invitation endpoints (mounted at /api/v1/invitations/)."""

from django.urls import path

from apps.companies.api.invitations_views import (
    InvitationAcceptExistingView,
    InvitationRegisterAcceptView,
    InvitationValidateView,
)

urlpatterns = [
    path("validate/", InvitationValidateView.as_view(), name="invitation-validate"),
    path(
        "accept/<str:token>/",
        InvitationAcceptExistingView.as_view(),
        name="invitation-accept-existing",
    ),
    path("register/", InvitationRegisterAcceptView.as_view(), name="invitation-register"),
]
