from rest_framework.routers import DefaultRouter

from apps.tasks.api.views import TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")

urlpatterns = router.urls
