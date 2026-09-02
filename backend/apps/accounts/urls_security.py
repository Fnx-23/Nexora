"""URL patterns for account security endpoints."""

from django.urls import path

from apps.accounts.views_security import (
    ChangePasswordView,
    ResetPasswordView,
    SecurityEventListView,
    SessionViewSet,
    VerifyEmailView,
)

urlpatterns = [
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("security-events/", SecurityEventListView.as_view(), name="security-events-list"),
    path("sessions/", SessionViewSet.as_view({"get": "list"}), name="sessions-list"),
    path(
        "sessions/revoke-others/",
        SessionViewSet.as_view({"post": "revoke_others"}),
        name="sessions-revoke-others",
    ),
    path(
        "sessions/<uuid:pk>/revoke/",
        SessionViewSet.as_view({"post": "revoke"}),
        name="sessions-revoke",
    ),
    path(
        "reset-password/<uuid:token_id>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
]
