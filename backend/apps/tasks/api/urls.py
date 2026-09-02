from rest_framework.routers import DefaultRouter

from apps.tasks.api.views import TaskLabelViewSet, TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="tasks")
router.register("labels", TaskLabelViewSet, basename="labels")

urlpatterns = router.urls
