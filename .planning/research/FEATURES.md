# Feature Research: BFF Service Architecture

**Domain:** Backend for Frontend (BFF) — SPA Authentication & API Gateway
**Researched:** 2026-05-28
**Confidence:** HIGH (based on codebase analysis of existing auth/API surface + established OIDC/BFF patterns)

---

## Context: What Already Exists

Before cataloguing BFF features, understanding what is being replaced matters.

**Current client-side auth (dashboard-app):**
- `keycloak-js` adapter in `main.js` runs PKCE authorization code flow entirely in the browser
- Access token, refresh token, and ID token stored in `sessionStorage` (`kc_token`, `kc_refresh`, `kc_id`)
- `api.js` reads `keycloak.token` on every request and injects `Authorization: Bearer <token>` header
- Token refresh is client-managed: `keycloak.onTokenExpired` fires 60s before expiry, calls `keycloak.updateToken(60)`
- `cubejs.js` store holds the CubeJS token and calls CubeJS API directly from the browser

**Current backend (FastAPI):**
- Validates `Authorization: Bearer` on every request via `security.py` (`verify_token`)
- Fetches JWKS from Keycloak, caches 1h, verifies RS256 signature
- Extracts `sub`, `email`, `name`, `realm_access.roles` from payload
- Auto-creates user record on first authenticated request (`ensure_user_exists`)

**API surface to proxy:** 15 endpoint groups in `router.py` — users, dashboards, widgets, palettes, data_types, dimensional_models, cube_config, llm_config, currencies, data_sources, knowledge_spaces, diagram_types, editor_tools, integration_flows, execution_history.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the BFF must deliver. Missing any = the BFF is not a BFF, the migration is incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| OIDC Authorization Code + PKCE initiation | Browser cannot hold a client secret; BFF initiates the redirect with `response_type=code` and PKCE challenge | MEDIUM | BFF generates `state` and `code_verifier`, stores in server session before redirect |
| Callback endpoint (`/auth/callback`) | Keycloak redirects here with `code`; BFF exchanges for tokens server-side | MEDIUM | POST to Keycloak `/token` endpoint with `code` + `code_verifier`; store tokens in session, set HttpOnly cookie |
| HttpOnly session cookie | Users should never have tokens in JS memory or `sessionStorage` | LOW | `express-session` + `connect-pg-simple` or in-memory (dev); `SameSite=Lax`, `Secure`, `HttpOnly` flags required |
| Session-backed token storage | Access token, refresh token, ID token stored server-side in session store, never sent to browser | LOW | Session record holds `{ access_token, refresh_token, id_token, expires_at }` |
| Transparent token refresh | When BFF proxies a request and the access token is expired (or near-expiry), BFF refreshes silently before forwarding | MEDIUM | Compare `expires_at` against `Date.now()`; call Keycloak `/token` with `grant_type=refresh_token`; update session; no user interaction |
| FastAPI proxy (`/api/*`) | Frontend currently calls FastAPI directly with Bearer; after BFF, frontend calls BFF which forwards with `Authorization: Bearer <stored_token>` | LOW-MEDIUM | `http-proxy-middleware` or `express-http-proxy`; strip cookie, inject Bearer from session |
| CubeJS proxy (`/cubejs/*`) | CubeJS JWT is currently held in `cubejs.js` store; BFF must hold and inject it | MEDIUM | BFF fetches or generates CubeJS token server-side; frontend sends no token to CubeJS; BFF proxies all `/cubejs-api/v1/*` requests |
| `/auth/me` endpoint | Frontend needs to know who is logged in (user profile, roles) after page load — cannot read HttpOnly cookie | LOW | BFF reads session, returns `{ sub, email, name, roles }` from stored ID token claims; no token exposed |
| Local logout (`/auth/logout`) | Destroy server-side session and clear the session cookie | LOW | `req.session.destroy()` + `res.clearCookie()`; redirect to Keycloak logout URL |
| Keycloak logout redirect | After local session is destroyed, redirect browser to Keycloak's `/protocol/openid-connect/logout` with `id_token_hint` and `post_logout_redirect_uri` | LOW | Required for full SSO logout; uses stored `id_token` from session before destroying it |
| Unauthenticated redirect | Any request to a protected route without a valid session returns 401 (for API calls) or redirects to login (for browser navigation) | LOW | Middleware: if no session, `res.status(401).json({ error: 'unauthenticated' })`; frontend handles redirect |
| CSRF protection | Session cookies are vulnerable to CSRF; all state-mutating BFF routes need protection | MEDIUM | `csurf` or `double-submit cookie` pattern; applies to `/auth/*` endpoints and any BFF-owned state |

---

### Differentiators (Competitive Advantage for This BFF)

Features that improve security posture or operational experience beyond the bare minimum.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| CubeJS token generation server-side | CubeJS JWT signed with shared secret never leaves the server; eliminates the current pattern of storing `VITE_CUBEJS_TOKEN` in frontend env | HIGH | BFF needs the CubeJS secret; generates JWT per-session or shared; injects on proxy |
| Session expiry aligned with Keycloak token TTL | Server-side session max-age mirrors Keycloak access + refresh token lifetime; no stale sessions holding expired tokens | MEDIUM | Read `expires_in` from Keycloak token response; set `session.cookie.maxAge` accordingly |
| `/auth/status` polling endpoint | Frontend can poll BFF to detect session expiry without reading tokens; enables proactive logout UI | LOW | Returns `{ authenticated: boolean, expiresAt: ISO string }` from session metadata |
| Token refresh on-demand (`/auth/refresh`) | Frontend can explicitly trigger refresh (e.g., after returning from background); BFF refreshes and updates session | LOW | Calls Keycloak `/token` with `grant_type=refresh_token`; no response body needed beyond 200/401 |
| Keycloak backchannel logout (OIDC Back-Channel) | Keycloak can notify the BFF server directly when a session is invalidated (e.g., admin logout, password change) | HIGH | Requires registering BFF backchannel logout URL in Keycloak client config; BFF destroys matching sessions from store |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Exposing raw tokens to frontend | Seems simpler — just forward the token from session to the browser | Defeats the entire purpose of the BFF pattern; tokens in JS memory are accessible via XSS | Keep tokens server-side; expose only user metadata via `/auth/me` |
| BFF managing business logic | Tempting to add filtering, aggregation, or transformation in the BFF while proxying | BFF becomes a second FastAPI; adds coupling, doubles maintenance surface | BFF is a dumb proxy + auth layer only; all business logic stays in FastAPI |
| Replacing express-session with JWT-signed cookies | Stateless approach avoids session store complexity | Logout cannot revoke a JWT cookie; stolen cookie is valid until expiry; no backchannel logout possible | Use server-side session store (even in-memory for dev); `connect-pg-simple` for production |
| Silent SSO iframe checks | keycloak-js uses an iframe to check session status without redirect; current code already disables this (`checkLoginIframe: false`) due to Keycloak's `frame-ancestors 'self'` CSP | iframes blocked by CSP at `oauth2.qa.comsatel.com.pe`; cannot use; causes silent failures | Use `/auth/status` polling or session cookie presence as the session check mechanism |
| WebSocket proxying via BFF | CubeJS real-time subscriptions use WebSocket; proxying WS through BFF is non-trivial | Adds significant complexity; CubeJS WebSocket auth is separate from REST auth | For v1, proxy only HTTP; defer WebSocket to v2 or keep direct CubeJS WS connection (acceptable risk if CubeJS is not internet-exposed) |
| Per-request token validation in BFF | BFF re-validates token signature on every proxied request | Adds latency; creates second JWKS dependency in BFF; FastAPI already validates; double validation is redundant | BFF trusts its own session (it set the token); FastAPI validates signature as-is; BFF just injects the stored token |
| Storing tokens in Redis with complex eviction | Seems production-grade | Overkill for a single-tenant internal dashboard; adds infrastructure dependency | `connect-pg-simple` uses the existing PostgreSQL database; one less service to operate |

---

## Feature Breakdown by Auth Flow

### Flow 1: Login (User-Visible vs Server-Side)

**User sees:**
1. App loads, no session cookie → frontend detects 401 from `/auth/me` → redirects browser to `/auth/login`
2. Browser redirects to Keycloak login page
3. User enters credentials on Keycloak UI
4. Browser redirects back to the app

**Server-side mechanics (BFF):**

`GET /auth/login`:
- BFF generates `state` (random nonce), `code_verifier` (random), `code_challenge = BASE64URL(SHA256(code_verifier))`
- Stores `{ state, code_verifier }` in `req.session` (before redirect, so session exists)
- Redirects browser to: `https://keycloak/realms/{realm}/protocol/openid-connect/auth?response_type=code&client_id=bff&redirect_uri=https://bff/auth/callback&scope=openid+profile+email&state={state}&code_challenge={challenge}&code_challenge_method=S256`

`GET /auth/callback?code={code}&state={state}`:
- Validates `state` matches session (CSRF protection)
- POSTs to Keycloak `/token`: `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret` (if confidential client), `code_verifier`
- Keycloak responds with `{ access_token, refresh_token, id_token, expires_in, refresh_expires_in }`
- BFF stores all tokens in session: `req.session.tokens = { access_token, refresh_token, id_token, expires_at: Date.now() + expires_in * 1000 }`
- BFF sets session cookie (HttpOnly, Secure, SameSite=Lax)
- Redirects browser to `/` (or stored pre-login URL)

**Complexity:** MEDIUM
**Dependencies:** Keycloak client configured with BFF callback URI; PKCE support in Keycloak (enabled by default in Keycloak 18+)

---

### Flow 2: Session Check (Page Load)

**User sees:** App loads seamlessly if session valid; redirect to login if not.

**Server-side mechanics:**

`GET /auth/me`:
- BFF checks `req.session.tokens`
- If no session or session expired: `401 Unauthenticated`
- If session valid: extract claims from stored `id_token` (parse JWT, no verification needed — BFF issued it); return `{ sub, email, name, roles }`
- Frontend uses this to populate `useAuthStore`; no `keycloak-js` adapter needed

**Complexity:** LOW

---

### Flow 3: Transparent Token Refresh (On Proxy Request)

**User sees:** Nothing — API calls continue working even as the access token expires.

**Server-side mechanics (BFF middleware):**

Before forwarding any proxied request:
1. Check `req.session.tokens.expires_at` — if `expires_at - Date.now() < 60_000` (< 60s remaining):
2. POST to Keycloak `/token`: `grant_type=refresh_token`, `refresh_token`, `client_id`, `client_secret`
3. If refresh succeeds: update `req.session.tokens` with new tokens + new `expires_at`; save session; proceed with proxy using new `access_token`
4. If refresh fails (refresh token expired): destroy session; return `401` to frontend; frontend redirects to login

**Complexity:** MEDIUM
**Critical:** Concurrent requests during refresh window can cause multiple simultaneous refresh calls. Mitigation: in-flight refresh deduplication per session ID (a simple promise map keyed by session ID is sufficient).

---

### Flow 4: API Proxy (FastAPI Routes)

**User sees:** All API calls work as before; no auth headers to manage in frontend.

**Server-side mechanics:**

`ALL /api/*` → forward to `http://backend:8000/api/*`
- Strip `Cookie` header (never forward session cookie to backend)
- Inject `Authorization: Bearer {req.session.tokens.access_token}`
- Forward all other headers (Content-Type, etc.)
- Forward request body unchanged
- Stream response back to client
- On `401` from backend: attempt one token refresh, retry once, then propagate `401`

**Complexity:** LOW-MEDIUM
**Library:** `http-proxy-middleware` v3 (Express-compatible, supports `on.proxyReq` hook for header injection)

---

### Flow 5: CubeJS Proxy

**User sees:** CubeJS charts load as before; frontend no longer needs `VITE_CUBEJS_TOKEN`.

**Server-side mechanics:**

Option A (recommended for v1.8): BFF reads CubeJS JWT from `cube_config` table via FastAPI API, caches it in memory (it changes infrequently).
Option B: BFF generates the CubeJS JWT itself using the shared secret (requires BFF to know `CUBEJS_API_SECRET`).

`ALL /cubejs-api/*` → forward to `http://cubejs:4000/cubejs-api/*`
- Inject `Authorization: Bearer {cubejs_token}`
- No user-specific CubeJS token needed for v1 (single-tenant, shared token)

**Complexity:** MEDIUM (Option A) / HIGH (Option B — requires secret management)
**Recommendation:** Option A for v1; BFF calls `GET /api/v1/cube-config/active` on startup to get the CubeJS token; refreshes on cache miss or backend-signaled change.

---

### Flow 6: Logout

**User sees:** Clicks "Logout" → session ends → redirected to Keycloak login page.

**Server-side mechanics:**

`POST /auth/logout`:
1. Extract `id_token` from `req.session.tokens` (needed for `id_token_hint`)
2. Call `req.session.destroy()` to invalidate server-side session
3. Call `res.clearCookie(SESSION_COOKIE_NAME)`
4. Redirect browser to: `https://keycloak/realms/{realm}/protocol/openid-connect/logout?id_token_hint={id_token}&post_logout_redirect_uri=https://dashboard/auth/login`
5. Keycloak invalidates its SSO session; redirects user to `post_logout_redirect_uri`

**Complexity:** LOW
**Note:** Without `id_token_hint`, Keycloak (v18+) shows a "do you want to logout?" confirmation page. Always include it.

---

## Feature Dependencies

```
Keycloak OIDC Client (confidential or PKCE public)
    └──required for──> Login Flow (/auth/login + /auth/callback)
                           └──produces──> Session with tokens
                                              └──enables──> /auth/me (identity)
                                              └──enables──> API Proxy (/api/*)
                                              └──enables──> CubeJS Proxy (/cubejs-api/*)
                                              └──enables──> Token Refresh (transparent)
                                              └──enables──> Logout (/auth/logout)

Session Store (express-session + pg or memory)
    └──required for──> All session-dependent features above

CubeJS token source (either FastAPI /cube-config/active or shared secret)
    └──required for──> CubeJS Proxy

Frontend update (remove keycloak-js adapter, remove direct API calls)
    └──depends on──> All BFF flows being operational first
```

### Dependency Notes

- **Login flow requires session before redirect:** `req.session` must be initialized (session middleware must run before `/auth/login`) so `state` and `code_verifier` survive the redirect roundtrip.
- **Token refresh requires session store to be write-capable:** In-memory session store loses sessions on BFF restart; use `connect-pg-simple` in production.
- **Frontend removal of keycloak-js requires BFF to be fully operational:** The frontend migration (`remove keycloak-js`, `call BFF instead of FastAPI`) must happen after the BFF is deployed and tested.
- **FastAPI auth cleanup depends on BFF being the sole caller:** Only remove FastAPI JWT validation after confirming BFF injects Bearer on every request; premature removal breaks security.

---

## MVP Definition

### Launch With (v1.8 — this milestone)

- [ ] OIDC authorization code + PKCE login flow (`/auth/login` + `/auth/callback`) — without this the BFF has no auth
- [ ] HttpOnly session cookie with server-side session store — without this tokens leak to browser
- [ ] `/auth/me` endpoint — without this frontend cannot determine logged-in identity
- [ ] Transparent token refresh middleware — without this sessions expire mid-use
- [ ] FastAPI proxy (`/api/*`) with Bearer injection — without this no business functionality works
- [ ] CubeJS proxy (`/cubejs-api/*`) with server-side token — without this dashboards show no data
- [ ] Logout (`/auth/logout`) with Keycloak redirect — without this users cannot sign out
- [ ] CSRF protection on `/auth/*` endpoints — without this session fixation/CSRF attacks are possible
- [ ] Frontend update: replace `keycloak-js` calls with BFF calls, use `credentials: 'include'` — without this BFF is unused

### Add After Validation (v1.8.x)

- [ ] `/auth/status` endpoint — add when frontend needs proactive session expiry UI
- [ ] `/auth/refresh` explicit endpoint — add when background-tab refresh is needed
- [ ] `connect-pg-simple` session store — add when BFF restarts are causing session loss in production

### Future Consideration (v2+)

- [ ] Keycloak backchannel logout — requires Keycloak client configuration + session store that supports lookup by `sid` claim; complex, adds real-time logout propagation
- [ ] Per-user CubeJS JWT with row-level security claims — requires CubeJS RBAC model; significant CubeJS schema work
- [ ] WebSocket proxy for CubeJS real-time subscriptions — requires `http-proxy-middleware` WS mode + BFF auth for WS upgrade

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| OIDC login flow (redirect + callback) | HIGH | MEDIUM | P1 |
| HttpOnly cookie session | HIGH | LOW | P1 |
| `/auth/me` identity endpoint | HIGH | LOW | P1 |
| Transparent token refresh | HIGH | MEDIUM | P1 |
| FastAPI proxy with Bearer injection | HIGH | LOW | P1 |
| CubeJS proxy with server-side token | HIGH | MEDIUM | P1 |
| Logout + Keycloak redirect | HIGH | LOW | P1 |
| CSRF protection | HIGH (security) | MEDIUM | P1 |
| Frontend migration off keycloak-js | HIGH | MEDIUM | P1 |
| `/auth/status` polling | MEDIUM | LOW | P2 |
| `connect-pg-simple` session persistence | MEDIUM | LOW | P2 |
| Keycloak backchannel logout | LOW | HIGH | P3 |
| Per-user CubeJS JWT (RBAC) | MEDIUM | HIGH | P3 |
| WebSocket proxy | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (v1.8 milestone)
- P2: Should have, add after core validated
- P3: Future consideration (v2+)

---

## Existing Infrastructure Dependencies

| Component | Current State | BFF Dependency |
|-----------|--------------|----------------|
| Keycloak at `oauth2.qa.comsatel.com.pe` | Running, PKCE enabled, CSP `frame-ancestors 'self'` | BFF needs a new confidential client (or reuses `dashboard-app` as public PKCE client); callback URI must be registered |
| FastAPI backend at `dashboard-api.pm.comsatel.com.pe` | Running, validates JWT via JWKS | BFF proxies all traffic; FastAPI JWT validation stays in place (defense in depth) |
| CubeJS instance | Running, token in `cube_config` table | BFF fetches token via FastAPI on startup; or receives `CUBEJS_API_SECRET` env var |
| PostgreSQL (backend DB) | Running | `connect-pg-simple` can use same DB for session store (separate table) |
| Traefik reverse proxy | Running, routes `dashboard.pm.comsatel.com.pe` → frontend | Needs new route for BFF or BFF sits behind existing frontend domain as a new service |
| `express-session` | Not yet installed | Core BFF dependency; session cookie name and secret must be in BFF env |

---

## User-Visible vs Server-Side Behavior Summary

| User Experience | What BFF Does Server-Side |
|----------------|--------------------------|
| User clicks "Login" → sees Keycloak login page | `/auth/login` generates PKCE challenge, stores in session, redirects to Keycloak |
| User enters credentials on Keycloak → app loads | `/auth/callback` exchanges `code` for tokens, stores in session, sets HttpOnly cookie, redirects to `/` |
| App loads, user appears logged in | Frontend calls `/auth/me`, BFF reads session and returns user claims — no token in browser |
| User navigates, API calls succeed | BFF middleware reads session, injects Bearer, proxies to FastAPI; user sees normal app |
| User stays on app for hours without action | Keycloak refresh token keeps session alive; BFF refreshes silently 60s before access token expires |
| User clicks "Logout" | `/auth/logout` destroys session, clears cookie, redirects to Keycloak logout; Keycloak shows login page |
| Admin forces user logout in Keycloak (v2) | Keycloak calls BFF backchannel endpoint; BFF destroys session; next request from user gets 401 |

---

## Sources

| Source | Confidence | Notes |
|--------|------------|-------|
| Codebase analysis: `dashboard-app/src/services/keycloak.js`, `main.js`, `api.js`, `stores/auth.js`, `stores/cubejs.js` | HIGH | Direct inspection of current client-side auth implementation |
| Codebase analysis: `backend/app/core/security.py`, `api/router.py` | HIGH | Direct inspection of FastAPI JWT validation and API surface |
| Codebase analysis: `docker-compose.yaml` | HIGH | Infrastructure topology |
| OIDC Authorization Code + PKCE flow (RFC 7636, OpenID Connect Core 1.0) | HIGH | Well-established, stable specs; BFF pattern applies these directly |
| `express-session` + `http-proxy-middleware` established patterns | HIGH (training, pre-cutoff) | Both libraries stable, widely documented; verify current major versions |
| Keycloak OIDC logout spec (`id_token_hint` + `post_logout_redirect_uri`) | HIGH | Keycloak 18+ behavior; current deployment at `oauth2.qa.comsatel.com.pe` |

---

*Feature research for: BFF Service Architecture (Dashboard Studio v1.8)*
*Researched: 2026-05-28*
