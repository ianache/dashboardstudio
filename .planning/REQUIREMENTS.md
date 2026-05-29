# Requirements: Dashboard Studio v1.8

**Defined:** 2026-05-28
**Core Value:** BFF concentra auth y session management, expone API unificada al frontend — el browser nunca ve tokens

## v1.8 Requirements

Requirements for the BFF Service Architecture milestone. Each maps to roadmap phases.

### BFF Infrastructure

- [ ] **BFF-01**: User can access the dashboard app through a BFF service deployed as an Express 5 Node.js server
- [ ] **BFF-02**: BFF service is containerized and included in docker-compose alongside backend, frontend, and CubeJS
- [ ] **BFF-03**: Server-side sessions are persisted in PostgreSQL via `connect-pg-simple` with HttpOnly secure cookie delivered to browser
- [ ] **BFF-04**: BFF configuration is fully externalized via environment variables (Keycloak URLs, client credentials, session secret, CubeJS secret)

### Authentication

- [ ] **AUTH-01**: User can initiate login via BFF which redirects to Keycloak (OIDC authorization code flow + PKCE)
- [ ] **AUTH-02**: User is redirected to BFF callback after Keycloak auth; server-side session is established (state/nonce/PKCE validated)
- [ ] **AUTH-03**: User session state can be checked via `GET /bff/auth/me`, returning user profile when authenticated
- [ ] **AUTH-04**: User access tokens are silently refreshed server-side before expiry (transparent to frontend)
- [ ] **AUTH-05**: User can logout via BFF which destroys local session and redirects to Keycloak end-session endpoint

### Proxy

- [ ] **PROXY-01**: All FastAPI backend routes are accessible via BFF at `/bff/api/*` with Bearer token injected from session
- [ ] **PROXY-02**: CubeJS queries are proxied via BFF at `/bff/cubejs/*` with per-request HS256 JWT signed server-side (token never reaches browser)
- [ ] **PROXY-03**: CORS is handled exclusively by BFF; upstream CORS headers from FastAPI are stripped on proxy response

### Frontend Migration

- [ ] **FE-01**: Frontend no longer uses `keycloak-js` adapter; `keycloak.js` service deleted, Keycloak init removed from `main.js`
- [ ] **FE-02**: Frontend API calls (`api.js`) route through BFF base URL with `credentials: 'include'` for session cookie transmission
- [ ] **FE-03**: Frontend CubeJS store (`cubejs.js`) no longer manages tokens; queries proxied through BFF
- [ ] **FE-04**: Frontend auth store uses `authStore.initialized` flag with `/bff/auth/me` session check; router guards updated accordingly

### Backend Cleanup

- [ ] **BE-01**: FastAPI `CORSMiddleware` targeting SPA origin is removed (BFF is sole CORS handler)
- [ ] **BE-02**: Backend service is restricted to internal docker network (not publicly exposed); only reachable from BFF

## Future Requirements

### Observability
- **OBS-01**: BFF logs all proxied requests with user context (user ID, route, response time)
- **OBS-02**: BFF exposes health check endpoint (`/bff/health`) for container orchestration

### Scalability
- **SCALE-01**: BFF session store migrated to Redis for horizontal scaling support
- **SCALE-02**: BFF stateless token validation (no session lookup for internal service calls)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Redis session store | PostgreSQL covers current single-instance deployment; Redis added when horizontal scaling needed |
| Business logic in BFF | BFF is a pass-through — no domain logic; FastAPI owns all business logic |
| JWT-signed cookies | Server-side sessions with HttpOnly cookies chosen; JWT cookies expose token data to browser |
| Per-user CubeJS queryRewrite | Requires CubeJS schema changes; can be addressed in a follow-up if needed |
| Keycloak admin API calls from BFF | BFF is a client, not an admin; user management stays in FastAPI/Keycloak |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BFF-01 | Phase 33 | Pending |
| BFF-02 | Phase 33 | Pending |
| BFF-03 | Phase 33 | Pending |
| BFF-04 | Phase 33 | Pending |
| AUTH-01 | Phase 34 | Pending |
| AUTH-02 | Phase 34 | Pending |
| AUTH-03 | Phase 34 | Pending |
| AUTH-04 | Phase 34 | Pending |
| AUTH-05 | Phase 34 | Pending |
| PROXY-01 | Phase 35 | Pending |
| PROXY-03 | Phase 35 | Pending |
| BE-01 | Phase 35 | Pending |
| PROXY-02 | Phase 36 | Pending |
| BE-02 | Phase 36 | Pending |
| FE-01 | Phase 37 | Pending |
| FE-02 | Phase 37 | Pending |
| FE-03 | Phase 37 | Pending |
| FE-04 | Phase 37 | Pending |

**Coverage:**
- v1.8 requirements: 18 total
- Mapped to phases: 18/18 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-28*
*Last updated: 2026-05-28 — traceability filled after roadmap creation*
