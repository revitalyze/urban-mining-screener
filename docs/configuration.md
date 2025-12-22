# Configuration

This document catalogs all configuration knobs for Urban Mining Screener (UMS), explains precedence rules, cookie security behavior, CORS, ports, and frontend build-time variables. Where decisions are pending, TODO placeholders are included.

- Secrets required at startup: APP_PASSWORD, AUTH_SECRET (the backend will fail fast if missing).
- ENV drives cookie security (Secure/SameSite mode).
- DATABASE_URL takes precedence over DB_* decomposition variables when provided.
- Frontend’s VITE_BACKEND_URL is a build-time variable set in the Dockerfile stage.

Key references:
- Settings loader: [`app/config.py`](../app/config.py)
- Cookie behavior: [`main.py:auth_login()`](../main.py:98)
- Static SPA serving (prod/Docker): [`main.py`](../main.py)
- Container entry/migrations: [`entrypoint.sh`](../entrypoint.sh)
- Compose port mappings: [`docker-compose.yml`](../docker-compose.yml)
- Frontend build-time endpoint: [`Dockerfile`](../Dockerfile)

## Environment variable catalog

Notes:
- Type indicates expected string/number form.
- Default reflects code defaults if env is not set; .env.example may propose different local dev values.
- Required means application will not start without a sensible value.
- Source indicates where this variable is consumed or defined.

| Name | Type |                                    Default | Required | Description | Source |
|---|---|-------------------------------------------:|:---:|---|---|
| DB_USER | string |                                     "user" | No | Database user when composing DATABASE_URL from parts. | [`app/config.py`](../app/config.py) |
| DB_PASSWORD | string |                                 "password" | No | Database password when composing DATABASE_URL from parts. | [`app/config.py`](../app/config.py) |
| DB_NAME | string |                                   "ums_db" | No | Database name when composing DATABASE_URL from parts. | [`app/config.py`](../app/config.py) |
| DB_HOST | string |                                 "postgres" | No | Database host when composing DATABASE_URL from parts (in Docker, service name differs). | [`app/config.py`](../app/config.py) |
| DB_PORT | int |                                       5432 | No | Database port when composing DATABASE_URL from parts. | [`app/config.py`](../app/config.py) |
| DATABASE_URL | string |                          Derived from DB_* | No | Full DSN; if set, this takes precedence over DB_* parts. Example: postgresql://user:password@host:5432/ums_db | [`app/config.py`](../app/config.py) |
| APP_PASSWORD | string |                                          — | Yes | Password required for login; validates requests to issue signed session cookie. | [`main.py:auth_login()`](../main.py:98) |
| AUTH_SECRET | string |                                          — | Yes | Secret for signing auth cookie with itsdangerous serializer. | [`main.py:auth_login()`](../main.py:98) |
| ENV | string |                              "development" | No | Controls cookie security (production vs non-production) and static serving switch. Expected: development, docker, production. | [`main.py`](../main.py) |
| BACKEND_PORT | int |                                       8000 | No | Host port mapping for backend via Compose: ${BACKEND_PORT:-8000}:8000. Not read by the app itself. | [`docker-compose.yml`](../docker-compose.yml) |
| POSTGRES_PORT | int |                                       5432 | No | Host port mapping for PostgreSQL via Compose: ${POSTGRES_PORT:-5432}:5432. | [`docker-compose.yml`](../docker-compose.yml) |
| POSTGRES_USER | string |                                     "user" | No | Environment to postgres container; for DB bootstrap in Compose. | [`docker-compose.yml`](../docker-compose.yml) |
| POSTGRES_PASSWORD | string |                                 "password" | No | Environment to postgres container; for DB bootstrap in Compose. | [`docker-compose.yml`](../docker-compose.yml) |
| POSTGRES_DB | string |                                   "ums_db" | No | Environment to postgres container; for DB bootstrap in Compose. | [`docker-compose.yml`](../docker-compose.yml) |
| VITE_BACKEND_URL | string (URL) |                                         "" | No | Frontend build-time API base URL. Set during Docker frontend build stage. Must be changed and image rebuilt to adjust. | [`Dockerfile`](../Dockerfile) |

## Database URL precedence

- If DATABASE_URL is set, it will be used as-is.
- If DATABASE_URL is not set, the application composes it from DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME.
- Example composition: postgresql://user:password@postgres:5432/ums_db

Examples:
- Full DSN:
  - DATABASE_URL=postgresql://user:pass@localhost:5432/ums_db
- From parts (local):
  - DB_USER=user
  - DB_PASSWORD=pass
  - DB_HOST=localhost
  - DB_PORT=5432
  - DB_NAME=ums_db

Compose-specific:
- The app service sets DB_HOST to ums_postgres so the app container can reach the postgres container by service name. See [`docker-compose.yml`](../docker-compose.yml).

## Authentication cookie behavior

Cookie issuance occurs in [`main.py:auth_login()`](../main.py:98). The helper `_is_cookie_secure()` returns True only when ENV == "production". Behavior:

- production:
  - secure=True
  - SameSite="none" (required when using Secure cookies across sites)
  - HTTPS required for cookie acceptance by modern browsers
- development or docker:
  - secure=False
  - SameSite="lax"
  - Works with http://localhost origins and typical local dev setups

Operational guidance:
- For production deployments behind TLS, ensure ENV=production and serve over HTTPS so the browser accepts Secure cookies.
- For local dev, ENV should remain development (default) or docker (Compose sets ENV=docker).

## CORS configuration

Current behavior:
- The backend explicitly configures CORS allow_origins and allow_origin_regex in code to support:
  - http://localhost:5173 (Vite dev)
  - http://localhost:3000
  - http://localhost:8080
  - http://127.0.0.1:8000

Recommendations:
- For local dev, use the Vite dev server at http://localhost:5173 and backend at http://localhost:8000 (CORS is already allowed).

## Ports and networking

- Backend dev (uvicorn): 8000
- Frontend dev (Vite): 5173
- PostgreSQL (Compose): 5432 (host-mapped)
- Docker backend mapping: ${BACKEND_PORT:-8000}:8000 (host:container)

See [`docker-compose.yml`](../docker-compose.yml) for mappings and network name.

## Frontend build-time API base URL

VITE_BACKEND_URL is compiled into the frontend during build. In this repository, it is set in the frontend build stage of the Dockerfile:

- [`Dockerfile`](../Dockerfile) sets:
  - ENV VITE_BACKEND_URL=""
- To change the production API target, edit the ENV line in the Dockerfile and rebuild the image.

Local development:
- When running `npm run dev` in the frontend, calls can be made directly to http://localhost:8000 (CORS allowed) or proxied via Vite dev server.

## Configuration examples

Minimal .env for local development (using part-based DB variables):
```
APP_PASSWORD=change-me
AUTH_SECRET=use-a-random-long-secret
DB_USER=user
DB_PASSWORD=password
DB_NAME=ums_db
DB_HOST=localhost
DB_PORT=5432
# Optional: DATABASE_URL=postgresql://user:password@localhost:5432/ums_db
```

Compose-backed local run (backend + postgres):
```
# .env used by docker compose
APP_PASSWORD=test
AUTH_SECRET=testtest
BACKEND_PORT=8000
POSTGRES_PORT=5432
# DB_* will be overridden by compose service environment for the app:
#   DB_HOST=ums_postgres, DB_PORT=5432, DB_NAME=ums_db, DB_USER=user, DB_PASSWORD=password
```

Production environment (example):
```
ENV=production
APP_PASSWORD=${STRONG_PASSWORD}
AUTH_SECRET=${LONG_RANDOM_SECRET}
DATABASE_URL=postgresql://ums:${DB_PASS}@${DB_HOST}:${DB_PORT}/ums_prod
```

## Warnings and best practices

- Do not commit real secrets (APP_PASSWORD, AUTH_SECRET, DATABASE_URL).
- Use HTTPS in production to satisfy Secure cookie requirements.
- Ensure DATABASE_URL uses credentials with least privilege.
- Keep ENV=production only in secure deployments; otherwise use development or docker.

## Related files

- Settings and env loading: [`app/config.py`](../app/config.py)
- Cookie issuance and SameSite/Secure toggle: [`main.py:auth_login()`](../main.py:98)
- Compose environment and ports: [`docker-compose.yml`](../docker-compose.yml)
- Entrypoint migrations: [`entrypoint.sh`](../entrypoint.sh)
- Frontend build-time endpoint: [`Dockerfile`](../Dockerfile)