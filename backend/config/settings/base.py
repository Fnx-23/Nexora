"""
Base Django settings shared by every environment.

All deployment-specific values are read from environment variables
(optionally loaded from a `.env` file at the repository root of the backend).
Secrets must never be hard-coded or committed.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "django-insecure-dev-only-key-do-not-use-in-production"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    POSTGRES_DB=(str, "nexora"),
    POSTGRES_USER=(str, "nexora"),
    POSTGRES_PASSWORD=(str, "nexora"),
    POSTGRES_HOST=(str, "localhost"),
    POSTGRES_PORT=(int, 5432),
    REDIS_URL=(str, ""),
    CELERY_BROKER_URL=(str, ""),
    CELERY_TASK_ALWAYS_EAGER=(bool, False),
    ACCESS_TOKEN_MINUTES=(int, 30),
    REFRESH_TOKEN_DAYS=(int, 7),
    AUTH_THROTTLE_LOGIN=(str, "10/min"),
    AUTH_THROTTLE_REGISTER=(str, "5/min"),
    AUTH_THROTTLE_REFRESH=(str, "30/min"),
    NUM_PROXIES=(str, "1"),
    AVATAR_MAX_SIZE_MB=(int, 2),
    API_DOCS_ENABLED=(bool, True),
    ADMIN_ENABLED=(bool, True),
    LOG_LEVEL=(str, "INFO"),
    STATIC_ROOT=(str, str(BASE_DIR / "staticfiles")),
    MEDIA_ROOT=(str, str(BASE_DIR / "media")),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.companies",
    "apps.customers",
    "apps.projects",
    "apps.tasks",
    "apps.activities",
    # Reserved for upcoming domains; kept installed so wiring stays in place.
    "apps.time_tracking",
    "apps.documents",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Clear the request-scoped audit actor on the way out (pooled threads).
    "apps.core.api.middleware.RequestActorMiddleware",
    # L-10: per-request 404 gating of /admin/ and API schema/docs surfaces.
    "apps.core.api.middleware.SurfaceExposureMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Authentication

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("REFRESH_TOKEN_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Database (PostgreSQL)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "CONN_MAX_AGE": 60,
    }
}

# Cache / Redis / Celery
#
# The default cache backs DRF request throttling: it is Redis whenever
# REDIS_URL is configured (production/Docker) and falls back to an in-process
# store for bare local development. Production settings refuse to boot without
# Redis so throttling is never in-memory-only there (see settings/production.py).

REDIS_URL = env("REDIS_URL")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

CELERY_BROKER_URL = env("CELERY_BROKER_URL") or REDIS_URL or "memory://"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER")
CELERY_TASK_EAGER_PROPAGATES = True

# DRF

# Number of reverse proxies in front of the API that append to
# X-Forwarded-For. Throttle identity uses the client hop selected by this
# value ("0" trusts REMOTE_ADDR only). Behind the nginx edge service the
# correct value is 1; clients cannot spoof past it because nginx appends the
# real remote address as the last element.
_num_proxies_raw = env("NUM_PROXIES").strip()
NUM_PROXIES = int(_num_proxies_raw) if _num_proxies_raw else None

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.api.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    # Scoped rates for anonymous authentication endpoints only; applied via
    # per-view `throttle_classes` (see apps/core/api/throttling.py), not globally.
    "DEFAULT_THROTTLE_RATES": {
        "auth-login": env("AUTH_THROTTLE_LOGIN"),
        "auth-register": env("AUTH_THROTTLE_REGISTER"),
        "auth-refresh": env("AUTH_THROTTLE_REFRESH"),
    },
    "NUM_PROXIES": NUM_PROXIES,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# OpenAPI schema / Swagger

# L-10: developer-facing schema/docs endpoints (/api/schema/, /api/docs/,
# /api/redoc/) can be turned off at runtime. Development defaults to enabled;
# production flips the default to disabled (see settings/production.py).
API_DOCS_ENABLED = env("API_DOCS_ENABLED")

# L-10: the Django admin surface can be disabled entirely for hardened
# deployments that administer accounts via CLI/API only.
ADMIN_ENABLED = env("ADMIN_ENABLED")

SPECTACULAR_SETTINGS = {
    "TITLE": "Nexora API",
    "DESCRIPTION": "REST API for the Nexora business management platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# CORS / CSRF

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Uploads

AVATAR_MAX_SIZE_MB = env("AVATAR_MAX_SIZE_MB")

# Static & media files

STATIC_URL = "static/"
STATIC_ROOT = Path(env("STATIC_ROOT"))
# Leading slash keeps FileField.url values absolute ("/media/..."), which the
# SPA can use directly regardless of the active client-side route.
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {module}.{funcName}(): {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL"),
    },
    "loggers": {
        "django": {"level": "INFO"},
        "django.server": {"level": "WARNING"},
    },
}
