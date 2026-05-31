# Project Roadmap: Dashboard Studio

## Milestones

- ✅ **v1.6 ODS Execution Engine** — Phases 29-31 (shipped 2026-05-17)
- ✅ **v1.7 Email Node** — Phase 32 (shipped 2026-05-17)
- ✅ **v1.8 BFF Service Architecture** — Phases 33-37 (shipped 2026-05-31)

## Progress Table

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-28. Core & Extensions | Pre-v1.6 | 28/28 | Complete | 2026-05-17 |
| 29. Metadata Inspection API | v1.6 | 2/2 | Complete | 2026-05-16 |
| 30. ODS Node UI Enhancement | v1.6 | 1/1 | Complete | 2026-05-16 |
| 31. ODS Execution Engine | v1.6 | 3/3 | Complete | 2026-05-17 |
| 32. Email Node Implementation | v1.7 | 3/3 | Complete | 2026-05-17 |
| 33. BFF Foundation | v1.8 | 3/3 | Complete | 2026-05-28 |
| 34. Keycloak Auth Flow | v1.8 | 3/3 | Complete | 2026-05-28 |
| 35. FastAPI Proxy + CORS | v1.8 | 2/2 | Complete | 2026-05-28 |
| 36. CubeJS Proxy + Network Isolation | v1.8 | 2/2 | Complete | 2026-05-28 |
| 37. Frontend Migration | v1.8 | 2/2 | Complete | 2026-05-29 |

---

## ✅ v1.6 ODS Execution Engine (Phases 29-31) — SHIPPED 2026-05-17

<details>
<summary>View v1.6 Details</summary>

### Phase 29: Metadata Inspection API
- [x] 29-01: Implement MetadataService with PostgreSQL support.
- [x] 29-02: Expose metadata inspection via FastAPI endpoints.

### Phase 30: ODS Node UI Enhancement
- [x] 30-01: Update ODS node UI with dynamic selectors, refresh buttons, and conditional identity fields.

### Phase 31: ODS Execution Engine
- [x] 31-01: Core ODSExecutor Service (ods_executor.py with Append, Overwrite, Upsert)
- [x] 31-02: Deno Integration & Signal Protocol (runner.ts, deno_service.py)
- [x] 31-03: Validation, Testing & Hardening (validation, logging, tests, deprecation)

**Archive:** `.planning/milestones/v1.6-ROADMAP.md`

</details>

---

## ✅ v1.7 Email Node with Dynamic Templates (Phase 32) — SHIPPED 2026-05-17

<details>
<summary>View v1.7 Details</summary>

### Phase 32: Email Node Implementation
- [x] 32-01: Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration)
- [x] 32-02: Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [x] 32-03: UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

**Archive:** `.planning/milestones/v1.7-ROADMAP.md`

</details>

---

## ✅ v1.8 BFF Service Architecture (Phases 33-37) — SHIPPED 2026-05-31

<details>
<summary>View v1.8 Details</summary>

### Phase 33: BFF Foundation
- [x] 33-01: BFF Express 5 scaffold — package.json, Dockerfile, config.js, health route
- [x] 33-02: Infrastructure config — docker-compose bff + redis service, .env-bff.example
- [x] 33-03: Session store — connect-redis wired to Redis, HttpOnly cookie

### Phase 34: Keycloak Auth Flow
- [x] 34-01: ESM Migration & OIDC Client Setup — openid-client v6, discovery
- [x] 34-02: Auth routes — login, callback, me, logout (PKCE OIDC)
- [x] 34-03: Token Management & Refresh — tokenRefresh middleware, concurrent refresh coordination

### Phase 35: FastAPI Proxy + CORS Consolidation
- [x] 35-01: FastAPI proxy — Bearer injection, CORS stripping, path rewrite /bff/api → /api
- [x] 35-02: Backend CORS cleanup — remove CORSMiddleware from main.py

### Phase 36: CubeJS Proxy + Network Isolation
- [x] 36-01: CubeJS proxy — cubeToken.js HS256 signer, per-request JWT signing
- [x] 36-02: Backend network isolation — remove Traefik labels and public ports from backend/cubejs

### Phase 37: Frontend Migration
- [x] 37-01: Remove keycloak-js — delete keycloak.js, update auth store to use /bff/auth/me
- [x] 37-02: Final cleanup — main.js BFF init, router guards, keycloak-js uninstalled

**Archive:** `.planning/milestones/v1.8-ROADMAP.md`

</details>

---

*For detailed milestone history, see .planning/milestones/*
*Last updated: 2026-05-31 after v1.8 milestone*
