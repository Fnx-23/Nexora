from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self) -> None:
        from apps.notifications import signals  # noqa: F401
