# Build from the repository root so both backend source and the shared
# entrypoint are available:
#   docker build -f infrastructure/docker/backend/Dockerfile .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Dependencies first so source changes do not bust this layer.
COPY backend/requirements/ /app/requirements/
RUN pip install -r requirements/production.txt

COPY backend/ /app/
COPY infrastructure/docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && addgroup --system nexora \
    && adduser --system --ingroup nexora --home /app nexora \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R nexora:nexora /app

USER nexora

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
