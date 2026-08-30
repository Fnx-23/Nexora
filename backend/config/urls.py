"""Root URL configuration."""

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
    path("users/", include("apps.accounts.api.users_urls")),
    path("companies/", include("apps.companies.api.urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include("apps.customers.api.urls")),
    path("", include("apps.projects.api.urls")),
    path("", include("apps.tasks.api.urls")),
    path("", include("apps.activities.api.urls")),
    path("", include("apps.time_tracking.api.urls")),
    path("", include("apps.notifications.api.urls")),
    path("", include("apps.documents.api.urls")),
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
