# Architecture Research

**Domain:** BFF Service Architecture — Dashboard Studio v1.8
**Researched:** 2026-05-28
**Confidence:** HIGH (based on direct codebase analysis)

---

## Standard Architecture

### System Overview

```
CURRENT (v1.7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────────┐     Bearer <kc_token>     ┌──────────────────────┐
  │  dashboard-app       │ ─────────────────────────► │  backend FastAPI     │
  │  Vue 3 (port 3000)   │                            │  (port 8000, Traefik)│
  │                      │   Keycloak JS adapter      │                      │
  │  keycloak.js         │◄───────────────────────────│  security.py:        │
  │  stores tokens in    │      redirect flows        │  verify_token()      │
  │  sessionStorage      │                            │  fetches JWKS        │
  │                      │                            └──────────────────────┘
  │  cubejs.js           │   Bearer <cube_jwt>        ┌──────────────────────┐
  │  token from DB via   │ ─────────────────────────► │  CubeJS              │
  │  FastAPI             │                            │  (port 4000, ext.)   │
  └──────────────────────┘                            └──────────────────────┘
             │                                                   ▲
             │ OIDC redirect                          Static JWT from DB
             ▼                                        (cube_config table)
  ┌──────────────────────┐
  │  Keycloak            │
  │  (ext. OIDC server)  │
  └──────────────────────┘


TARGET (v1.8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────────┐   httpOnly cookie session  ┌──────────────────────┐
  │  dashboard-app       │ ─────────────────────────► │  BFF                 │
  │  Vue 3 (port 3000)   │                            │  Node.js + Express   │
  │                      │   /bff/auth/login          │  (port 3001)         │
  │  NO keycloak-js      │   /bff/api/v1/...          │                      │
  │  NO token in browser │   /bff/cubejs/...          │  Session store       │
  │                      │◄──────────────────────────  │  OIDC client         │
  │  api.js points to    │   Set-Cookie: session=...  │  http-proxy-mw       │
  │  BFF base URL        │                            └──────────┬───────────┘
  └──────────────────────┘                                       │
                                                                 │ Bearer <kc_token> (forwarded)
                                                                 ▼
                                            ┌───────────────────────────────────────┐
                                            │                                       │
                               ┌────────────▼──────────┐   ┌──────────────────────┐│
                               │  backend FastAPI       │   │  CubeJS              ││
                               │  (port 8000, internal) │   │  (port 4000, int.)   ││
                               │                        │   │                      ││
                               │  security.py:          │   │  JWT signed by BFF   ││
                               │  verify_token()        │   │  (shared secret)     ││
                               │  unchanged             │   └──────────────────────┘│
                               └────────────────────────┘                           │
                                            │                                       │
                                            └───────────────────────────────────────┘
                                                         ▲
                                            ┌────────────┴──────────┐
                                            │  Keycloak             │
                                            │  (ext. OIDC server)   │
                                            │  JWKS, token endpoint │
                                            └───────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Change in v1.8 |
|-----------|----------------|----------------|
| dashboard-app | Vue 3 SPA, renders UI, calls APIs | Remove keycloak-js; point api.js to BFF |
| BFF | Auth flows, session management, proxy to backend + CubeJS | NEW service |
| backend FastAPI | Business logic only, CRUD, flow execution | Keep verify_token; add internal-only CORS |
| CubeJS | Semantic layer for analytical queries | Unchanged; JWT now signed server-side |
| Keycloak | External OIDC identity provider | Unchanged; BFF becomes the OIDC relying party |

---

## Port Layout

| Service | Dev port | Docker-internal | Production (Traefik) |
|---------|----------|-----------------|----------------------|
| dashboard-app (Nginx) | 3000 | 80 | dashboard.pm.comsatel.com.pe |
| BFF (Express) | 3001 | 3001 | dashboard-bff.pm.comsatel.com.pe (or same domain, /bff) |
| backend (FastAPI) | 8000 | 8000 | dashboard-api.pm.comsatel.com.pe (restrict to internal) |
| CubeJS | 4000 | 4000 | (internal only — never exposed to public) |

**Recommendation:** Use a single external hostname and path-prefix routing via Traefik or an upstream Nginx in the frontend image:
- `dashboard.pm.comsatel.com.pe/bff/*` → BFF:3001
- BFF:3001 proxies internally to backend:8000 and cubejs:4000

This avoids CORS headaches because frontend and BFF share the same origin. The httpOnly session cookie has `SameSite=Lax` and `Secure`, which works cross-origin if needed but is simpler at the same origin.

---

## Recommended Project Structure

```
bff/                              # New top-level service
├── package.json
├── Dockerfile
├── .env.example
└── src/
    ├── index.js                  # Express app entry point, port 3001
    ├── config.js                 # Env-driven config (Keycloak, backend URL, CubeJS URL)
    ├── middleware/
    │   ├── session.js            # express-session + connect-pg-simple or memorystore
    │   └── requireSession.js     # Guard: 401 if no active session
    ├── routes/
    │   ├── auth.js               # GET /bff/auth/login, /bff/auth/callback, /bff/auth/logout
    │   │                         # POST /bff/auth/refresh, GET /bff/auth/me
    │   ├── api.js                # ALL /bff/api/* → http-proxy-middleware → FastAPI
    │   └── cubejs.js             # ALL /bff/cubejs/* → http-proxy-middleware → CubeJS
    └── lib/
        ├── oidcClient.js         # openid-client: discovery, authorizationUrl, callback
        └── cubeToken.js          # jsonwebtoken.sign() with CUBEJS_API_SECRET
```

---

## Architectural Patterns

### Pattern 1: Server-Side Session with httpOnly Cookie

**What:** BFF stores Keycloak access token and refresh token in a server-side session. The browser receives only an opaque session ID cookie. No tokens are ever sent to the browser.

**When to use:** Required when the goal is to prevent token theft via XSS. The Keycloak `frame-ancestors 'self'` CSP already blocks the silent iframe refresh; this pattern eliminates client-side token entirely.

**Trade-offs:** Statefulness on the BFF. The session store must survive BFF restarts (use Redis or PostgreSQL-backed sessions in production; in-memory is acceptable for single-instance dev).

**Implementation sketch:**
```javascript
// src/middleware/session.js
import session from 'express-session'

export default session({
  secret: process.env.SESSION_SECRET,
  name: 'dsid',               // cookie name — opaque, not "connect.sid"
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',  // HTTPS in prod
    sameSite: 'lax',
    maxAge: 8 * 60 * 60 * 1000  // 8 hours — matches Keycloak SSO session
  }
})
```

**Session payload (stored server-side, never in cookie):**
```javascript
req.session.tokens = {
  accessToken: '...',          // Keycloak access JWT
  refreshToken: '...',
  idToken: '...',
  expiresAt: Date.now() + 300_000  // ms
}
req.session.user = {
  sub: '...',
  email: '...',
  name: '...',
  roles: ['designer']
}
```

### Pattern 2: OIDC Authorization Code Flow (Server-Side)

**What:** BFF initiates and completes the OIDC Authorization Code + PKCE flow on behalf of the SPA. The frontend redirects to `GET /bff/auth/login` instead of calling `keycloak.login()`.

**When to use:** Required when removing keycloak-js from the browser.

**Trade-offs:** BFF must be a registered OIDC client in Keycloak with its own `client_id` and `client_secret` (confidential client). The existing `dashboard-app` public client in Keycloak can be retired or kept for fallback.

**Keycloak client required:**
- Client ID: `dashboard-bff`
- Client type: Confidential
- Valid Redirect URIs: `https://dashboard.pm.comsatel.com.pe/bff/auth/callback`
- Service accounts: not needed

**Flow:**
```
Browser            BFF                    Keycloak
  |                 |                        |
  |--GET /bff/auth/login-->                  |
  |                 |--302 redirect-------->  |
  |<--------302 to Keycloak login----------  |
  |                 |                        |
  |--POST credentials (user types)---------> |
  |<--------302 to /bff/auth/callback------  |
  |                 |                        |
  |--GET /bff/auth/callback?code=xxx-------> |
  |                 |--exchange code-------> |
  |                 |<--tokens (access+refresh+id)--|
  |                 |--store in session       |
  |<--Set-Cookie: dsid=xxx; redirect to /   |
```

**openid-client usage:**
```javascript
// src/lib/oidcClient.js
import { Issuer } from 'openid-client'

let _client = null

export async function getOidcClient() {
  if (_client) return _client
  const issuer = await Issuer.discover(
    `${process.env.KEYCLOAK_URL}/realms/${process.env.KEYCLOAK_REALM}`
  )
  _client = new issuer.Client({
    client_id: process.env.KEYCLOAK_CLIENT_ID,       // dashboard-bff
    client_secret: process.env.KEYCLOAK_CLIENT_SECRET,
    redirect_uris: [process.env.BFF_CALLBACK_URL],   // /bff/auth/callback
    response_types: ['code'],
  })
  return _client
}
```

### Pattern 3: Token Forwarding to FastAPI (Transparent Proxy)

**What:** BFF reads `req.session.tokens.accessToken` and attaches it as `Authorization: Bearer <token>` on every proxied request to FastAPI. FastAPI's existing `security.py` (`verify_token`, JWKS validation) is completely unchanged.

**When to use:** This is the minimal-change option for the backend. FastAPI keeps validating Keycloak JWTs — it just receives them from the BFF instead of from the browser.

**Trade-offs:** FastAPI still hits Keycloak JWKS on every token KID lookup (cached hourly in memory). If the BFF later rotates to service-account tokens instead, FastAPI would need no change there either.

**Token refresh before proxy:**
```javascript
// src/middleware/requireSession.js
export async function withTokenRefresh(req, res, next) {
  if (!req.session.tokens) return res.status(401).json({ detail: 'Not authenticated' })

  const { expiresAt, refreshToken } = req.session.tokens
  // Refresh if token expires within 60 seconds
  if (Date.now() > expiresAt - 60_000) {
    try {
      const client = await getOidcClient()
      const refreshed = await client.refresh(refreshToken)
      req.session.tokens = {
        accessToken: refreshed.access_token,
        refreshToken: refreshed.refresh_token ?? refreshToken,
        idToken: refreshed.id_token,
        expiresAt: Date.now() + (refreshed.expires_in * 1000)
      }
    } catch {
      req.session.destroy()
      return res.status(401).json({ detail: 'Session expired' })
    }
  }
  next()
}
```

**http-proxy-middleware setup:**
```javascript
// src/routes/api.js
import { createProxyMiddleware } from 'http-proxy-middleware'
import { withTokenRefresh } from '../middleware/requireSession.js'

const apiProxy = createProxyMiddleware({
  target: process.env.BACKEND_URL,  // http://backend:8000
  changeOrigin: true,
  pathRewrite: { '^/bff/api': '/api' },
  on: {
    proxyReq: (proxyReq, req) => {
      // Inject the stored Keycloak access token
      proxyReq.setHeader('Authorization', `Bearer ${req.session.tokens.accessToken}`)
    }
  }
})

router.use('/*', withTokenRefresh, apiProxy)
```

### Pattern 4: CubeJS JWT Generated Server-Side

**What:** CubeJS requires a signed JWT to authorize queries. Currently the token is stored (encrypted) in FastAPI's `cube_config` table and sent to the browser via `/api/v1/cube-config/active`. With the BFF, the BFF fetches the `CUBEJS_API_SECRET` from env and signs a JWT server-side on each request or on session creation. The browser never sees the secret or the signed token.

**When to use:** Always preferred over exposing CUBEJS_API_SECRET to the frontend.

**CubeJS JWT structure:**
```javascript
// src/lib/cubeToken.js
import jwt from 'jsonwebtoken'

export function signCubeToken(userRoles = []) {
  return jwt.sign(
    {
      // Claims that CubeJS security context can read for row-level security
      roles: userRoles,
      iat: Math.floor(Date.now() / 1000),
    },
    process.env.CUBEJS_API_SECRET,
    { expiresIn: '1h', algorithm: 'HS256' }
  )
}
```

**CubeJS proxy:**
```javascript
// src/routes/cubejs.js
const cubeProxy = createProxyMiddleware({
  target: process.env.CUBEJS_URL,   // http://cubejs:4000
  changeOrigin: true,
  pathRewrite: { '^/bff/cubejs': '/cubejs-api' },
  on: {
    proxyReq: (proxyReq, req) => {
      const token = signCubeToken(req.session.user?.roles ?? [])
      proxyReq.setHeader('Authorization', `Bearer ${token}`)
    }
  }
})
router.use('/*', withTokenRefresh, cubeProxy)
```

**Frontend change:** `cubejs.js` store changes `apiUrl` to `/bff/cubejs/v1` and removes the `token` field (token is injected server-side, browser sends cookies only).

---

## Data Flow

### Request Flow (Authenticated API Call)

```
[User action in Vue component]
         |
         | fetch('/bff/api/v1/dashboards/')
         | + Cookie: dsid=abc123 (automatic, no JS required)
         v
[BFF Express]
  - requireSession: lookup session by dsid
  - withTokenRefresh: token still valid? skip / refresh
  - http-proxy-middleware → http://backend:8000/api/v1/dashboards/
  + Authorization: Bearer <keycloak_access_token>
         |
         v
[FastAPI backend]
  - verify_token() unchanged: validates Keycloak JWT via JWKS
  - returns JSON
         |
         v
[BFF] → forwards response body unchanged → [Browser]
```

### Auth Flow (Login)

```
[Browser visits /]
  → authStore detects no session (GET /bff/auth/me returns 401)
  → redirect to /bff/auth/login
         |
[BFF] generates state + PKCE verifier, stores in req.session
  → 302 redirect to Keycloak /auth endpoint
         |
[Keycloak] user logs in → 302 to /bff/auth/callback?code=xxx
         |
[BFF /auth/callback]
  → exchange code for tokens (openid-client)
  → store tokens in session
  → 302 redirect to '/'
         |
[Browser loads app] → GET /bff/auth/me → { sub, email, name, roles }
  → authStore.initFromBff(userInfo)
```

### CubeJS Query Flow

```
[Vue cubejs store]
  cubejs('@COOKIE_BASED@', { apiUrl: '/bff/cubejs/v1' })
  → HTTP GET /bff/cubejs/v1/meta  + Cookie: dsid=abc123
         |
[BFF /bff/cubejs/*]
  → signCubeToken(session.user.roles)
  → proxy to http://cubejs:4000/cubejs-api/v1/meta
  + Authorization: Bearer <signed_cube_jwt>
         |
[CubeJS] validates JWT with CUBEJS_API_SECRET → returns meta
```

---

## Integration Points

### BFF ↔ Frontend (dashboard-app)

| Concern | Current | After BFF |
|---------|---------|-----------|
| Login | keycloak.login() in main.js | redirect to GET /bff/auth/login |
| Auth state | keycloak.tokenParsed | GET /bff/auth/me → JSON user object |
| Token refresh | keycloak.updateToken() in api.js | Transparent — BFF handles in proxy |
| Logout | keycloak.logout() in authStore | POST /bff/auth/logout → destroy session → redirect to Keycloak logout |
| API base URL | VITE_API_URL (port 8000) | /bff/api (same origin, no VITE needed) |
| CubeJS URL | VITE_CUBEJS_API_URL + VITE_CUBEJS_TOKEN | /bff/cubejs/v1 (no token, cookie only) |
| Role guards | parsed from keycloak.tokenParsed | parsed from /bff/auth/me response |

**Files to modify in dashboard-app:**
- `src/main.js` — remove keycloak init, replace with /bff/auth/me fetch
- `src/services/keycloak.js` — can be deleted entirely
- `src/services/api.js` — change `API_BASE_URL` to `/bff/api`; remove `getAuthHeaders()`; use plain `fetch` with `credentials: 'include'`
- `src/stores/auth.js` — replace `initFromKeycloak()` with `initFromBff(userInfo)`; remove `_keycloak` reference
- `src/stores/cubejs.js` — remove `token` field; set `apiUrl` to `/bff/cubejs/v1`; remove `loadConfigFromBackend` for token (URL still comes from backend or env)

### BFF ↔ Backend (FastAPI)

| Concern | Detail |
|---------|--------|
| Token mechanism | BFF forwards the original Keycloak access token in `Authorization: Bearer` header |
| No backend changes required | `security.py` verify_token() and get_current_user() are completely unchanged |
| CORS change needed | FastAPI CORS `origins` list should remove `localhost:3000` and add `localhost:3001` (BFF origin) for dev; in prod, backend can restrict to the BFF internal hostname only |
| User provisioning | `POST /api/v1/users/provision-batch` stays as-is; BFF proxies it transparently |
| JWKS caching | Stays in FastAPI security.py in-memory cache; no change |

**Files to modify in backend:**
- `app/main.py` — update CORS `origins` list to include BFF dev port and restrict to internal network in prod; the exception handler's allowed list also needs updating

### BFF ↔ CubeJS

| Concern | Detail |
|---------|--------|
| Token mechanism | BFF signs a fresh JWT per-request using `CUBEJS_API_SECRET` |
| CubeJS configuration | Unchanged — CubeJS is already running as an internal service |
| Security context | BFF can embed user roles in JWT payload for CubeJS row-level security |
| Frontend CubeJS client | `@cubejs-client/core` connects to `/bff/cubejs/v1` without a token; session cookie is sent automatically |

### BFF ↔ Keycloak

| Concern | Detail |
|---------|--------|
| New Keycloak client needed | Register `dashboard-bff` as a **confidential** client with PKCE |
| Redirect URI | `https://dashboard.pm.comsatel.com.pe/bff/auth/callback` |
| Old client | `dashboard-app` public client can be kept (for legacy dev) or retired |
| Token storage | BFF stores tokens server-side; Keycloak never sees the browser again after callback |
| Session logout | On `/bff/auth/logout`, BFF destroys session then redirects to Keycloak's end-session endpoint |

---

## Docker Compose Changes

The existing `docker-compose.yaml` has two services (`backend`, `frontend-app`). The BFF becomes a third service:

```yaml
# Addition to docker-compose.yaml

  bff:
    build:
      context: ./bff
      dockerfile: Dockerfile
    env_file:
      - ./.env-bff           # New env file with BFF-specific config
    # ports:
    #   - "3001:3001"        # Expose locally for dev; Traefik routes in prod
    restart: unless-stopped
    depends_on:
      - backend
    labels:
      traefik.enable: true
      traefik.http.routers.dashboard-bff.rule: Host(`dashboard.pm.comsatel.com.pe`) && PathPrefix(`/bff`)
      traefik.http.routers.dashboard-bff.entrypoints: web-secure
      traefik.http.routers.dashboard-bff.tls: true
      traefik.http.services.dashboard-bff.loadbalancer.server.port: 3001
    networks:
      - frontends
      - backends
```

**New `.env-bff` file contents:**
```env
NODE_ENV=production
PORT=3001
SESSION_SECRET=<random-256-bit>
KEYCLOAK_URL=https://oauth2.qa.comsatel.com.pe
KEYCLOAK_REALM=Apps
KEYCLOAK_CLIENT_ID=dashboard-bff
KEYCLOAK_CLIENT_SECRET=<from-keycloak-admin>
BFF_CALLBACK_URL=https://dashboard.pm.comsatel.com.pe/bff/auth/callback
BACKEND_URL=http://backend:8000
CUBEJS_URL=http://cubejs:4000
CUBEJS_API_SECRET=<same-secret-used-by-cubejs-container>
FRONTEND_URL=https://dashboard.pm.comsatel.com.pe
```

**Network topology:** Both `backend` and `bff` need to be on the `backends` network so BFF can reach `http://backend:8000`. The `frontend-app` only needs `frontends` (it serves static files). BFF needs both `frontends` (Traefik routes to it) and `backends` (to reach FastAPI and CubeJS).

---

## New Components vs. Modified Components

### New Components (Create from Scratch)

| Component | Location | Purpose |
|-----------|----------|---------|
| BFF Express app | `bff/src/index.js` | Entry point, Express setup |
| OIDC client wrapper | `bff/src/lib/oidcClient.js` | openid-client Keycloak integration |
| CubeJS token signer | `bff/src/lib/cubeToken.js` | jsonwebtoken.sign() for CubeJS |
| Session middleware | `bff/src/middleware/session.js` | express-session configuration |
| Auth guard | `bff/src/middleware/requireSession.js` | 401 guard + token refresh |
| Auth routes | `bff/src/routes/auth.js` | /login, /callback, /logout, /me |
| API proxy routes | `bff/src/routes/api.js` | Proxy all /bff/api/* to FastAPI |
| CubeJS proxy routes | `bff/src/routes/cubejs.js` | Proxy all /bff/cubejs/* to CubeJS |
| BFF Dockerfile | `bff/Dockerfile` | Node.js Alpine image |
| BFF env example | `bff/.env.example` | Documentation for env vars |

### Modified Components (Update Existing)

| Component | File | Scope of Change |
|-----------|------|----------------|
| Main app bootstrap | `dashboard-app/src/main.js` | Remove keycloak init (60+ lines); replace with /bff/auth/me fetch; mount app on success |
| Auth store | `dashboard-app/src/stores/auth.js` | Replace initFromKeycloak(); remove _keycloak reference; add initFromBff() |
| API client | `dashboard-app/src/services/api.js` | Change base URL; remove getAuthHeaders(); add credentials:'include' to fetch |
| CubeJS store | `dashboard-app/src/stores/cubejs.js` | Remove token field from state/config; set apiUrl to /bff/cubejs/v1 |
| FastAPI CORS | `backend/app/main.py` | Add BFF origin to allowed origins list; update exception handler list |
| docker-compose | `docker-compose.yaml` | Add `bff` service block |

### Deleted Components

| Component | File | Reason |
|-----------|------|--------|
| Keycloak JS service | `dashboard-app/src/services/keycloak.js` | Auth moved to BFF entirely |

---

## Suggested Build Order

Building the BFF in this order respects dependencies and allows incremental validation:

### Phase 1 — BFF Foundation (no frontend changes yet)

Build the BFF service with auth and session, but leave the frontend untouched. Test auth flows with browser directly hitting `/bff/auth/login`.

1. `bff/` scaffolding: `package.json`, `Dockerfile`, `src/index.js`, `config.js`
2. Session middleware (`express-session`)
3. OIDC client (`openid-client`) + auth routes (`/login`, `/callback`, `/logout`, `/me`)
4. Verify: browser hits `/bff/auth/login` → Keycloak → `/bff/auth/callback` → session set → `/bff/auth/me` returns user JSON
5. Add to `docker-compose.yaml` with correct networks

### Phase 2 — API Proxy

Add the FastAPI proxy. Keep CORS open temporarily to allow direct frontend testing.

6. `requireSession` middleware with token refresh
7. `http-proxy-middleware` for `/bff/api/*` → FastAPI
8. Inject `Authorization: Bearer` from session
9. Update FastAPI CORS to add BFF port
10. Verify: curl/Postman with session cookie proxied to FastAPI returns data

### Phase 3 — CubeJS Proxy

11. `cubeToken.js` JWT signer
12. `http-proxy-middleware` for `/bff/cubejs/*` → CubeJS
13. Inject signed cube JWT per request
14. Verify: `/bff/cubejs/v1/meta` returns cube schema

### Phase 4 — Frontend Migration

Only after BFF is confirmed working end-to-end with curl.

15. Update `api.js`: change base URL to `/bff/api`, remove auth headers, add `credentials: 'include'`
16. Update `cubejs.js` store: remove token, set apiUrl to `/bff/cubejs/v1`
17. Update `main.js`: remove keycloak init; replace with fetch(`/bff/auth/me`) + mount
18. Update `auth.js` store: replace `initFromKeycloak()` with `initFromBff()`
19. Delete `keycloak.js` service
20. Update `main.py` CORS origins
21. End-to-end smoke test: full login flow in browser, API calls, CubeJS queries

---

## Anti-Patterns

### Anti-Pattern 1: Storing Keycloak Tokens in the BFF's Memory Only

**What people do:** Skip a real session store; keep tokens in a `Map` in process memory keyed by session ID.

**Why it's wrong:** BFF restart loses all sessions, forcing all users to re-login. Unacceptable in production, and cannot scale to multiple BFF replicas.

**Do this instead:** Use `express-session` backed by a persistent store. For single-replica deployments, `connect-pg-simple` (same PostgreSQL already used by FastAPI) is simplest. For multi-replica, use `connect-redis`.

### Anti-Pattern 2: Generating One CubeJS Token Per Session (Long-Lived)

**What people do:** Sign a cube JWT at login time and store it in the session alongside the Keycloak tokens.

**Why it's wrong:** CubeJS tokens have a fixed expiry. If the BFF signs a 1-hour token at login and the session lasts 8 hours, queries will fail silently after the first hour.

**Do this instead:** Sign a fresh CubeJS JWT on each proxied request to CubeJS (`signCubeToken()` in the proxy middleware). `jwt.sign()` with HS256 is synchronous and costs ~0.1ms. No caching needed.

### Anti-Pattern 3: Making FastAPI Call Keycloak Userinfo to Validate BFF Requests

**What people do:** Add a new auth mode to FastAPI where requests from BFF include a custom `X-BFF-Token` header, and FastAPI validates it by calling Keycloak `/userinfo`.

**Why it's wrong:** Unnecessary coupling, adds latency, and the simpler solution (forwarding the original Keycloak JWT) already works with the existing `verify_token()` with zero backend changes.

**Do this instead:** BFF forwards the original Keycloak access token as `Authorization: Bearer`. FastAPI validates it with JWKS as before. No new auth mode needed.

### Anti-Pattern 4: Stripping Authentication from FastAPI Entirely

**What people do:** Plan to "clean up" FastAPI by removing all Keycloak auth checks since "the BFF handles it now."

**Why it's wrong:** FastAPI would then be an unauthenticated service on the internal network. Any service on the Docker network (including other containers or a compromised container) could call it without authentication. Defense in depth requires the backend to still validate tokens.

**Do this instead:** Keep `verify_token()` and all `Depends(get_current_user)` decorators in FastAPI unchanged. The BFF is the public entry point but FastAPI is not blind.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 concurrent users | In-memory session store acceptable; single BFF instance |
| 10-500 users | connect-pg-simple (reuse existing PG); single BFF instance |
| 500+ users | Redis session store; BFF can be horizontally scaled (stateless once session is in Redis) |

The BFF is naturally the first bottleneck for session throughput. Because Keycloak access tokens are forwarded and FastAPI validates independently, the backend is not affected by BFF scaling choices.

---

## Integration Points Summary Table

| Touchpoint | Protocol | Auth Mechanism | Change Required |
|------------|----------|----------------|-----------------|
| Frontend → BFF | HTTP + httpOnly cookie | Session ID in cookie | Frontend: remove keycloak-js; update base URLs |
| BFF → FastAPI | HTTP (internal Docker network) | Bearer <Keycloak JWT> forwarded | FastAPI: CORS origin update only |
| BFF → CubeJS | HTTP (internal Docker network) | Bearer <BFF-signed HS256 JWT> | None in CubeJS config |
| BFF → Keycloak | OIDC Authorization Code + PKCE | client_id + client_secret | Register new confidential client |
| FastAPI → Keycloak | JWKS fetch (cached 1h) | N/A (reads public keys) | None |

---

## Sources

- Direct analysis of codebase (HIGH confidence):
  - `dashboard-app/src/main.js` — keycloak-js init pattern, PKCE, sessionStorage tokens
  - `dashboard-app/src/services/keycloak.js` — Keycloak client config
  - `dashboard-app/src/services/api.js` — Bearer token injection, API endpoint inventory
  - `dashboard-app/src/stores/auth.js` — role extraction from tokenParsed
  - `dashboard-app/src/stores/cubejs.js` — CubeJS token loaded from backend DB
  - `backend/app/core/security.py` — JWKS-based verify_token, get_current_user
  - `backend/app/core/config.py` — Keycloak URLs, CORS origins setting
  - `backend/app/main.py` — CORS middleware configuration
  - `backend/app/api/router.py` — full API surface (15 route groups)
  - `docker-compose.yaml` — Traefik labels, network topology
- openid-client library: https://github.com/panva/node-openid-client (MEDIUM confidence — widely used, well maintained)
- http-proxy-middleware: https://github.com/chimurai/http-proxy-middleware (HIGH confidence — de facto standard for Express proxying)
- express-session: https://github.com/expressjs/session (HIGH confidence — official Express ecosystem)
- CubeJS JWT auth: https://cube.dev/docs/product/auth (MEDIUM confidence — based on training data, verify HS256 secret name matches running CubeJS container env)

---

*Architecture research for: BFF Service Architecture (v1.8)*
*Researched: 2026-05-28*
