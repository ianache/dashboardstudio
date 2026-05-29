# Project Research Summary

**Project:** Dashboard Studio - v1.8 BFF Service Architecture
**Domain:** Backend for Frontend (BFF) - Keycloak OIDC / Express Proxy / SPA Auth Migration
**Researched:** 2026-05-28
**Confidence:** HIGH

## Executive Summary

Dashboard Studio v1.8 introduces a Node.js + Express BFF (Backend for Frontend) service that moves all Keycloak OIDC auth from the browser to the server. The current architecture stores access tokens and refresh tokens in `sessionStorage` via `keycloak-js`, which exposes them to XSS. The BFF eliminates this by completing the OIDC Authorization Code + PKCE flow server-side, storing tokens only in an `express-session` backed by PostgreSQL, and issuing an HttpOnly session cookie to the browser. The browser never sees a token again.

The recommended approach is a five-phase build: first establish the BFF service with Keycloak auth (no frontend changes), confirm cookie transport, add the FastAPI proxy, add the CubeJS proxy with server-side JWT signing, and finally migrate the Vue 3 frontend to remove `keycloak-js` entirely. This incremental order allows each phase to be validated independently before the next is built. The BFF becomes the single entry point for the SPA: all API calls route through `/bff/api/*` and `/bff/cubejs/*`, while Traefik continues to serve the frontend and routes `/bff/*` to the new BFF service.

The primary risk is the cluster of session-state pitfalls unique to the OIDC redirect flow: the session must be explicitly saved before every Keycloak redirect, or PKCE code verifiers and state parameters are lost. The secondary risk is the cookie/CORS triple-constraint (frontend `credentials: include`, BFF CORS `credentials: true`, cookie `SameSite=None; Secure`) -- all three must be correct simultaneously or every API call fails silently. Both risks are well-understood and preventable with the patterns documented in PITFALLS.md.

---

## Key Findings

### Recommended Stack

The BFF is a thin Node.js + Express 5 service. Express 5 (stable Oct 2024) is chosen over Fastify because native async error handling eliminates `try/catch` boilerplate in OIDC callback routes, and `http-proxy-middleware` v4 explicitly targets Express 5. The critical library decision is `openid-client` v6 over `keycloak-connect`: the OpenID Foundation library handles state, nonce, PKCE, token validation, and refresh automatically, while `keycloak-connect` is in maintenance mode and was not designed for the BFF-proxies-tokens pattern. Sessions are stored in PostgreSQL via `connect-pg-simple` v10, reusing the existing database -- no Redis required for the expected single-tenant dashboard load.

**Core technologies:**
- `express@^5.2.1` -- HTTP server; native async error handling; current stable release
- `openid-client@^6.8.4` -- Keycloak OIDC client; only fully RFC-compliant option; v6 is a complete API rewrite from v5 (do not follow v5 tutorials)
- `express-session@^1.19.0` -- server-side session management; pairs with connect-pg-simple to persist across BFF restarts
- `http-proxy-middleware@^4.0.0` -- reverse proxy to FastAPI and CubeJS; streaming, header injection, path rewriting; Express 5 compatible
- `connect-pg-simple@^10.0.0` -- PostgreSQL session store; reuses existing database; requires a session table (SQL provided by the package)
- `helmet@^8.x` -- security headers; one line covers CSP, HSTS, X-Frame-Options
- `express-rate-limit@^7.x` -- auth endpoint protection; apply to /auth/* only

**Version constraint:** `openid-client` v6 requires Node.js 20+. The BFF must not run on Node 18.

### Expected Features

The BFF delivers six user-facing flows, all P1 for v1.8. The frontend migration (removing `keycloak-js`) is a P1 dependency -- the BFF is unusable until the Vue app stops calling FastAPI directly.

**Must have -- v1.8 launch (P1):**
- OIDC Authorization Code + PKCE login flow (`/bff/auth/login` + `/bff/auth/callback`)
- HttpOnly session cookie with PostgreSQL-backed session store
- `/bff/auth/me` -- returns `{ sub, email, name, roles }` from session; frontend uses this instead of `keycloak.tokenParsed`
- Transparent token refresh middleware -- checks `expires_at` before every proxied request; refreshes silently if within 60s of expiry
- FastAPI proxy (`/bff/api/*` to `http://backend:8000/api/*`) with `Authorization: Bearer` injected from session
- CubeJS proxy (`/bff/cubejs/*` to `http://cubejs:4000/cubejs-api/*`) with per-request HS256 JWT signed by BFF
- Logout (`/bff/auth/logout`) -- destroys session, clears cookie, redirects to Keycloak end-session with `id_token_hint`
- CSRF protection on all `/auth/*` endpoints
- Frontend migration: remove `keycloak-js`, replace with `credentials: include` fetch to BFF

**Should have -- add after v1.8 validated (P2):**
- `/bff/auth/status` endpoint for proactive session-expiry UI
- `/bff/auth/refresh` explicit endpoint for background-tab refresh
- Production PostgreSQL session store (start with in-memory for dev)

**Defer to v2+:**
- Keycloak backchannel logout -- requires session store lookup by Keycloak `sid` claim
- Per-user CubeJS JWT with row-level security (`queryRewrite`)
- WebSocket proxy for CubeJS real-time subscriptions

**Anti-features to reject:**
- Exposing raw tokens to the frontend -- defeats BFF purpose entirely
- Adding business logic to BFF -- must remain a dumb proxy + auth layer
- Removing JWT validation from FastAPI -- defense in depth requires both layers to validate

### Architecture Approach

The BFF sits between the Vue 3 SPA and all backend services. It is a new Docker Compose service (`bff`) added to the `backends` + `frontends` networks, reachable via Traefik at `dashboard.pm.comsatel.com.pe/bff/*`. The existing `frontend-app` (Nginx) and `backend` (FastAPI) services are unchanged in their core logic; only CORS origins and the SPA base URLs change.

**Major components:**
1. BFF Express app (`bff/src/index.js`) -- entry point, assembles middleware and routes
2. Session middleware (`bff/src/middleware/session.js`) -- `express-session` + `connect-pg-simple`; HttpOnly, Secure, SameSite cookie
3. Auth guard + token refresh (`bff/src/middleware/requireSession.js`) -- 401 if no session; silent Keycloak refresh if token within 60s of expiry
4. OIDC client wrapper (`bff/src/lib/oidcClient.js`) -- `openid-client` v6 `discovery()` + singleton; handles login redirect, callback exchange, logout redirect
5. Auth routes (`bff/src/routes/auth.js`) -- /login, /callback, /logout, /me
6. FastAPI proxy (`bff/src/routes/api.js`) -- `http-proxy-middleware`; injects Bearer from session; strips Cookie header
7. CubeJS proxy (`bff/src/routes/cubejs.js`) -- `http-proxy-middleware`; signs fresh HS256 JWT per-request via `cubeToken.js`

**Files modified in existing services:**
- `dashboard-app/src/main.js` -- remove 60+ lines of keycloak-js init; replace with fetch("/bff/auth/me")
- `dashboard-app/src/services/api.js` -- change base URL to `/bff/api`; remove `getAuthHeaders()`; add `credentials: include`
- `dashboard-app/src/stores/auth.js` -- replace `initFromKeycloak()` with `initFromBff(userInfo)`
- `dashboard-app/src/stores/cubejs.js` -- remove token; set `apiUrl` to `/bff/cubejs/v1`
- `backend/app/main.py` -- update CORS origins to include BFF port; restrict to internal in prod
- `docker-compose.yaml` -- add bff service with Traefik labels and network membership
- DELETE: `dashboard-app/src/services/keycloak.js`

### Critical Pitfalls

1. **Session not saved before Keycloak redirect** -- `express-session` saves lazily; `state`, `nonce`, and `code_verifier` must be written then `req.session.save()` called explicitly before `res.redirect(authorizationUrl)`. Without this, the callback handler reads an empty session and every login fails with HTTP 400. Affects every login attempt.

2. **Cookie not sent by SPA -- the triple constraint** -- All three must be correct simultaneously: (a) `credentials: include` on every `fetch` in `api.js`, (b) BFF CORS `origin: exact-string` plus `credentials: true`, (c) session cookie `SameSite=None; Secure` when SPA and BFF are on different subdomains. One wrong setting causes silent authentication failure on every API call.

3. **CORS double-header from FastAPI proxy** -- FastAPI `CORSMiddleware` adds `Access-Control-Allow-Origin`; the BFF CORS middleware adds another. Browsers reject duplicate CORS headers. Fix: in `http-proxy-middleware` `onProxyRes` hook, delete all four `access-control-*` headers from the FastAPI response before the BFF adds its own.

4. **CubeJS token without user context** -- A generic CubeJS JWT (no `sub`, `roles` claims) means all users see all data; CubeJS `queryRewrite` depends on `securityContext`. Always embed `sub` and `roles` from the Keycloak session when signing the CubeJS JWT. Must be correct from day one.

5. **Vue Router guard race condition on frontend migration** -- Current `main.js` initializes Keycloak synchronously before mounting; router guard safely reads `authStore.isAuthenticated`. After migration, `/bff/auth/me` is async; the guard fires before it resolves, causing a flash redirect for authenticated users. Fix: add `authStore.initialized` boolean; `await authStore.init()` in `beforeEach`; show a loading state while `initialized` is false.

---

## Implications for Roadmap

Based on the dependency graph from FEATURES.md and the build order from ARCHITECTURE.md, five phases are recommended, sequenced so each is independently testable before the next begins.

### Phase 1: BFF Foundation -- OIDC Auth + Session

**Rationale:** Everything depends on a working session. Login, token storage, and /auth/me are prerequisites for all proxy work. This phase has the highest density of security-critical code and the most non-obvious pitfalls. It must be solid before any proxy is built. The entire phase is testable without touching the frontend.

**Delivers:** A deployable BFF service that completes the Keycloak login flow end-to-end, sets an HttpOnly session cookie, and serves /bff/auth/me -- verifiable with a browser hitting the BFF directly.

**Features addressed:** OIDC Authorization Code + PKCE login, HttpOnly session cookie, server-side session store, /auth/me, logout with Keycloak end-session redirect, CSRF protection via state parameter validation.

**Stack:** `express@5`, `openid-client@6`, `express-session`, `connect-pg-simple`, `helmet`, `express-rate-limit`, Docker Compose bff service block.

**Pitfalls to prevent:** Session not saved before redirect, CSRF state validation, nonce validation, PKCE verifier loss, refresh token rotation.

### Phase 2: Session Cookie Configuration

**Rationale:** Must be confirmed working as a discrete step before building proxies. Cookie/CORS configuration depends on the deployment topology (same domain vs. separate subdomains).

**Delivers:** Session cookie correctly sent on all fetch calls from the SPA dev server to the BFF. Browser DevTools confirms cookie presence in API request headers.

**Features addressed:** HttpOnly + Secure + SameSite cookie flags, CORS `credentials: true`, `credentials: include` pattern.

**Pitfalls to prevent:** The triple constraint (Pitfall 4 in PITFALLS.md). This is a Phase 3 gate: if the cookie does not travel, the proxy is untestable from the browser.

### Phase 3: FastAPI Proxy

**Rationale:** FastAPI proxy is the core business-functionality path. Once the session cookie is confirmed working, the proxy is technically straightforward but requires careful header management.

**Delivers:** All 15 FastAPI route groups accessible via `/bff/api/*`. Bearer token injected from session on every proxied request. FastAPI unchanged except for CORS origins.

**Stack:** `http-proxy-middleware@4`, `pathRewrite`, `onProxyReq` hook for Bearer injection, `onProxyRes` hook for CORS header stripping.

**Pitfalls to prevent:** Authorization header not forwarded (Pitfall 6), CORS double-header from FastAPI (Pitfall 5), session cookie leaked to FastAPI.

### Phase 4: CubeJS Proxy

**Rationale:** Architecturally similar to Phase 3 but with an additional concern: the BFF must sign a fresh CubeJS JWT per-request. Separate phase because CubeJS token management has its own pitfall cluster.

**Delivers:** All CubeJS queries routed via `/bff/cubejs/*`. Browser never sends a token to CubeJS. CubeJS JWT contains `sub` and `roles` from the authenticated Keycloak session.

**Stack:** `jsonwebtoken` for HS256 signing, `CUBEJS_API_SECRET` env var, `signCubeToken()` in `bff/src/lib/cubeToken.js`.

**Pitfalls to prevent:** CubeJS token expiry not synchronized with session (sign fresh per-request, not at login time), CubeJS missing user context (embed `sub` and `roles`).

### Phase 5: Frontend Migration -- Remove keycloak-js

**Rationale:** The frontend migration is last because it is a one-way door -- once `keycloak-js` is removed and `api.js` points to the BFF, there is no fallback. All BFF phases must be confirmed end-to-end before this phase begins.

**Delivers:** The Vue 3 SPA fully operating without `keycloak-js`. Auth state driven by `/bff/auth/me`. API and CubeJS calls routed through BFF. `keycloak.js` service file deleted.

**Files changed:** `main.js`, `services/api.js`, `stores/auth.js`, `stores/cubejs.js`, delete `services/keycloak.js`.

**Pitfalls to prevent:** Vue Router guard race condition (add `authStore.initialized` flag and `await authStore.init()` in `beforeEach`). Dual-auth period must be zero -- remove `keycloak-js` atomically.

### Phase Ordering Rationale

- Session must exist before any proxy can work (Phase 1 first, always).
- Cookie transport must be confirmed before the proxy can be tested from a browser (Phase 2 gates Phase 3).
- FastAPI proxy carries business functionality and is simpler than CubeJS (Phase 3 before Phase 4).
- CubeJS proxy requires a working auth session to test and has additional token-signing concerns (Phase 4 after Phase 3).
- Frontend migration is a one-way door and must come last (Phase 5 always last).
- Each phase produces an independently testable artifact before the next starts.

### Research Flags

Phases needing deeper research or careful attention during implementation planning:

- **Phase 1:** `openid-client` v6 API is a complete rewrite from v5; the `discovery()` function and the `authorizationCodeGrant()` patterns differ from all tutorials prior to 2024. Confirm the exact v6 call sequence against the package README before writing auth routes. Do not copy v5 examples.
- **Phase 2:** The SameSite cookie strategy depends on whether Traefik serves the SPA and BFF from the same domain (`SameSite=Lax`) or different subdomains (`SameSite=None; Secure`). Confirm topology from Traefik labels in `docker-compose.yaml` before implementing.
- **Phase 4:** Whether the running CubeJS instance already enforces row-level security via `queryRewrite` is unknown without inspecting the CubeJS schema directory. If it does not, Phase 4 scope must include adding `queryRewrite`.

Phases with standard patterns (skip additional research):

- **Phase 3:** FastAPI proxy via `http-proxy-middleware` with `onProxyReq` header injection is a canonical, well-documented pattern. No additional research needed.
- **Phase 5:** Vue store and router changes are mechanical; file-by-file modifications are fully specified in ARCHITECTURE.md.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified via npm registry on 2026-05-28. Express 5 + HPM v4 compatibility confirmed. openid-client v6 API confirmed against GitHub release notes. |
| Features | HIGH | Based on direct codebase analysis of keycloak.js, api.js, auth.js, cubejs.js, security.py, router.py. The 15 FastAPI route groups enumerated directly from router.py. |
| Architecture | HIGH | Direct inspection of docker-compose.yaml, Traefik labels, network topology, and all files listed under modified components. BFF file structure follows established Express BFF conventions. |
| Pitfalls | HIGH | Sourced from OWASP cheat sheets, RFC 7636 (PKCE), OpenID Connect Core spec, express-session documentation, and direct analysis of existing main.js keycloak init patterns. All 11 pitfalls mapped to specific phases. |

**Overall confidence:** HIGH

### Gaps to Address

- **`openid-client` v6 exact callback pattern:** One code snippet in ARCHITECTURE.md uses the v5 `Issuer.discover()` API; the surrounding prose correctly describes v6 semantics. During Phase 1, verify the complete v6 call sequence against the actual package README before writing route handlers.

- **Keycloak client registration (operational prerequisite):** A new confidential client `dashboard-bff` must be registered in the Keycloak admin console at `oauth2.qa.comsatel.com.pe` with the correct callback URI and PKCE settings. This cannot be automated in code. Confirm access to the Keycloak admin console before starting Phase 1.

- **CubeJS `queryRewrite` current state:** Whether the running CubeJS deployment enforces row-level security is unknown without inspecting the CubeJS schema files. If it does not, Phase 4 scope expands to include adding `queryRewrite`.

- **Session cookie domain topology:** The exact Traefik routing configuration determines whether `SameSite=Lax` (same origin) or `SameSite=None; Secure` (cross-origin) is required. Confirmable from the current Traefik labels in `docker-compose.yaml`.

---

## Sources

### Primary (HIGH confidence)

- Codebase: `dashboard-app/src/main.js`, `services/keycloak.js`, `services/api.js`, `stores/auth.js`, `stores/cubejs.js` -- direct inspection
- Codebase: `backend/app/core/security.py`, `app/main.py`, `app/api/router.py` -- direct inspection
- Codebase: `docker-compose.yaml`, `environment/keycloak/realm-export.json` -- direct inspection
- npm registry: `express@5.2.1`, `openid-client@6.8.4`, `express-session@1.19.0`, `http-proxy-middleware@4.0.0`, `connect-pg-simple@10.0.0` -- verified 2026-05-28
- OIDC Core 1.0 specification, RFC 7636 (PKCE), RFC 6749 -- state/nonce/PKCE requirements
- OWASP Session Management Cheat Sheet, OWASP CSRF Prevention Cheat Sheet
- MDN Web Docs: Fetch `credentials`, SameSite cookie attribute
- `express-session` npm documentation: `save()`, `saveUninitialized`, `resave` behavior

### Secondary (MEDIUM confidence)

- Express 5 release announcement (https://expressjs.com/2024/10/15/v5-release.html) -- async error handling
- `openid-client` v6 migration guide (https://github.com/panva/openid-client/releases) -- API changes from v5
- `http-proxy-middleware` v4 changelog (https://github.com/chimurai/http-proxy-middleware) -- Express 5 compatibility
- CubeJS JWT auth documentation (https://cube.dev/docs/product/auth) -- `securityContext`, `queryRewrite`

### Tertiary (LOW confidence / needs validation)

- `keycloak-connect` maintenance status -- inferred from npm activity and Keycloak community signals; verify against official Keycloak GitHub during Phase 1 planning
- CubeJS `queryRewrite` current state in the running deployment -- unknown without inspecting CubeJS schema files

---

*Research completed: 2026-05-28*
*Ready for roadmap: yes*