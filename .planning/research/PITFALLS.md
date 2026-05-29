# Pitfalls Research: BFF Service Architecture

**Domain:** BFF (Backend for Frontend) — Keycloak OIDC / Express Session / Proxy layer
**Project:** Dashboard Studio — v1.8 BFF Service Architecture
**Researched:** 2026-05-28
**Confidence:** HIGH (based on direct codebase analysis + well-established patterns in OIDC/BFF literature)

---

## Critical Pitfalls

### Pitfall 1: CSRF via Missing State Parameter Validation in the OIDC Callback

**What goes wrong:**
The BFF generates the authorization URL with a `state` parameter to prevent CSRF, but never verifies that the `state` returned by Keycloak in the callback matches what was stored in the session. An attacker who can trick a user's browser into hitting `/auth/callback?code=...&state=attacker-controlled` can hijack the code exchange.

**Why it happens:**
Developers focus on getting the happy path working (redirect → callback → token exchange → session write) and add state validation "later." Libraries like `openid-client` validate state automatically, but if you call `issuer.grant()` or raw `axios.post(tokenUrl)` manually, nothing validates it for you.

**How to avoid:**
1. Before redirecting to Keycloak, generate a cryptographically random `state` value: `crypto.randomUUID()` or `crypto.randomBytes(32).toString('hex')`.
2. Store it in `req.session.oidcState` **before** the redirect and call `req.session.save()` — do not rely on the session being auto-saved before the response is sent.
3. In the callback handler, reject immediately (HTTP 400) if `req.query.state !== req.session.oidcState`.
4. Delete `req.session.oidcState` after a successful validation to prevent replay.

**Warning signs:**
- The callback route does not read `req.session.oidcState` at all.
- No `state` parameter included in the authorization redirect URL.
- Using `crypto.randomBytes` but not storing the result before redirect.

**Phase to address:** Phase 1 — Keycloak OIDC Authorization Code Flow

---

### Pitfall 2: Nonce Not Validated Against the ID Token Claim

**What goes wrong:**
The `nonce` parameter is included in the authorization request (good), but the BFF never checks that the `nonce` claim inside the received `id_token` matches the value stored in the session. An attacker who replays an old ID token (obtained via MITM or token leak) can bypass freshness guarantees.

**Why it happens:**
Nonce validation is not enforced by Keycloak itself — it is the client's responsibility. When using `openid-client`, nonce checking happens automatically if you pass the nonce to `callbackParams`. When rolling a manual token exchange, the nonce is ignored.

**How to avoid:**
1. Generate a separate nonce alongside the state: `crypto.randomBytes(32).toString('hex')`.
2. Store it in `req.session.oidcNonce` before the redirect.
3. After the token exchange, decode the `id_token` payload (without full verification — just `Buffer.from(parts[1], 'base64').toString()`) and assert `payload.nonce === req.session.oidcNonce`.
4. Reject if they differ.
5. Use `openid-client` (the `openid-client` npm package) rather than raw HTTP calls: it validates state, nonce, iss, aud, exp, iat automatically.

**Warning signs:**
- Token exchange is done via a raw `fetch` or `axios.post` to Keycloak's token endpoint rather than through `openid-client`.
- No `nonce` key is ever read from `req.session` in the callback handler.

**Phase to address:** Phase 1 — Keycloak OIDC Authorization Code Flow

---

### Pitfall 3: express-session Not Persisting Before the Keycloak Redirect

**What goes wrong:**
The OIDC state and nonce are written to `req.session` before calling `res.redirect(authorizationUrl)`. Because `express-session` saves sessions **after the response is sent** (lazy save), the state has not yet been written to the session store when Keycloak redirects the browser back to the callback. The callback reads an empty session and the state check fails, causing every login attempt to return HTTP 400.

**Why it happens:**
`express-session` by default uses `saveUninitialized: false` and saves at response-end. A redirect is a response, so the write happens — but only if the store's I/O is synchronous (memory store). With Redis or Postgres stores, the async write may not complete before the TCP FIN goes out. More critically, if the session was already existing and only partially modified, some stores with `resave: false` will not save at all.

**How to avoid:**
1. After writing state/nonce to the session, explicitly call `req.session.save(err => { if (err) next(err); else res.redirect(authorizationUrl); })`.
2. Set `saveUninitialized: true` only during the OAuth flow routes, or create a new session with `req.session.regenerate` before writing the OIDC values.
3. With Redis as session store, verify the `connect-redis` store's `disableTouch` option is not set to `true` for OIDC routes.

**Warning signs:**
- Login succeeds on the first browser tab but fails on subsequent attempts.
- `req.session.oidcState` is `undefined` in the callback handler.
- Tests pass with the default `MemoryStore` but break in production with Redis.

**Phase to address:** Phase 1 — Keycloak OIDC Authorization Code Flow

---

### Pitfall 4: Session Cookie Not Sent by the SPA Due to Wrong CORS or Cookie Configuration

**What goes wrong:**
The SPA (Vue 3 on `dashboard.pm.comsatel.com.pe`) makes API calls to the BFF, but the session cookie is never sent. All BFF endpoints see an unauthenticated session. This is the single most common failure mode when migrating from Bearer tokens to session cookies.

**Why it happens:**
Three independent settings must all be correct simultaneously:
1. **SPA side:** `fetch` (or axios) must include `credentials: 'include'` (or `withCredentials: true`).
2. **BFF CORS:** The Express CORS middleware must be configured with `origin: 'https://dashboard.pm.comsatel.com.pe'` (exact string, not `*`) and `credentials: true`.
3. **Cookie flags:** The session cookie must have `SameSite: 'None'` and `Secure: true` when the SPA and BFF are on different origins (even different subdomains). With `SameSite: 'Strict'` or `SameSite: 'Lax'`, cross-origin `fetch` calls will not send the cookie.

Currently, `api.js` uses plain `fetch` without `credentials: 'include'`. This must be changed globally.

**How to avoid:**
1. Set `cookie: { sameSite: 'none', secure: true, httpOnly: true }` in `express-session` options when BFF and SPA are on different subdomains.
2. Set `sameSite: 'lax'` only if BFF and SPA are served from the exact same domain and port (not applicable here — Traefik routes separate them).
3. Add to every `fetch` call in `api.js`: `credentials: 'include'`.
4. If using axios globally: `axios.defaults.withCredentials = true`.
5. CORS origin must be an exact string (no trailing slash). Wildcards (`*`) with `credentials: true` are rejected by browsers.
6. In development (http), use `secure: false` and `sameSite: 'lax'` or `'strict'` to avoid the HTTPS requirement, but document that production requires HTTPS.

**Warning signs:**
- Browser DevTools Network tab shows the cookie is set in the `/auth/callback` response, but is absent in subsequent API requests.
- CORS preflight response is missing `Access-Control-Allow-Credentials: true`.
- Session cookie has `SameSite=Strict` but the SPA and BFF are on different subdomains.

**Phase to address:** Phase 2 — express-session & Secure Cookie Setup

---

### Pitfall 5: CORS Double-Handling When the BFF Proxies to FastAPI

**What goes wrong:**
The existing FastAPI backend already has `CORSMiddleware` configured to allow the SPA origin. When the BFF proxies requests to FastAPI, FastAPI adds `Access-Control-Allow-Origin: https://dashboard.pm.comsatel.com.pe` to the response. The BFF also adds its own CORS headers for the SPA. The browser receives duplicate `Access-Control-Allow-Origin` headers, which some browsers treat as a CORS error (the header value contains two values separated by a comma, which is invalid per the spec).

**Why it happens:**
`http-proxy-middleware` forwards the response as-is, including all headers. The BFF adds CORS headers on top. Result: two CORS headers for the same response.

**How to avoid:**
1. Strip CORS headers from upstream (FastAPI) responses in the proxy `onProxyRes` hook:
   ```js
   onProxyRes(proxyRes) {
     delete proxyRes.headers['access-control-allow-origin'];
     delete proxyRes.headers['access-control-allow-credentials'];
     delete proxyRes.headers['access-control-allow-headers'];
     delete proxyRes.headers['access-control-allow-methods'];
   }
   ```
2. After the BFF is introduced, remove `CORSMiddleware` from FastAPI entirely — FastAPI will only be called by the BFF (a server-to-server request), which does not need CORS.
3. Add a Traefik rule or network policy to block direct browser access to `dashboard-api.pm.comsatel.com.pe` so the migration is complete.

**Warning signs:**
- CORS errors in the browser despite having seemingly correct CORS configuration.
- DevTools shows `Access-Control-Allow-Origin` with two values: `https://dashboard.pm.comsatel.com.pe, https://dashboard.pm.comsatel.com.pe`.
- FastAPI logs show requests from the BFF's IP, confirming they arrive server-to-server.

**Phase to address:** Phase 3 — BFF Proxy to FastAPI

---

### Pitfall 6: `Authorization` Header Not Forwarded to FastAPI After BFF Takeover

**What goes wrong:**
Currently the SPA sends `Authorization: Bearer <keycloak_token>` and FastAPI validates it. After the BFF takes over, the BFF must inject the Keycloak access token (stored in the session) as the `Authorization` header on every proxied request to FastAPI. If the BFF proxies the raw client request without adding this header, FastAPI receives unauthenticated requests and returns HTTP 401.

**Why it happens:**
The proxy is configured for routing (URL rewrite) but not for header injection. Developers focus on getting the proxy path working and forget that the session contains the credentials that must be forwarded.

**How to avoid:**
1. In `http-proxy-middleware`'s `onProxyReq` hook, inject the access token:
   ```js
   onProxyReq(proxyReq, req) {
     const token = req.session?.accessToken;
     if (token) {
       proxyReq.setHeader('Authorization', `Bearer ${token}`);
     }
   }
   ```
2. Also strip the incoming cookie from the proxied request (`proxyReq.removeHeader('Cookie')`) to avoid leaking the session cookie to FastAPI.
3. Ensure the session always stores the latest access token, updated after each refresh.

**Warning signs:**
- FastAPI logs show `401 Unauthorized` for every proxied request.
- The BFF session contains `accessToken` but FastAPI still rejects the request.
- FastAPI logs show no `Authorization` header in incoming requests.

**Phase to address:** Phase 3 — BFF Proxy to FastAPI

---

### Pitfall 7: CubeJS Token Expiry Not Synchronized With Keycloak Session

**What goes wrong:**
The BFF generates a CubeJS JWT on login and stores it in the session. CubeJS tokens expire (typically 1h–24h depending on configuration). When the CubeJS token expires mid-session, CubeJS returns HTTP 403. The BFF does not detect this and continues forwarding the expired token, causing all chart queries to silently fail.

**Why it happens:**
CubeJS token expiry is independent of Keycloak's access token expiry. Developers track Keycloak token refresh but forget to re-generate the CubeJS token when it expires.

**How to avoid:**
1. Store the CubeJS token alongside its `iat` (issued-at) timestamp in the session: `req.session.cubeToken` and `req.session.cubeTokenIssuedAt`.
2. Before every proxied CubeJS request, check if the token is within `CUBE_TOKEN_LIFETIME - 60s`. If expired, regenerate it from the Keycloak access token before forwarding.
3. Set CubeJS token lifetime to match or exceed Keycloak's session lifetime. A reasonable approach: generate a new CubeJS token on each Keycloak token refresh event.
4. Return a specific error code (e.g., `session_expired`) to the SPA on CubeJS 403, triggering a full re-login.

**Warning signs:**
- Dashboard widgets stop loading after ~1 hour without page reload.
- CubeJS logs show `403 Forbidden` with "JWT expired" in the error body.
- No CubeJS token refresh logic exists in the BFF.

**Phase to address:** Phase 4 — CubeJS Token Management

---

### Pitfall 8: Multi-Tenant User Context Not Included in CubeJS Token

**What goes wrong:**
CubeJS uses security context (claims inside the JWT) to filter data per user or tenant (via `queryRewrite` in `cube.js` schema). If the BFF generates a generic CubeJS token without embedding the Keycloak user's `sub`, roles, or tenant ID, all users see all data — the multi-tenant isolation is silently broken.

**Why it happens:**
The current `cubejs.js` store uses a static token from `VITE_CUBEJS_TOKEN` env var (or the backend's active config). This static token approach provides no user context. The BFF may replicate this anti-pattern if the developer treats CubeJS token generation as just "sign anything with the secret."

**How to avoid:**
1. When generating the CubeJS token in the BFF, include the Keycloak user's claims:
   ```js
   const cubeToken = jwt.sign({
     sub: session.userId,
     roles: session.roles,
     iat: Math.floor(Date.now() / 1000)
   }, process.env.CUBEJS_API_SECRET, { expiresIn: '1h' });
   ```
2. In the `cube.js` schema, use `queryRewrite` to apply row-level filters based on `securityContext.roles` or `securityContext.sub`.
3. Verify the current Cube.js deployment's `queryRewrite` configuration — if it is missing, add it as part of this milestone.

**Warning signs:**
- All users (regardless of role — designer, viewer, admin) see identical data in charts.
- CubeJS `queryRewrite` function exists but always receives an empty `securityContext`.
- The CubeJS JWT payload contains only `iat` and `exp` with no user claims.

**Phase to address:** Phase 4 — CubeJS Token Management

---

### Pitfall 9: Vue Router Guard Breaks During Migration — App Renders Before BFF Session Check

**What goes wrong:**
The current `main.js` initializes Keycloak synchronously before mounting the Vue app. The router guard then checks `authStore.isAuthenticated`. After the BFF migration, the app mounts first and makes an async call to `GET /auth/me` to hydrate the auth store. During this async gap, Vue Router may redirect unauthenticated users to `/` (the default guard behavior) before the session check completes, causing a flash of the wrong page or a redirect loop.

**Why it happens:**
The current design is synchronous: Keycloak JS resolves authentication before `app.mount()`. The new BFF model is async: the app mounts, then discovers its auth status. The router guard code `if (!authStore.isAuthenticated) return next('/')` is still pointing to a synchronous assumption.

**How to avoid:**
1. Add an `authStore.initialized` boolean flag (default `false`). Set it to `true` after the `/auth/me` check resolves (success or 401).
2. In the router's `beforeEach` guard, await initialization:
   ```js
   router.beforeEach(async (to, from, next) => {
     if (!authStore.initialized) await authStore.init(); // calls GET /auth/me
     if (!authStore.isAuthenticated && to.meta.requiresAuth) return next('/login');
     next();
   });
   ```
3. Show a global loading spinner (not a blank page) while `authStore.initialized === false`.
4. Remove the `keycloak.init(...)` block in `main.js` entirely once the BFF handles authentication — do not leave both systems active simultaneously.

**Warning signs:**
- The app briefly shows a blank page or `/` before settling on the correct route after login.
- Router guard triggers a redirect to `/` for authenticated users because `authStore.isAuthenticated` is `false` at guard execution time.
- Browser DevTools shows `GET /auth/me` completing after the router navigation has already committed.

**Phase to address:** Phase 5 — Frontend Migration (Remove Keycloak JS Adapter)

---

### Pitfall 10: Keycloak Refresh Token Stored in the BFF Session Without a Rotation Strategy

**What goes wrong:**
The BFF stores the Keycloak `refresh_token` in `req.session` indefinitely. If the session store is compromised (Redis dump, memory store leak, debug logging that prints session contents), an attacker gets a long-lived refresh token that works until it is explicitly revoked in Keycloak.

**Why it happens:**
Refresh tokens are needed to silently extend the session, so storing them server-side in the session is correct. The mistake is not implementing refresh token rotation: Keycloak returns a new refresh token on every use, but developers keep using the old one.

**How to avoid:**
1. Every time `POST /token` is called with `grant_type: refresh_token`, store the **new** refresh token from the response — do not re-use the original.
2. Enable Keycloak's built-in refresh token rotation: in the realm settings, set "Revoke Refresh Token" = ON and "Refresh Token Max Reuse" = 0.
3. Implement a session expiry policy: destroy the session if the refresh token exchange returns `invalid_grant` (Keycloak's response when refresh token is expired or revoked).
4. Never log the session contents in production — mask `accessToken`, `refreshToken`, `idToken` fields.

**Warning signs:**
- Session store contains the same `refreshToken` value for hours or days without change.
- Keycloak's "Revoke Refresh Token" setting is disabled.
- Application logs print `req.session` in error handlers.

**Phase to address:** Phase 1 — Keycloak OIDC Authorization Code Flow (security foundation)

---

### Pitfall 11: PKCE Code Verifier Lost Between Redirect and Callback

**What goes wrong:**
PKCE (S256) requires the BFF to generate a `code_verifier`, store it, hash it into a `code_challenge` for the authorization request, and then send the original `code_verifier` in the token exchange. If the `code_verifier` is stored in `req.session` but the session is not saved before the redirect (same root cause as Pitfall 3), the token exchange fails with `invalid_grant: PKCE verification failed`.

**Why it happens:**
This is the same session persistence race condition as Pitfall 3, but the failure is attributed to PKCE rather than state validation, making it confusing to debug.

**How to avoid:**
1. Store `state`, `nonce`, and `code_verifier` in a single `req.session.oidcPending` object.
2. Always call `req.session.save()` before redirecting — this ensures all three are persisted atomically.
3. Verify PKCE support in the Keycloak client configuration: the client must have "PKCE Code Challenge Method" set to `S256`.
4. Use `openid-client` which handles PKCE generation and verification automatically.

**Warning signs:**
- Keycloak returns `error: invalid_grant` during the token exchange.
- The BFF never successfully completes a login in a new Redis session (works fine with MemoryStore because writes are synchronous).
- Keycloak logs show "PKCE code verifier does not match."

**Phase to address:** Phase 1 — Keycloak OIDC Authorization Code Flow

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `MemoryStore` for `express-session` in production | Zero setup time | All sessions are lost on BFF restart; not horizontally scalable | Never in production — dev only |
| Storing `accessToken` in a cookie instead of session store | No need for a session store | Token is visible in DevTools and subject to XSS leaks (even httpOnly mitigates but does not fully eliminate risk) | Never — defeats the BFF security model |
| Leaving Keycloak JS adapter active alongside the BFF | Gradual migration, no big-bang cutover | Dual auth systems cause split brain: some routes use cookies, others use Bearer tokens; impossible to audit | Acceptable for 1 sprint max, must be removed |
| Static CubeJS token (global, no user context) | Simple to implement | All users see all data; breaks multi-tenant isolation silently | Only acceptable if CubeJS has no `queryRewrite` and data is intentionally shared |
| Proxying CubeJS with `changeOrigin: true` but no token injection | Proxy works for connectivity | CubeJS receives no user context; requests unauthenticated | Never — CubeJS must receive a per-user JWT |
| Not implementing logout at the Keycloak level (just destroying the local session) | Simple logout implementation | The Keycloak session remains alive; user can get a new session via SSO without re-entering credentials | Never — incomplete logout is a security vulnerability |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Keycloak OIDC | Using the `implicit` grant (returning tokens in URL hash) instead of authorization code flow | Always use `authorization_code` + PKCE for BFF; never put tokens in URLs |
| Keycloak OIDC | Hard-coding the token endpoint URL instead of using OIDC discovery | Fetch `/.well-known/openid-configuration` and cache the endpoints |
| Keycloak OIDC | Trusting the `state` parameter from query string before checking session | Validate `req.query.state === req.session.oidcState` as first line of the callback handler |
| express-session + Redis | Not setting `prefix` in `connect-redis`, causing session key collisions if Redis is shared with other services | Set `prefix: 'dashboardstudio:sess:'` |
| express-session + Redis | Not configuring `ttl` in `connect-redis`, so sessions never expire in Redis | Set `ttl` equal to `cookie.maxAge / 1000` (in seconds) |
| http-proxy-middleware to FastAPI | Forgetting to set `xfwd: true` so FastAPI sees `X-Forwarded-For` with the real client IP | Pass `{ xfwd: true }` in proxy options |
| http-proxy-middleware to FastAPI | Proxy path includes `/api/v1` prefix and FastAPI also prefixes routes — results in double prefix | Carefully align `pathRewrite` options with FastAPI route definitions |
| CubeJS proxy | Forwarding the browser's cookie to CubeJS | Strip `Cookie` header in `onProxyReq`; CubeJS authenticates via JWT, not cookies |
| CubeJS proxy | Not proxying WebSocket connections when CubeJS uses real-time features | Add `ws: true` to `http-proxy-middleware` options for `/cubejs-api` route |
| Vue auth store | Calling `getMe()` in `app.use(pinia)` before the store is ready | Call `authStore.init()` from `main.js` after `app.use(pinia)` resolves |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Refreshing Keycloak token on every BFF request | Each API call adds ~100ms for the Keycloak token endpoint call | Only refresh when `accessToken` is within 60s of expiry; cache `expiresAt` in session | At ~50 concurrent users with rapid clicking |
| Generating a new CubeJS JWT on every request | CubeJS request latency doubles due to JWT signing overhead | Cache the CubeJS token in the session; regenerate only on expiry | At ~20 concurrent users hitting chart widgets |
| Redis session store with no connection pooling | BFF hangs when Redis is briefly unavailable | Configure `connect-redis` with retry strategy and pool size | First Redis blip in production |
| Not compressing proxied responses | Large CubeJS result payloads (for dashboard with 10+ widgets) hit Traefik's response buffer limits | Enable `compression()` middleware in Express before proxy routes | Dashboard with >8 widgets each querying large datasets |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Allowing `redirect_uri` to be passed as a query parameter by the SPA | Open redirect attack — attacker redirects callback to attacker-controlled site | Hard-code the `redirect_uri` in BFF configuration; never accept it from the client |
| Reflecting the full error from Keycloak's token endpoint to the SPA | Information disclosure — Keycloak error messages reveal realm configuration details | Log the full error server-side; return a generic `Authentication failed` message to the SPA |
| Using `httpOnly: false` on the session cookie | XSS can steal the session cookie directly from JavaScript | Always use `httpOnly: true` — the SPA has no legitimate reason to read the session cookie |
| Logging `req.session` in error handlers or debug middleware | Access tokens and refresh tokens appear in log files | Mask or omit session token fields in all logging; use a `sanitize(session)` helper |
| Not rotating the express-session `secret` periodically | Old `secret` values can be used to forge sessions if they leak | Support an array of secrets in `express-session`: `secret: [newSecret, oldSecret]` allows graceful rotation |
| Trusting the `X-Forwarded-For` header from any source when inside Traefik | IP spoofing | Set `app.set('trust proxy', 1)` to trust only Traefik (one hop); do not set it higher |
| CubeJS API secret visible in BFF environment variables without restricted access | CubeJS secret leaked = anyone can forge tokens with admin access to all data | Use Docker secrets or a secrets manager (HashiCorp Vault); never embed in `docker-compose.yaml` plaintext |

---

## UX Pitfalls

Common user experience mistakes specific to this BFF migration.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing a blank page during the async `/auth/me` check on app load | Users see a flash of white before the app renders | Show a branded loading state (`<div class="app-loading">`) while `authStore.initialized === false` |
| Redirecting to Keycloak on every hard refresh even for active sessions | Users are forced through a redirect on F5 | The BFF's `/auth/me` endpoint returns 200 with user data if the session is valid; the SPA checks this before triggering login |
| Not preserving the original URL through the login redirect | After login, users land on `/` instead of the page they were trying to access | Store `req.query.returnTo` (or use session) before the Keycloak redirect; redirect to it after callback |
| No logout confirmation or feedback | User clicks logout, is redirected to Keycloak, then back — with no indication the logout succeeded | Show a transient "You have been logged out" notification after the post-logout redirect |
| CubeJS 403 errors rendered as generic "Error loading chart" with no recovery action | Users see broken charts with no way to recover without a full page reload | Intercept 403 from CubeJS proxy in the SPA; trigger a session refresh call (`GET /auth/refresh`) and retry the chart query once |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Keycloak Login Flow:** PKCE code verifier is generated and stored — verify it survives a session save/load cycle in Redis, not just MemoryStore.
- [ ] **CSRF Protection:** `state` parameter is stored before redirect — verify `req.session.save()` is called explicitly before `res.redirect()`.
- [ ] **Cookie Configuration:** Session cookie appears in DevTools — verify it is sent on cross-origin `fetch` calls (check that `credentials: 'include'` and `SameSite=None; Secure` are both set).
- [ ] **FastAPI Proxy:** Routes respond correctly — verify the `Authorization` header with the Keycloak token is being injected (FastAPI should log it; check with a 401 test on the backend if the header is removed).
- [ ] **CORS Cleanup:** No browser CORS errors — verify FastAPI's `CORSMiddleware` is removed or restricted to internal-only origins after the BFF is live.
- [ ] **CubeJS Proxy:** CubeJS queries work — verify the CubeJS JWT contains `sub` and `roles` claims from the authenticated Keycloak user (decode the token in CubeJS logs).
- [ ] **Logout:** Local session is destroyed — verify Keycloak logout (`/protocol/openid-connect/logout`) is also called so the upstream session is terminated.
- [ ] **Token Refresh:** Short-lived Keycloak tokens are refreshed — verify behavior after the access token expires (set token lifespan to 1 minute in Keycloak realm settings for testing).
- [ ] **Vue Router Guard:** Auth guard works — verify that a hard-refresh on a protected route does not flash a redirect to `/` before `/auth/me` resolves.
- [ ] **Keycloak JS Adapter Removed:** Old `keycloak.js` service and `main.js` init block are fully removed — verify no `import keycloak from '@/services/keycloak'` references remain in any Vue component or store.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CSRF state mismatch causing all logins to fail | LOW | Add explicit `req.session.save()` before redirect; redeploy BFF |
| Cookie not sent (SameSite misconfiguration) | LOW | Fix `sameSite: 'none'` and `credentials: 'include'` on both sides; no data migration needed |
| CORS double-header breaking API calls | LOW | Add `delete proxyRes.headers['access-control-allow-origin']` in proxy `onProxyRes`; redeploy |
| CubeJS token without user context (all users see all data) | MEDIUM | Generate per-user CubeJS tokens; update `queryRewrite` in CubeJS schema; flush cached dimension values |
| MemoryStore used in production and sessions lost on restart | MEDIUM | Add Redis, configure `connect-redis`, roll BFF; users must re-login once |
| Keycloak JS adapter not fully removed (dual auth system) | MEDIUM | Audit all `import keycloak` usages; remove auth store's `_keycloak` reference; test all routes |
| Refresh token not rotated (stale refresh token in session) | HIGH | Enable Keycloak refresh token rotation in realm settings; force all users to re-login (session flush); audit logs for anomalous refresh attempts |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Missing state/nonce validation | Phase 1 — OIDC Auth Code Flow | Integration test: callback with wrong `state` returns 400 |
| Session not saved before redirect | Phase 1 — OIDC Auth Code Flow | Test with Redis store (not MemoryStore) in dev environment |
| PKCE verifier lost | Phase 1 — OIDC Auth Code Flow | Complete login flow test in Redis-backed session environment |
| Refresh token not rotated | Phase 1 — OIDC Auth Code Flow | Keycloak realm has "Revoke Refresh Token" ON; verify new token on each refresh |
| Cookie not sent by SPA | Phase 2 — Session & Cookie Setup | Browser test: check `credentials: 'include'` in all `fetch` calls; cookie present in request headers |
| CORS double-handling | Phase 3 — FastAPI Proxy | Response headers contain single `Access-Control-Allow-Origin`; no duplicate |
| Authorization header not forwarded | Phase 3 — FastAPI Proxy | FastAPI access log shows `Authorization: Bearer ...` on proxied requests |
| CubeJS token expiry unhandled | Phase 4 — CubeJS Token Management | Charts still load after 1h without refresh (simulate with short token TTL) |
| CubeJS missing user context | Phase 4 — CubeJS Token Management | Viewer user only sees their permitted data; designer sees all |
| Router guard race condition | Phase 5 — Frontend Migration | Hard-refresh on protected route shows loading state, then correct page (no flash redirect) |
| Keycloak JS adapter not removed | Phase 5 — Frontend Migration | `grep -r "keycloak-js" src/` returns no results |

---

## Sources

- Direct codebase analysis: `dashboard-app/src/main.js`, `src/services/keycloak.js`, `src/services/api.js`, `src/stores/auth.js`, `src/stores/cubejs.js`, `src/router/index.js` — **HIGH confidence**
- OIDC Core specification (RFC 6749, OpenID Connect Core 1.0) — state/nonce/PKCE requirements — **HIGH confidence**
- RFC 7636 — PKCE (Proof Key for Code Exchange) specification — **HIGH confidence**
- OWASP Session Management Cheat Sheet — cookie flag requirements, session fixation — **HIGH confidence**
- OWASP CSRF Prevention Cheat Sheet — state parameter validation — **HIGH confidence**
- MDN Web Docs: Fetch API, `credentials: 'include'`, SameSite cookie attribute — **HIGH confidence**
- `express-session` npm package documentation — `saveUninitialized`, `resave`, `save()` behavior — **HIGH confidence**
- `http-proxy-middleware` GitHub documentation — `onProxyReq`, `onProxyRes` hooks — **HIGH confidence**
- CubeJS Security documentation — `securityContext`, `queryRewrite`, JWT payload claims — **HIGH confidence**

---
*Pitfalls research for: BFF Service Architecture (v1.8) — Keycloak OIDC / Express Session / Proxy*
*Researched: 2026-05-28*
