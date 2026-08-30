#!/usr/bin/env bash
# One-time local bootstrap: environment file, Python venv, JS dependencies.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - review it before running."
fi

echo "==> Setting up backend virtualenv (.venv)"
python3 -m venv backend/.venv
backend/.venv/bin/pip install --quiet --upgrade pip
backend/.venv/bin/pip install --quiet -r backend/requirements/development.txt

echo "==> Installing frontend dependencies"
(cd frontend && npm install)

cat <<'EOF'

Done. Next steps:

  source backend/.venv/bin/activate
  cd backend && python manage.py migrate && python manage.py runserver

  cd frontend && npm run dev

Or run everything containerized:  docker compose up --build
EOF
