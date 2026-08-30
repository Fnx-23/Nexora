"""
Production settings: hardened defaults behind a TLS-terminating reverse proxy.

Requires a real SECRET_KEY and explicit ALLOWED_HOSTS/CORS configuration
through environment variables.
"""

from .base import *
from .base import env

DEBUG = False

if not env("SECRET_KEY") or SECRET_KEY.startswith("django-insecure"):
    raise RuntimeError("SECRET_KEY must be set to a strong value in production.")

# Request throttling counters (and Celery) depend on the shared cache; running
# production on an in-process cache would reset limits per worker and per boot.
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL must be configured in production so that request throttling "
        "is backed by Redis rather than per-process memory."
    )

# L-10: schema/docs are disabled by default in production; opt in explicitly
# (preferably only for internal/staging deployments) via API_DOCS_ENABLED=true.
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=False)

# L-10: the admin stays available for legitimate administration but can be
# switched off entirely for hardened deployments via ADMIN_ENABLED=false.
ADMIN_ENABLED = env.bool("ADMIN_ENABLED", default=True)

# Trust nginx as the SSL-terminating proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Opt-in: enable when a TLS-terminating load balancer sits in front of nginx,
# otherwise plain-HTTP internal traffic would be redirected forever.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)

SECURE_HSTS_SECONDS = 31_536_000  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# Serve application static files (admin, DRF) directly from gunicorn via WhiteNoise.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
