from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"
    verbose_name = "Activity & Audit Log"

    def ready(self) -> None:
        # Connect model signal receivers. Importing the module registers the
        # @receiver-decorated handlers that translate domain writes into audit
        # Activity records, keeping that logic out of every view.
        from apps.activities import signals  # noqa: F401
