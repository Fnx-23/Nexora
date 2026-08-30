from rest_framework.routers import DefaultRouter

from apps.activities.api.views import ActivityViewSet

router = DefaultRouter()
router.register("activities", ActivityViewSet, basename="activities")

urlpatterns = router.urls
