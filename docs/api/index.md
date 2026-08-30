# API Reference (v1)

Interactive documentation is served by the backend:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI 3 schema: `/api/schema/`

These endpoints are enabled in development and disabled (404) in production
unless `API_DOCS_ENABLED=true` is set.

## Conventions

- Base path: `/api/v1/`
- Auth: `Authorization: Bearer <access>` on every endpoint except
  `auth/register`, `auth/token*` and `/healthz/`.
- Tenant selection: optional `X-Company-Id: <company uuid>` header. Invalid or
  non-member values are ignored; the user's oldest active membership is used.
- Pagination: DRF page pagination (`?page=`, `?page_size=`, max 100).
- Filtering/search/ordering are enabled per viewset (`?is_active=`,
  `?search=`, `?ordering=-created_at`).
- Errors: DRF default payloads — `{"detail": "..."}` for auth/permission
  errors, field-keyed objects for validation errors. Login failures are
  uniform by design and never indicate which credential was wrong.
- Rate limiting: anonymous authentication endpoints are throttled per client
  IP (`auth/login` 10/min, `auth/register` 5/min, `auth/refresh` 30/min by
  default; configurable via `AUTH_THROTTLE_*` environment variables).
  Exceeding a limit returns `429 Too Many Requests`.

## Endpoint Map

| Method                | Path                        | Auth      | Notes                              |
| --------------------- | --------------------------- | --------- | ---------------------------------- |
| POST                  | `/auth/register/`           | anonymous | Creates user + company + ADMIN     |
| POST                  | `/auth/token/`              | anonymous | `{access, refresh, user}`          |
| POST                  | `/auth/token/refresh/`      | anonymous | Rotates refresh token              |
| POST                  | `/auth/token/verify/`       | anonymous |                                    |
| GET                   | `/auth/me/`                 | any user  | Profile + memberships + active co. |
| GET/PATCH             | `/companies/current/`       | member    | PATCH requires ADMIN               |
| GET                   | `/users/` ` /users/{id}/`   | member    | Directory incl. role               |
| CRUD                  | `/customers/`               | member    | DELETE requires MANAGER/ADMIN      |
| CRUD                  | `/projects/`                | member    | Cross-company customer rejected    |
| CRUD                  | `/tasks/`                   | member    | Assignee must be a company member  |
| GET                   | `/healthz/` (root, no v1)   | anonymous | DB + Redis status, 200/503         |

## Example Session

```bash
# Bootstrap a tenant
curl -sX POST http://localhost/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@acme.test","password":"Str0ng-Pass!","first_name":"Ada",
       "last_name":"Lovelace","company_name":"Acme Inc"}'

# Use the returned access token
TOKEN=...
curl -s http://localhost/api/v1/customers/ -H "Authorization: Bearer $TOKEN"

# Create a record (company is stamped server-side)
curl -sX POST http://localhost/api/v1/customers/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Globex GmbH"}'
```
