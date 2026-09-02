from django.urls import path

from apps.search.api.views import SearchView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
]
