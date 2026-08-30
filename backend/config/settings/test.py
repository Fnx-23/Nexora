"""
Test settings.

Uses an in-memory SQLite database by default so `pytest` runs anywhere.
Set `TEST_USE_POSTGRES=true` (plus the standard POSTGRES_* variables) to run
the suite against PostgreSQL instead, as CI does.
"""

from .base import *
from .base import env

DEBUG = False

if not env.bool("TEST_USE_POSTGRES", default=False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = None

REDIS_URL = ""
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
