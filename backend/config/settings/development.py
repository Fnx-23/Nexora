"""Development settings: verbose, permissive defaults for local work."""

from .base import *

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
