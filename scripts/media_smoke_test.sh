#!/usr/bin/env bash
# H-4 infrastructure smoke test: verifies that uploaded media is served by the
# edge nginx from the shared volume, while non-image payloads are blocked.
#
# Usage: start the stack first (`docker compose up --build -d`), then run this
# script. It cleans up after itself and never touches real uploads.
set -euo pipefail

cd "$(dirname "$0")/.."

BASE_URL="${BASE_URL:-http://localhost}"
PROBE_DIR="smoke-$$"

echo "==> Waiting for backend health…"
for _ in $(seq 1 30); do
    if curl -sf "$BASE_URL/healthz/" >/dev/null 2>&1; then break; fi
    sleep 2
done
curl -sf "$BASE_URL/healthz/" >/dev/null || { echo "backend never became healthy"; exit 1; }

cleanup() {
    docker compose exec -T backend rm -rf "/app/media/$PROBE_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Planting probe files (via backend container, which owns the volume)"
docker compose exec -T backend sh -c "
    mkdir -p /app/media/$PROBE_DIR &&
    printf 'not-a-real-png-but-extension-gated' > /app/media/$PROBE_DIR/probe.png &&
    printf '<html><script>alert(1)</script></html>' > /app/media/$PROBE_DIR/payload.html &&
    printf 'SECRET_KEY=leak' > /app/media/$PROBE_DIR/app.conf
"

echo "==> Image extension must be served through nginx"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/media/$PROBE_DIR/probe.png")
[ "$HTTP_CODE" = "200" ] || { echo "FAIL: expected 200 for probe.png, got $HTTP_CODE"; exit 1; }

HEADERS=$(curl -sI "$BASE_URL/media/$PROBE_DIR/probe.png")
echo "$HEADERS" | grep -qi 'x-content-type-options:.*nosniff' || { echo "FAIL: nosniff header missing"; exit 1; }
echo "$HEADERS" | grep -qi 'content-disposition:.*inline' || { echo "FAIL: inline disposition header missing"; exit 1; }
echo "    served OK with hardening headers"

echo "==> Non-image payloads must be blocked (scripts, config, private files)"
for name in payload.html app.conf; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/media/$PROBE_DIR/$name")
    [ "$HTTP_CODE" = "403" ] || { echo "FAIL: expected 403 for $name, got $HTTP_CODE"; exit 1; }
    echo "    blocked $name"
done

echo "==> Media smoke test passed."
