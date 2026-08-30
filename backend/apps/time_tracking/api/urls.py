from rest_framework.routers import DefaultRouter

from apps.time_tracking.api.views import TimeEntryViewSet

router = DefaultRouter()
router.register("time-entries", TimeEntryViewSet, basename="time-entries")

urlpatterns = router.urls
