# Development Guide

## Setup

See the README's [Local Development](../../README.md#local-development) section
for first-time setup. Day-to-day shortcuts live in the Makefile (`make help`).

## Backend Conventions

### App layout

Each domain app under `apps/` follows the same shape:

```
apps/<domain>/
├── models.py            # data + integrity (constraints, indexes)
├── services.py          # business logic (transactions live here)
├── admin.py
├── api/
│   ├── serializers.py   # request/response shapes + field validation
│   ├── views.py         # thin orchestration over services/querysets
│   └── urls.py          # router registration for this app
└── migrations/
```

Rules of thumb:

1. **Tenant scoping is inherited, never re-implemented.** Business entities
   extend `apps.core.db.models.TenantedModel` and their viewsets extend
   `TenantScopedModelViewSet`. That alone gives correct isolation.
2. **Business logic goes in services**, not views or serializer `create()`.
3. **Role checks go through permission classes** (`role_required(...)`), so
   they stay greppable and testable in one place.
4. Migrations are committed alongside model changes; CI fails on missing ones.

### Adding a new domain module (checklist)

1. `python manage.py startapp <domain> apps/<domain>` then set
   `name = "apps.<domain>"` in its `AppConfig`.
2. Register the app in `config/settings/base.py`.
3. Model extends `TenantedModel`; add indexes/constraints.
4. Serializer + `SomeViewSet(TenantScopedModelViewSet)`.
5. Router registration included from `config/urls.py`.
6. Tests: at minimum list/detail isolation cases (copy the pattern from
   `backend/tests/test_tenant_isolation.py`).

## Frontend Conventions

- **UI kit first**: build screens from `src/components/ui/*`. If you need a
  new variant, extend the component rather than inlining styles.
- **Server state via TanStack Query**: define query functions in
  `src/features/<domain>/api.ts`, consume with `useQuery`/`useMutation`.
- **Types mirror the API** in `src/types/*.ts` (snake_case fields on purpose —
  no client-side renaming layer until it pays for itself).
- Route additions go through `src/App.tsx`; authenticated pages render inside
  `AppLayout`.

## Code Style

- Backend: Ruff (lint + format), line length 100, type hints where useful.
  `cd backend && ruff check . --fix && ruff format .`
- Frontend: ESLint (flat config). `cd frontend && npm run lint`
- EditorConfig keeps whitespace consistent across editors.

Install git hooks once: `pre-commit install`.

## Testing

- Backend tests live in `backend/tests/`, grouped by domain. Fixtures shared
  by suites sit in `tests/conftest.py` (`tenant`, `auth_client`, factories).
- The tenant-isolation suite is the regression net that matters most; when you
  add an entity, parametrize those tests over it.
- Run: `make test`

## Debugging Tips

- Django shell with real env: `make shell`
- Follow all logs: `make logs`
- Hit health probe inside the stack:
  `docker compose exec backend curl -s localhost:8000/healthz/` — the backend
  has no published host port; use `make up-dev` for a loopback-only
  `127.0.0.1:8000` mapping during local debugging
- Celery eager mode locally: keep `CELERY_TASK_ALWAYS_EAGER=false`; tasks run
  through Redis in Docker, inline otherwise.

## Development vs Production Behavior

| Surface                     | Development                              | Production (`config.settings.production`)            |
| --------------------------- | ---------------------------------------- | ---------------------------------------------------- |
| Backend port                | `make up-dev` binds `127.0.0.1:8000`     | not published; nginx is the only edge                 |
| Redis                       | Compose default dev password             | set `REDIS_PASSWORD` (strong value)                   |
| `/api/schema|docs|redoc/`   | enabled                                  | **disabled** unless `API_DOCS_ENABLED=true`           |
| Django admin                | enabled                                  | enabled; fully removable via `ADMIN_ENABLED=false`    |
| SPA security headers        | always on (frontend nginx snippet)       | same, plus TLS/HSTS at the terminating layer          |
| HSTS                        | never advertised over plain HTTP         | emitted only on HTTPS requests (via `X-Forwarded-Proto`) |

Toggles are read per request (`apps.core.api.middleware.SurfaceExposureMiddleware`),
so flipping `API_DOCS_ENABLED` / `ADMIN_ENABLED` takes effect without a restart.
