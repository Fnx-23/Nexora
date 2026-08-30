# Nexora

A modern business management platform for small and medium-sized companies —
customers, teams, projects, tasks and reporting behind one clean B2B SaaS
foundation.

> **Status: foundation.** This repository contains the production-grade
> skeleton: multi-tenant architecture, authentication, role system, API
> scaffolding, design system and CI. Feature modules ship on top of it one by
> one (see [Roadmap](#roadmap)).

## Overview

Nexora is built as two independent applications:

- **`backend/`** — a Django REST Framework API with JWT authentication,
  PostgreSQL persistence, Redis/Celery for async work and strict company-level
  tenant isolation.
- **`frontend/`** — a React + TypeScript SPA (Vite) with Tailwind CSS,
  React Router and TanStack Query.

An nginx edge service routes `/api/*`, `/admin/*`, static and media to the
backend; everything else is served by the SPA container. The whole stack runs
with a single `docker compose up --build`.

## Features

Implemented in the foundation:

- Email/password auth with JWT access & refresh tokens (rotation + blacklist)
  and scoped rate limiting on login/register/refresh (Redis-backed in prod)
- Custom `User` model (UUID PKs, avatar, timestamps)
- Multi-tenant data model with per-request company context (`X-Company-Id`
  header support) enforced at the queryset level
- Roles: **ADMIN / MANAGER / EMPLOYEE** with reusable DRF permission classes
- Initial domain models: Company, Membership, Customer, Project, Task
- Versioned API under `/api/v1/` with OpenAPI schema, Swagger UI and ReDoc
- Health endpoint (`/healthz/`) checking database and Redis
- Celery wiring with a reference task; eager mode in dev/tests
- React app shell: login flow, protected routes, sidebar/topbar layout,
  reusable UI kit, team directory backed by the live API
- pytest suite including dedicated tenant-isolation tests
- CI pipeline (lint → config validation → tests → build)

## Architecture

High-level shape:

```
Browser ──▶ nginx (edge)
              ├── /api/, /admin/, /static/, /media/, /healthz/ ──▶ Django (gunicorn) ──▶ PostgreSQL
              │                                              └──▶ Redis ◀── Celery worker
              └── everything else ──▶ frontend (nginx serving the SPA bundle)
```

Key decisions are documented in [docs/architecture/overview.md](docs/architecture/overview.md):

- Single-database, shared-schema tenancy keyed by a mandatory `company` FK
- Tenant scoping applied in `TenantScopedModelViewSet`, never in ad-hoc code
- Services own business logic; views/serializers stay thin
- Role checks centralized in permission classes, never hard-coded inline

## Tech Stack

| Layer      | Technology                                                        |
| ---------- | ----------------------------------------------------------------- |
| Backend    | Python 3.12+, Django 5.2, Django REST Framework, SimpleJWT         |
| Database   | PostgreSQL 17                                                     |
| Async      | Celery 5, Redis 7                                                 |
| Frontend   | React 19, TypeScript 5, Vite 6, Tailwind CSS 4                    |
| Data layer | TanStack Query 5, Axios, React Router 7                           |
| Infra      | Docker, Docker Compose, nginx                                     |
| Quality    | pytest, Ruff, ESLint, pre-commit, GitHub Actions                  |
| Docs       | drf-spectacular (OpenAPI 3), Swagger UI, ReDoc, Mermaid           |

## Project Structure

```
nexora/
├── backend/
│   ├── config/               # Project configuration
│   │   ├── settings/         # base / development / test / production
│   │   ├── celery.py
│   │   ├── urls.py           # Root URLConf incl. /api/v1/ router
│   │   └── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── core/             # Model bases, tenant context, permissions, health
│   │   ├── accounts/         # User model, auth endpoints, user directory
│   │   ├── companies/        # Company (tenant), Membership, roles
│   │   ├── customers/        # Customer CRUD (tenant-scoped)
│   │   ├── projects/         # Project CRUD (tenant-scoped)
│   │   ├── tasks/            # Task CRUD (tenant-scoped)
│   │   └── time_tracking/ documents/ notifications/   # Reserved domains
│   ├── tests/                # pytest suite (incl. tenant isolation)
│   ├── requirements/         # base / development / production
│   └── pyproject.toml        # Ruff + pytest configuration
├── frontend/
│   ├── src/
│   │   ├── components/ui/    # Design system (Button, Modal, Table, …)
│   │   ├── components/layout/# Sidebar, Navbar, UserMenu, PageHeader
│   │   ├── contexts/ hooks/  # Auth state, shared hooks
│   │   ├── features/         # Feature modules (auth, team): api clients
│   │   ├── layouts/pages/    # App shell + routed pages
│   │   ├── services/         # Axios instance, token storage, interceptors
│   │   └── types/ utils/
│   └── vite.config.ts
├── infrastructure/
│   ├── docker/               # Dockerfiles + backend entrypoint + SPA nginx
│   └── nginx/nginx.conf      # Edge proxy routing
├── docs/                     # architecture / api / development guides
├── scripts/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 22+
- A running PostgreSQL 16+ (or use Docker for just the database)

```bash
cp .env.example .env                       # then edit secrets

# --- backend ---
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver                 # http://localhost:8000

# --- frontend ---
cd ../frontend
npm install
npm run dev                                # http://localhost:5173
```

The Vite dev server proxies nothing: set `VITE_API_BASE_URL=http://localhost:8000/api/v1`
in `.env` when running the stack without the nginx edge.

Useful management commands live in the [Makefile](Makefile) — run `make help`.

## Environment Variables

All configuration flows through environment variables (see
[`.env.example`](.env.example)). Highlights:

| Variable                | Purpose                                        | Default            |
| ----------------------- | ---------------------------------------------- | ------------------ |
| `SECRET_KEY`            | Django signing key                             | dev-only fallback  |
| `DEBUG`                 | Debug mode                                     | `false`            |
| `DJANGO_SETTINGS_MODULE`| Settings module to load                        | per process        |
| `ALLOWED_HOSTS`         | Comma-separated hosts                          | localhost          |
| `CORS_ALLOWED_ORIGINS`  | Comma-separated origins                        | local Vite ports   |
| `POSTGRES_*`            | Database connection                            | nexora@localhost   |
| `REDIS_URL`             | Cache backend                                  | in-memory if unset |
| `REDIS_PASSWORD`        | Redis authentication (used by Docker Compose)  | dev default in Compose |
| `CELERY_BROKER_URL`     | Broker for Celery                              | falls back to Redis|
| `API_DOCS_ENABLED`      | Expose `/api/schema|docs|redoc/`               | on; **off in production** |
| `ADMIN_ENABLED`         | Serve the Django admin at `/admin/`            | on                 |
| `VITE_API_BASE_URL`     | Base URL baked into the frontend at build time | `/api/v1`          |

Production additionally honors `SECURE_SSL_REDIRECT` and enforces HSTS,
secure cookies and WhiteNoise-compressed static files
(`config/settings/production.py`). It refuses to boot without a real
`SECRET_KEY`.

## Running with Docker

```bash
cp .env.example .env       # adjust values
docker compose up --build
```

Then:

- Application: <http://localhost>
- API: <http://localhost/api/v1/>
- Swagger UI: <http://localhost/api/docs/> (development settings only — see below)
- Django admin: <http://localhost/admin/> (`make superuser` first)
- Health probe: <http://localhost/healthz/>

The backend container has **no published port**: nginx is the single public
edge and the backend is reachable only over the internal Docker network. To
debug the API directly from the host during development, use the loopback-only
overlay (`make up-dev`, equivalent to
`docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`,
which binds `127.0.0.1:8000`).

Redis inside Compose requires authentication: set `REDIS_PASSWORD` (strong,
random) for real deployments; empty falls back to a well-known development
password so the stack boots locally out of the box. Cache, Celery broker and
the health probe all receive authenticated URLs automatically.

Stop with `docker compose down` (add `-v` to wipe the database volume).

## Running Tests

Backend (SQLite in-memory by default; add `TEST_USE_POSTGRES=true` for PG):

```bash
cd backend && python -m pytest
```

Frontend type-check + build (acts as the frontend gate):

```bash
cd frontend && npm run build && npm run lint
```

Everything CI runs, locally:

```bash
make ci
```

## API Documentation

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

These endpoints are enabled in development and **disabled by default in
production** (404). Set `API_DOCS_ENABLED=true` to expose them in a
production-like deployment — preferably restricted at your TLS edge.

Endpoint groups (all under `/api/v1/`):

| Prefix        | Description                                        |
| ------------- | -------------------------------------------------- |
| `/auth/`      | register, token obtain/refresh/verify, me          |
| `/companies/` | current company retrieve/update (ADMIN for update) |
| `/users/`     | member directory of the active company             |
| `/customers/` | customer CRUD                                      |
| `/projects/`  | project CRUD                                       |
| `/tasks/`     | task CRUD                                          |

## Roadmap

1. **Projects & Tasks UI** — full CRUD screens over the existing APIs
2. **Customer UI** — list/detail/create/edit with server-side filtering
3. **Invitations** — email invites, membership lifecycle (MANAGER+)
4. **Time tracking** — time entries linked to projects/tasks; reports
5. **Documents** — file storage per company (S3-compatible backend)
6. **Notifications** — in-app + email via Celery
7. **Reporting** — dashboards aggregating projects/tasks/time
8. **Billing** — subscription plans per tenant

## Contributing

- Create feature branches from `main`; keep PRs focused
- Run `make ci` before pushing — CI must stay green
- Follow the existing patterns: thin views, logic in services, tenant scoping
  via the provided base classes
- Install pre-commit hooks once: `pre-commit install`

## License

[MIT](LICENSE)
