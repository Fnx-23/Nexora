"""Signals: create session device on login, update last activity."""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.accounts.models_session import SessionDevice


@receiver(pre_save, sender=SessionDevice, dispatch_uid="accounts.session_device_pre_save")
def _session_device_pre_save(sender, instance, **kwargs):
    """Ensure only one session is marked current per user."""
    if instance.is_current:
        current = SessionDevice.objects.filter(
            user=instance.user,
            is_current=True,
        ).exclude(pk=instance.pk)
        current.update(is_current=False)
