# Installation and Setup

This guide explains how to set up Urban Mining Screener (UMS) for local development and Docker-based runs. It also covers migrations, ports, and troubleshooting for CORS, cookies, and database connectivity.

- Frontend dev server: Vite on port 5173
- Backend dev server: FastAPI (uvicorn) on port 8000
- Database: PostgreSQL 16 (via Docker or local instance)
- Migrations: Alembic executed automatically at container startup by [entrypoint.sh](../entrypoint.sh)

Important files:
- Docker orchestration: [docker-compose.yml](../docker-compose.yml)
- Container build: [Dockerfile](../Dockerfile)
- Env example: [.env.example](../.env.example)
- Backend entry: [main.py](../main.py)
- CORS/settings: [app/config.py](../app/config.py)
- Frontend config: [frontend/vite.config.ts](../frontend/vite.config.ts), [frontend/package.json](../frontend/package.json)

## Prerequisites

- Python 3.11
- Node.js 18+ (recommended 20)
- Docker 24+
- Docker Compose v2
- PostgreSQL (only required if not using Docker Compose)

## Repository-specific notes

- In Docker/production, the SPA (frontend build) is served statically by the backend at the root path ("/"). See static mount behavior in [main.py](../main.py).
- The container startup script will check database connectivity and run Alembic migrations automatically. See [entrypoint.sh](../entrypoint.sh).
- CORS is permissive for local development and selected deployment domains. See [main.py](../main.py) and [app/config.py](../app/config.py).
- The backend requires secrets to start (APP_PASSWORD and AUTH_SECRET). See [app/config.py](../app/config.py).

## 1) Environment setup

1. Create a local environment file:
   - Copy the example:
     - macOS/Linux:
       - cp .env.example .env
     - Windows (PowerShell):
       - Copy-Item .env.example .env

2. Edit .env to set database credentials and secrets:
   - Required:
     - APP_PASSWORD=… (password required to log in via the backend)
     - AUTH_SECRET=… (random string for cookie signing)
   - Optional / DB (if running locally without compose):
     - DB_USER=user
     - DB_PASSWORD=password
     - DB_NAME=ums_db
     - DB_HOST=localhost
     - DB_PORT=5432
   - Alternatively, set a full DATABASE_URL. See precedence in the Configuration guide.

See default examples in [.env.example](../.env.example).

## 2) Local development (Backend)

1. Create and activate a virtual environment (example with venv):
   - python3 -m venv .venv
   - source .venv/bin/activate  (macOS/Linux)
   - .venv\Scripts\Activate.ps1 (Windows PowerShell)

2. Install dependencies:
   - pip install --upgrade pip
   - pip install -r requirements.txt

3. Ensure your database is reachable:
   - If you’re using a local PostgreSQL, make sure DB_* variables are set correctly in .env and the DB is running.
   - If using Docker Compose for DB only, you can start just the postgres service via compose. See [docker-compose.yml](../docker-compose.yml).

4. Run Alembic migrations (local-only; Docker does this automatically):
   - alembic upgrade head

5. Start the backend in dev mode:
   - uvicorn main:app --reload --port 8000

Backend is now available at:
- http://127.0.0.1:8000
- OpenAPI docs: http://127.0.0.1:8000/docs

Note on authentication: The backend issues a signed session cookie when you POST to /auth/login with the configured APP_PASSWORD. Cookie behavior varies by environment (SameSite/Lax in development). See the Configuration guide and [main.py](../main.py).

## 3) Local development (Frontend)

1. Install Node dependencies:
   - cd frontend
   - npm install

2. Start Vite dev server:
   - npm run dev

3. Access the app:
   - http://localhost:5173

The frontend will call the backend at your configured base URL. For local development:
- Either configure API calls to http://localhost:8000 and rely on CORS (allowed in [main.py](../main.py))

Note on Vite build-time env:
- VITE_* variables are compiled at build time. For production builds, see the Docker section and the Configuration guide.

## 4) Docker (local all-in-one)

This repository ships with a Compose setup for PostgreSQL + Backend (serving the built SPA). The compose file expects an application image named ums:local.

1. Build the image (required before compose up):
   - docker build -t ums:local .

   Notes:
   - The frontend is built in the first stage of the [Dockerfile](../Dockerfile) and copied into /app/static_root of the final image.
   - The build stage sets ENV VITE_BACKEND_URL (default points to an no URL). To change the production API endpoint, edit the ENV line in [Dockerfile](../Dockerfile) before building.

2. Start services:
   - docker compose up -d

   Defaults:
   - Backend mapped to host port: ${BACKEND_PORT:-8000} (see [docker-compose.yml](../docker-compose.yml))
   - Postgres mapped to host port: ${POSTGRES_PORT:-5432}

3. Verify:
   - Backend health/docs: http://127.0.0.1:8000/docs
   - SPA is served by the backend at http://127.0.0.1:8000/

4. Environment:
   - Compose reads .env and also sets ENV=docker, APP_PASSWORD, AUTH_SECRET in [docker-compose.yml](../docker-compose.yml). You can adjust these in your .env and compose file.
   - Database service data persists in the postgres_data volume.

5. Logs:
   - docker compose logs -f app
   - docker compose logs -f postgres

6. Stop:
   - docker compose down

## 5) Database migrations

- Docker: Automatically executed at container startup by [entrypoint.sh](../entrypoint.sh), which:
  - Runs a DB connectivity check (app.check_db)
  - Executes alembic upgrade head
  - Starts uvicorn on 0.0.0.0:8000

- Local dev: Run Alembic manually before starting the backend:
  - alembic upgrade head

If you change models or import new CSVs altering schema, create Alembic revisions and upgrade accordingly.

## 6) Ports matrix

- Backend dev: 8000 (uvicorn)
- Frontend dev: 5173 (Vite)
- Postgres dev (compose): 5432
- Docker backend: exposed as ${BACKEND_PORT:-8000} to host, internal in-container port is 8000 (see [docker-compose.yml](../docker-compose.yml) and [Dockerfile](../Dockerfile))

## 7) Troubleshooting

CORS (Cross-Origin Resource Sharing):
- Symptom: Browser errors like “CORS policy” when calling backend from Vite dev server.
- Resolution:
  - Ensure you are accessing the frontend at an origin allowed by backend CORS (localhost:5173 is explicitly allowed in [main.py](../main.py)).
  - For custom hostnames/ports, either:
    - Add them via environment (CORS_ORIGINS, CORS_ORIGIN_REGEX). See [app/config.py](../app/config.py) and Configuration guide, or
    - Use a Vite dev proxy to http://localhost:8000 to avoid cross-origin calls.

Cookies (SameSite / Secure):
- Symptom: Login not persisting; cookie not set or blocked.
- Behavior:
  - In development/docker (non-production), cookies are issued with SameSite=Lax and Secure=False.
  - In production (ENV=production), cookies are issued with SameSite=None and Secure=True, requiring HTTPS.
- Resolution:
  - Use HTTPS in production to allow Secure cookies.
  - For local development, use the Vite dev server at http://localhost:5173 and backend at http://localhost:8000 (works with SameSite=Lax).
  - If embedding the app cross-site, ensure production HTTPS and SameSite=None are satisfied.

Database connectivity:
- Symptom: Startup error “Missing required environment variables: APP_PASSWORD, AUTH_SECRET” or DB connection errors.
- Resolution:
  - Set APP_PASSWORD and AUTH_SECRET in your environment or .env before starting.
  - Verify DB_* variables or DATABASE_URL are correct and reachable from the backend.
  - With Docker Compose, the backend DB_HOST should be ums_postgres (see [docker-compose.yml](../docker-compose.yml)). Without compose, use localhost and ensure port 5432 is open.

Image not found on docker compose up:
- Symptom: Error that image ums:local cannot be found.
- Resolution:
  - Build the image first: docker build -t ums:local .

Frontend calling wrong backend in Docker:
- Symptom: SPA tries to call cloud URL or wrong host.
- Cause: VITE_BACKEND_URL is set at build time in the Dockerfile stage.
- Resolution:
  - Edit [Dockerfile](../Dockerfile) to set the desired VITE_BACKEND_URL and rebuild the image.

## 8) Quickstart

Local (two terminals):
- Terminal A (backend):
  - python3 -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
  - alembic upgrade head
  - uvicorn main:app --reload --port 8000
- Terminal B (frontend):
  - cd frontend
  - npm install
  - npm run dev
- Open http://localhost:5173

Docker (single terminal):
- docker build -t ums:local .
- docker compose up -d
- Open http://127.0.0.1:8000

## 9) Next steps

- Read Configuration: [docs/configuration.md](configuration.md)
- Learn how to use the app: [docs/user-guide.md](user-guide.md)
- Understand architecture: [docs/architecture.md](architecture.md)