from django.urls import path

from apps.companies.api.views import CurrentCompanyView, MemberRoleUpdateView

urlpatterns = [
    path("current/", CurrentCompanyView.as_view(), name="current-company"),
    path(
        "members/<uuid:membership_id>/role/",
        MemberRoleUpdateView.as_view(),
        name="member-role",
    ),
]
