from rest_framework.routers import DefaultRouter

from apps.projects.api.views import ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="projects")

urlpatterns = router.urls
