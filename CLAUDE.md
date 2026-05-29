# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard Studio is a BI platform with two main subsystems:
1. **Dashboard Designer** — Vue 3 SPA for creating ECharts dashboards connected to CubeJS
2. **Integration Flows** — Node-based visual editor for building ETL pipelines executed in Deno

Services: `dashboard-app` (Vue 3, port 3000) → `backend` (FastAPI, port 8000) + `cubejs` (port 4000), orchestrated by Traefik.

**Planned for v1.8:** A `bff/` (Node.js + Express) layer will sit between `dashboard-app` and the backend/CubeJS, taking over Keycloak auth and session management.

---

## Commands

### Frontend (`dashboard-app/`)

```bash
cd dashboard-app
npm run dev        # Dev server → http://localhost:3000
npm run build      # Production build
npm run preview    # Preview the build
```

### Backend (`backend/`)

```bash
cd backend
uv sync                                                          # Install deps
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 # Dev server

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Tests (unit tests only — no DB required)
uv run pytest tests/
uv run pytest tests/test_ods_executor.py -v    # Single test file
uv run pytest tests/ -k "test_append"          # Single test by name
```

### Docker

```bash
docker-compose up --build     # Start all services
docker-compose up backend     # Single service
```

---

## Architecture

### Request Flow (Current)

```
Browser
  └─ keycloak-js (PKCE in browser, token in sessionStorage)
  └─ dashboard-app (Vue 3, Vite)
       ├─ services/api.js  →  backend:8000/api/v1/*  (Bearer token from keycloak)
       └─ stores/cubejs.js →  cubejs:4000            (CubeJS JWT from backend config)
```

### Backend Structure

```
backend/app/
├── main.py          # FastAPI app, CORSMiddleware, lifespan (init DB + scheduler)
├── api/
│   ├── router.py    # Aggregates all routers under /api/v1
│   └── endpoints/   # One file per domain (dashboards, widgets, integration_flows, etc.)
├── core/
│   ├── config.py    # Pydantic Settings (env vars, keycloak URLs, DB URL)
│   ├── security.py  # verify_token() via Keycloak JWKS, auto-creates user on first login
│   ├── encryption.py # Fernet encryption for DataSource credentials (recursive on JSON)
│   └── database.py  # SQLAlchemy engine + SessionLocal
├── models/models.py # All SQLAlchemy models in one file (biportal schema)
├── services/
│   ├── deno_service.py        # Spawns Deno subprocess, sends flow JSON via stdin, parses signals
│   ├── ods_executor.py        # Append/Overwrite/Upsert to PostgreSQL (asyncpg)
│   ├── email_executor.py      # Jinja2 SandboxedEnvironment email sending
│   └── scheduler.py          # APScheduler with SQLAlchemy jobstore for cron flows
└── runtime/runner.ts          # Deno TypeScript — executes flow nodes (Script, ODS, Email, etc.)
```

### Deno Integration Pattern

When a flow runs, FastAPI sends a JSON payload to `deno runtime/runner.ts` via stdin. The Deno process executes nodes sequentially, streaming structured signals back to stdout:

```
EXEC_START → NODE_START → NODE_COMPLETE / NODE_ERROR → EXEC_COMPLETE
```

For Python-side operations (ODS writes, email sends), Deno emits special signals (`EXEC_ODS`, `EXEC_EMAIL`) that `deno_service.py` intercepts and dispatches to the appropriate Python executor.

### Authentication

`security.py` validates Keycloak JWTs by fetching JWKS from `{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs` (cached 1h). On first valid request, users are auto-created in the DB from token claims. Roles: `admin`, `designer`, `viewer`.

### Encryption

`core/encryption.py` uses Fernet (AES-128-CBC) with a PBKDF2-derived key. `process_sensitive_fields()` recursively encrypts/decrypts JSON dictionaries for keys: `password`, `api_key`, `client_secret`, `token`, `api_token`. DataSource configs are stored encrypted in PostgreSQL.

### Frontend Architecture

All state lives in Pinia stores (`src/stores/`). `api.js` is the single API client — all backend calls go through `apiRequest()` which injects the Keycloak Bearer token. The `@` alias maps to `src/`.

Key stores:
- `auth.js` — Keycloak session, user profile, roles
- `integrations.js` — Flow CRUD, execution state, real-time log streaming (SSE)
- `cubejs.js` — CubeJS client, schema meta, query execution
- `dashboard.js` — Dashboard and widget CRUD

The Flow Editor (`FlowEditorView.vue` + `FlowEditorCanvas.vue`) manages a visual canvas where nodes are dragged, connected, and configured. Node types are defined in `toolCatalog`.

### Database

All tables live in the `biportal` PostgreSQL schema. SQLAlchemy models in `backend/app/models/models.py`. Migrations managed by Alembic (`backend/alembic/versions/`).

---

## Key Env Variables

### Backend (`backend/.env`)
```
POSTGRES_HOST / _PORT / _USER / _PASSWORD / _DB / _SCHEMA
KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
KEYCLOAK_REALM=Apps
KEYCLOAK_CLIENT_ID=bi-backend
ENCRYPTION_KEY=<fernet-key>
DEBUG=false
```

### Frontend (`dashboard-app/.env`)
```
VITE_API_URL=http://localhost:8000
VITE_KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
VITE_KEYCLOAK_REALM=Apps
VITE_KEYCLOAK_CLIENT_ID=dashboard-app
```

---

## Conventions

- **Backend:** `uv` for dependency management (not pip/poetry). All endpoints use `Depends(get_current_user)` or `Depends(require_role([...]))` for auth.
- **Frontend:** `<script setup>` Composition API everywhere. No TypeScript. `<style scoped>` on all components. No external CSS framework — CSS custom properties in `assets/main.css`.
- **Migrations:** Always use Alembic for schema changes; never modify the DB directly.
- **Encryption:** Always use `process_sensitive_fields(data, "encrypt")` before storing DataSource configs; decrypt on read.

---

# DIRECTIVES YOU MUST FOLLOW

## THINK & CLARIFY
- Think before coding.
- State assumptions, ask if ambiguous.
- Push back if a simpler approach exists.
- Stop if confused; name what is unclear.

## GOAL-DRIVEN EXECUTION
- Clarify targets first.
- Turn vague goals into verifiable targets.
- E.g., "Add validation" → "Write tests for invalid inputs, then make them pass."

## SIMPLICITY FIRST
- Minimum code to solve.
- No speculative abstractions or unasked flexibility.
- The Test: Would a senior engineer find this overcomplicated?

## SURGICAL CHANGES
- Touch only what the task requires.
- Do not improve neighboring code or refactor what works.
- Every changed line traces back to the request.
