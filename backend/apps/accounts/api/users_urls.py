"""User directory of the active company (mounted at /api/v1/users/)."""

from rest_framework.routers import DefaultRouter

from apps.accounts.api.users_views import UsersViewSet

router = DefaultRouter()
router.register("", UsersViewSet, basename="users")

urlpatterns = router.urls
