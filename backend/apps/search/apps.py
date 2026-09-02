"""App configuration for global search."""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = "apps.search"
    label = "search"
    verbose_name = "Search"
