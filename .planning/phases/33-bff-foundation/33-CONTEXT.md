# Phase 33: BFF Foundation - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

A deployable BFF Express 5 service scaffolded in `bff/`, running as a Docker Compose service with health checks, PostgreSQL-backed server-side sessions, and all configuration read from environment variables. No auth flows, no proxying, no frontend migration — those are Phases 34–37.

</domain>

<decisions>
## Implementation Decisions

### Traefik Exposure
- BFF gets a public Traefik label and hostname in Phase 33: `dashboard-bff.pm.comsatel.com.pe`
- Entrypoint: `web-secure` with TLS (same as backend)
- Internal port: `3001`
- BFF joins both `frontends` and `backends` Docker networks (same pattern as the `backend` service)
- `frontend-app` service gets `depends_on: bff` added in Phase 33 (establishing the future dependency early)

### Session Cookie Policy
- `SameSite=Lax` — BFF and frontend share the `.pm.comsatel.com.pe` parent domain
- Cookie name: `bff.sid`
- Cookie domain: `.pm.comsatel.com.pe` (shared across all `*.pm.comsatel.com.pe` subdomains so Phase 34 auth callbacks work seamlessly)
- Session TTL: 8 hours (maxAge = 28800000 ms)
- HttpOnly: true, Secure: true

### Env File Strategy
- BFF gets its own `.env-bff` file (follows existing `.env-backend` pattern)
- `.env-bff` is gitignored; `.env-bff.example` with placeholder values is committed
- All BFF vars use `BFF_` prefix (e.g., `BFF_SESSION_SECRET`, `BFF_KEYCLOAK_URL`)
- BFF uses its own `BFF_POSTGRES_*` vars for the session store DB connection (same instance as backend, but independently declared)

### BFF Base Path
- All BFF routes namespaced under `/bff/` prefix (e.g., `/bff/health`, future `/bff/auth/*`, `/bff/api/*`)
- Health check: `GET /bff/health` → `{ "status": "ok" }` JSON, 200
- Express server listens on port `3001` inside Docker

### Claude's Discretion
- Node.js image version (node:20-alpine, consistent with frontend build stage)
- npm as package manager (consistent with existing)
- Express app internal directory structure (`src/`, `src/routes/`, `src/middleware/`)
- Dockerfile multi-stage vs single-stage (single-stage is fine for a server)
- connect-pg-simple session table name (default `session` in the `biportal` schema is fine)
- Exact `BFF_POSTGRES_*` var names beyond the agreed prefix

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing BFF code — `bff/` directory does not exist yet, full scaffold required

### Established Patterns
- **Dockerfile pattern**: Backend uses `python:3.11-slim`, frontend uses `node:20-alpine` for build. BFF should use `node:20-alpine` (server, not build stage)
- **env_file pattern**: Backend uses `env_file: ./.env-backend` in docker-compose. BFF should use `env_file: ./.env-bff`
- **Docker networks**: Both `frontends` and `backends` are declared `external: true` — BFF joins both, same as backend
- **Traefik pattern**: Backend uses `traefik.http.routers.{name}.entrypoints: web-secure` + `tls: true`. BFF follows same pattern with router name `bff`
- **PostgreSQL**: Backend uses `biportal` schema — connect-pg-simple session table should live in `biportal` schema too for consistency

### Integration Points
- `docker-compose.yaml` — add `bff` service, add `depends_on: bff` to `frontend-app`
- `.gitignore` — add `.env-bff`
- `bff/` — new directory, owns its own `package.json`, `Dockerfile`, `src/`

</code_context>

<specifics>
## Specific Ideas

- BFF Express server at port 3001 (doesn't conflict with frontend:3000, backend:8000, CubeJS:4000)
- Session cookie domain `.pm.comsatel.com.pe` is critical for Phase 34 Keycloak auth callbacks to work without cross-domain cookie issues
- `.env-bff.example` should document all `BFF_*` vars with descriptions, not just placeholders

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 33-bff-foundation*
*Context gathered: 2026-05-28*
