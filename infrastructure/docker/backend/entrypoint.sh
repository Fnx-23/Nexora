#!/bin/sh
set -e

# Explicit non-server commands (the Compose celery service) exec directly:
# they must not run migrations or collectstatic alongside the API container.
if [ "${1:-}" = "celery" ]; then
    echo "==> Starting Celery worker…"
    exec "$@"
fi

echo "==> Waiting for the database…"
python - <<'PY'
import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
import django  # noqa: E402

django.setup()

from django.db import connection  # noqa: E402

deadline = time.monotonic() + 30
while True:
    try:
        connection.ensure_connection()
        break
    except Exception:
        if time.monotonic() > deadline:
            print("Database never became available.", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY

echo "==> Applying migrations…"
python manage.py migrate --noinput

echo "==> Collecting static files…"
python manage.py collectstatic --noinput

if [ "$RUN_DEV_SERVER" = "true" ]; then
    echo "==> Starting development server…"
    exec python manage.py runserver 0.0.0.0:8000
fi

echo "==> Starting gunicorn…"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
