# Project Roadmap: Dashboard Studio

## Milestones

- ✅ **v1.6 ODS Execution Engine** — Phases 29-31 (shipped 2026-05-17)
- ✅ **v1.7 Email Node** — Phase 32 (shipped 2026-05-17)
- 🚧 **v1.8 BFF Service Architecture** — Phases 33-37 (in progress)

## Progress Table

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-28. Core & Extensions | Pre-v1.6 | 28/28 | Complete | 2026-05-17 |
| 29. Metadata Inspection API | v1.6 | 2/2 | Complete | 2026-05-16 |
| 30. ODS Node UI Enhancement | v1.6 | 1/1 | Complete | 2026-05-16 |
| 31. ODS Execution Engine | v1.6 | 3/3 | Complete | 2026-05-17 |
| 32. Email Node Implementation | v1.7 | 3/3 | Complete | 2026-05-17 |
| 33. BFF Foundation | v1.8 | 0/TBD | Not started | - |
| 34. Keycloak Auth Flow | v1.8 | 0/TBD | Not started | - |
| 35. FastAPI Proxy + CORS | v1.8 | 0/TBD | Not started | - |
| 36. CubeJS Proxy + Network Isolation | v1.8 | 0/TBD | Not started | - |
| 37. Frontend Migration | v1.8 | 0/TBD | Not started | - |

---

## ✅ v1.6 ODS Execution Engine (Phases 29-31) — SHIPPED 2026-05-17

<details>
<summary>View v1.6 Details</summary>

### Phase 29: Metadata Inspection API
**Goal**: Implement backend services to inspect database schemas, tables, and columns.
**Requirements**: FR-01, FR-04, TR-01
**Status**: Complete
**Plans**: 2 plans
- [x] 29-01-PLAN.md — Implement MetadataService with PostgreSQL support.
- [x] 29-02-PLAN.md — Expose metadata inspection via FastAPI endpoints.

### Phase 30: ODS Node UI Enhancement
**Goal**: Update the ODS PostgreSQL node properties with dynamic selectors and conditional fields.
**Requirements**: FR-01, FR-02, FR-03, FR-04, TR-02, TR-03, UI
**Status**: Complete
**Plans**: 1 plan
- [x] 30-PLAN.md — Update ODS node UI with dynamic selectors, refresh buttons, and conditional identity fields.

### Phase 31: ODS Execution Engine
**Goal**: Implement the actual write/upsert logic in the backend with Deno delegation.
**Requirements**: FR-05, FR-06, TR-04, EXEC-01 through EXEC-21
**Status**: Complete
**Plans**: 3 plans in 3 waves
- [x] 31-01-PLAN.md — Core ODSExecutor Service (ods_executor.py with Append, Overwrite, Upsert)
- [x] 31-02-PLAN.md — Deno Integration & Signal Protocol (runner.ts, deno_service.py)
- [x] 31-03-PLAN.md — Validation, Testing & Hardening (validation, logging, tests, deprecation)

**Archive:** `.planning/milestones/v1.6-ROADMAP.md`

</details>

---

## ✅ v1.7 Email Node with Dynamic Templates (Phase 32) — SHIPPED 2026-05-17

<details>
<summary>View v1.7 Details</summary>

### Phase 32: Email Node Implementation
**Goal**: Implementar el nodo Email con soporte para plantillas dinámicas usando Jinja2, permitiendo el envío de correos con contenido generado dinámicamente desde el input del flujo.
**Requirements**: EMAIL-01 through EMAIL-24
**Status**: Complete
**Plans**: 3 plans in 3 waves
- [x] 32-01-PLAN.md — Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration)
- [x] 32-02-PLAN.md — Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [x] 32-03-PLAN.md — UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

**Archive:** `.planning/milestones/v1.7-ROADMAP.md`

</details>

---

## 🚧 v1.8 BFF Service Architecture (Phases 33-37)

**Milestone Goal:** Introduce a Node.js + Express BFF layer between the Vue 3 SPA and all backend services, concentrating Keycloak OIDC auth, server-side session management, and full API proxying in a single entry point. The browser never sees a token.

**Build order constraint:** BFF Foundation → Auth Flow → FastAPI Proxy → CubeJS Proxy → Frontend Migration (last; irreversible).

## Phases

- [ ] **Phase 33: BFF Foundation** - BFF service scaffolded, containerized, and connected to PostgreSQL session store
- [ ] **Phase 34: Keycloak Auth Flow** - Full OIDC Authorization Code + PKCE cycle working end-to-end server-side
- [ ] **Phase 35: FastAPI Proxy + CORS Consolidation** - All backend routes accessible via BFF; CORS owned exclusively by BFF
- [ ] **Phase 36: CubeJS Proxy + Network Isolation** - CubeJS queries proxied with server-side JWT signing; backend removed from public network
- [ ] **Phase 37: Frontend Migration** - Vue 3 SPA removes keycloak-js entirely; all calls routed through BFF

## Phase Details

### Phase 33: BFF Foundation
**Goal**: A deployable BFF Express service exists in `bff/`, runs as a Docker Compose service with proper health checks, persists sessions in PostgreSQL, and reads all configuration from environment variables.
**Depends on**: Phase 32 (existing project infrastructure)
**Requirements**: BFF-01, BFF-02, BFF-03, BFF-04
**Success Criteria** (what must be TRUE):
  1. Running `docker-compose up bff` starts the BFF container without errors and it responds to requests
  2. Session data written by the BFF is visible in the PostgreSQL `session` table after a request
  3. The BFF reads Keycloak URLs, client credentials, session secret, and CubeJS secret from environment variables with no hardcoded values
  4. The BFF is listed in the `backends` and `frontends` Docker networks alongside `backend` and `cubejs` services
**Plans**: TBD

Plans:
- [ ] 33-01: BFF scaffold — Express 5 app structure, package.json, Dockerfile, docker-compose integration
- [ ] 33-02: Session store — connect-pg-simple setup, session table migration, HttpOnly cookie configuration

### Phase 34: Keycloak Auth Flow
**Goal**: Users can log in via Keycloak through the BFF, have their session established server-side, check their session state via `/bff/auth/me`, get tokens silently refreshed, and log out completely — all without the browser ever receiving a token.
**Depends on**: Phase 33
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05
**Success Criteria** (what must be TRUE):
  1. Visiting `/bff/auth/login` redirects the browser to the Keycloak login page with a valid PKCE `code_challenge`
  2. After successful Keycloak login, the browser is redirected to `/bff/auth/callback`, the session is established, and an HttpOnly cookie is set
  3. `GET /bff/auth/me` returns `{ sub, email, name, roles }` for an authenticated session and 401 for an unauthenticated request
  4. Access tokens are refreshed server-side before expiry with no visible interruption to the user
  5. `GET /bff/auth/logout` destroys the session, clears the cookie, and redirects to the Keycloak end-session endpoint
**Plans**: TBD

Plans:
- [ ] 34-01: OIDC client — openid-client v6 discovery, login redirect, callback exchange with state/nonce/PKCE validation
- [ ] 34-02: Session middleware + auth routes — requireSession guard, /me endpoint, token refresh middleware, logout

### Phase 35: FastAPI Proxy + CORS Consolidation
**Goal**: All FastAPI routes are accessible at `/bff/api/*` with Bearer tokens injected from the session; CORS is handled exclusively by the BFF and FastAPI no longer adds CORS headers.
**Depends on**: Phase 34
**Requirements**: PROXY-01, PROXY-03, BE-01
**Success Criteria** (what must be TRUE):
  1. An authenticated browser request to `/bff/api/any-route` reaches the FastAPI backend with a valid `Authorization: Bearer` header injected from the session
  2. FastAPI responses do not contain `Access-Control-*` headers; the BFF is the sole source of those headers
  3. FastAPI `CORSMiddleware` targeting the SPA origin is removed from `backend/app/main.py`
  4. Unauthenticated requests to `/bff/api/*` return 401 before reaching the backend
**Plans**: TBD

Plans:
- [ ] 35-01: FastAPI proxy — http-proxy-middleware setup, Bearer injection in onProxyReq, CORS header stripping in onProxyRes, path rewrite /bff/api → /api
- [ ] 35-02: Backend CORS cleanup — remove CORSMiddleware from main.py, verify no duplicate headers in browser DevTools

### Phase 36: CubeJS Proxy + Network Isolation
**Goal**: All CubeJS queries are proxied through the BFF at `/bff/cubejs/*` with a freshly signed server-side JWT per request containing user context; the backend service is unreachable from outside the internal Docker network.
**Depends on**: Phase 35
**Requirements**: PROXY-02, BE-02
**Success Criteria** (what must be TRUE):
  1. A CubeJS query sent to `/bff/cubejs/v1/load` reaches the CubeJS service with a valid HS256 JWT signed by the BFF containing `sub` and `roles` from the Keycloak session
  2. The CubeJS JWT is never present in browser network traffic — only the session cookie travels to the BFF
  3. The `backend` service has no Traefik-exposed port and is only reachable from the `bff` service within the internal Docker network
**Plans**: TBD

Plans:
- [ ] 36-01: CubeJS proxy — cubeToken.js HS256 signer, http-proxy-middleware to cubejs service, per-request JWT signing with user context
- [ ] 36-02: Backend network isolation — update docker-compose.yaml to remove public port exposure for backend; verify backend is unreachable from host

### Phase 37: Frontend Migration
**Goal**: The Vue 3 SPA operates without keycloak-js; auth state is driven by `/bff/auth/me`; all API and CubeJS calls route through BFF; no token ever appears in browser storage or network traffic to backend services.
**Depends on**: Phase 36
**Requirements**: FE-01, FE-02, FE-03, FE-04
**Success Criteria** (what must be TRUE):
  1. `keycloak.js` service file is deleted and no import of `keycloak-js` exists anywhere in `dashboard-app/src/`
  2. All API calls in `api.js` use the BFF base URL with `credentials: 'include'` and the app works end-to-end for an authenticated user
  3. The CubeJS store no longer manages tokens; charts load correctly with queries routed through `/bff/cubejs/*`
  4. Router guards wait for `authStore.initialized` before evaluating auth state; no flash redirect occurs for already-authenticated users on page refresh
**Plans**: TBD

Plans:
- [ ] 37-01: Remove keycloak-js — delete keycloak.js, update main.js, update auth store to use /bff/auth/me, add initialized flag + router guard fix
- [ ] 37-02: API + CubeJS migration — update api.js base URL and credentials mode, update cubejs store to remove token management

---

*For detailed milestone history, see .planning/milestones/*
*Last updated: 2026-05-28*
