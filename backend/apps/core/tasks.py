"""Shared Celery tasks."""

from celery import shared_task


@shared_task
def ping() -> str:
    """Reference task proving broker wiring end-to-end."""
    return "pong"
