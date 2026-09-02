"""Root URL configuration."""

from apps.accounts.views_security import (
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    SecurityEventListView,
    SessionViewSet,
    VerifyEmailView,
)
from apps.core.api.dashboard import DashboardView
from apps.core.api.views import HealthCheckView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1 = [
    path("auth/", include("apps.accounts.api.urls")),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/security-events/", SecurityEventListView.as_view(), name="security-events-list"),
    path("auth/sessions/", SessionViewSet.as_view({"get": "list"}), name="sessions-list"),
    path(
        "auth/sessions/revoke-others/",
        SessionViewSet.as_view({"post": "revoke_others"}),
        name="sessions-revoke-others",
    ),
    path(
        "auth/sessions/<uuid:pk>/revoke/",
        SessionViewSet.as_view({"post": "revoke"}),
        name="sessions-revoke",
    ),
    path(
        "auth/reset-password/<uuid:token_id>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    path("users/", include("apps.accounts.api.users_urls")),
    path("companies/", include("apps.companies.api.urls")),
    path("invitations/", include("apps.companies.api.invitations_urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include("apps.customers.api.urls")),
    path("", include("apps.projects.api.urls")),
    path("", include("apps.tasks.api.urls")),
    path("", include("apps.activities.api.urls")),
    path("", include("apps.time_tracking.api.urls")),
    path("", include("apps.notifications.api.urls")),
    path("", include("apps.documents.api.urls")),
    path("", include("apps.search.api.urls")),
    path("reports/", include("apps.reports.api.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    path("healthz/", HealthCheckView.as_view(), name="health-check"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
