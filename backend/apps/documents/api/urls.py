"""URLs for the documents API."""

from rest_framework.routers import DefaultRouter

from apps.documents.api.views import DocumentViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="documents")

urlpatterns = router.urls
