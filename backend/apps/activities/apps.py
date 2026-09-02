from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"
    verbose_name = "Activity & Audit Log"

    def ready(self) -> None:
        from apps.activities import signals  # noqa: F401
