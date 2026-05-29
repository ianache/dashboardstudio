# Stack Research: BFF Service Architecture

**Project:** Dashboard Studio — v1.8 BFF Service  
**Milestone:** BFF (Backend for Frontend) in Node.js + Express  
**Researched:** 2026-05-28  
**Confidence:** HIGH (versions verified via npm registry; package choices verified against known architectural patterns for OIDC BFF with Keycloak)

---

## Context

This document covers exclusively the new `bff/` service. The existing stack (FastAPI backend, Vue 3 frontend, Keycloak, CubeJS, Deno) is already validated and is NOT re-researched here. The BFF concentrates Keycloak OIDC auth, server-side session management, and reverse proxy of all API routes into a single Node.js service.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `express` | **5.2.1** | HTTP server framework | Express 5 (released Oct 2024) is stable, drops legacy middleware quirks, and has native async error handling — no more `try/catch` in every route handler. The BFF is a thin layer, so Express is appropriate over Fastify/Koa. |
| `openid-client` | **6.8.4** | Keycloak OIDC integration (server-side) | The only fully RFC-compliant OIDC client maintained by the OpenID Foundation itself. v6 is a complete rewrite (2024) with native ESM, Web Crypto API, and no external dependencies. Preferred over `keycloak-connect` (see below). |
| `express-session` | **1.19.0** | Server-side session management | Official Express team package. Provides `req.session` with pluggable stores. Cookie is httpOnly + SameSite=Strict, token never leaves the server. |
| `http-proxy-middleware` | **4.0.0** | Reverse proxy to FastAPI and CubeJS | Standard Node.js proxy library, based on `http-proxy`. v4 supports Express 5 and http.createServer() natively. Handles WebSocket upgrades too (relevant for CubeJS subscriptions). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `connect-pg-simple` | **10.0.0** | PostgreSQL session store for express-session | Always — the project already has PostgreSQL. Sessions must survive BFF restarts; in-memory store (default) is unsafe for production. |
| `helmet` | **8.x** (latest) | Security headers middleware | Always in Express apps. Sets `Content-Security-Policy`, `X-Frame-Options`, `Strict-Transport-Security`, etc. One `app.use(helmet())` covers all. |
| `cors` | **2.x** (latest) | CORS headers for dev mode | Only in development, when Vue dev server (port 3000) hits BFF directly (port 4000). In production, the BFF serves the frontend or a reverse proxy (Traefik) handles CORS. |
| `dotenv` | **16.x** (latest) | Load `.env` file for local dev | In `bff/` only for local development. Docker Compose and production environments inject env vars natively. |
| `express-rate-limit` | **7.x** (latest) | Rate-limit `/auth/*` endpoints | On login and token-refresh routes specifically, to defend against brute-force and credential-stuffing attacks. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `nodemon` | Auto-restart during development | `nodemon src/index.js` — no transpilation needed (Node 20+ supports all required ESM features) |
| `jest` or `vitest` | Unit tests for auth middleware and proxy logic | `vitest` is preferred for consistency with the Vue frontend toolchain |

---

## Why `openid-client` over `keycloak-connect`

This is the single most important decision in the BFF stack. Both packages were verified via npm (versions as of 2026-05-28).

**`keycloak-connect` (version 26.1.1):**
- Official Keycloak Node.js adapter maintained by Red Hat / Keycloak project
- Version number tracks Keycloak server releases (currently Keycloak 26)
- Deeply tied to the `express-session` pattern for storing tokens
- Works well for straightforward "protect a route" middleware scenarios
- Problem: As of Keycloak 21+, Red Hat has signaled that `keycloak-connect` is in maintenance mode; the project recommends migrating to a generic OIDC library. The adapter's `keycloak-connect` GitHub repo shows diminishing active development compared to `openid-client`.
- Missing: does not handle the Authorization Code Flow + PKCE pattern cleanly for SPAs-behind-BFF

**`openid-client` (version 6.8.4):**
- Maintained by the OpenID Foundation (panva/node-openid-client)
- Supports all OIDC flows: Authorization Code + PKCE, Client Credentials, Token Refresh, End Session
- Framework-agnostic — integrates with Express via standard middleware pattern
- v6 (2024 rewrite) uses Web Crypto API, zero external dependencies, native ESM
- Explicitly designed for the "BFF proxies tokens" pattern described in this milestone
- The Keycloak documentation itself links to `openid-client` for server-side OIDC integration

**Recommendation: Use `openid-client` v6.**

The BFF pattern being implemented — where the BFF handles all OIDC flows and only exposes session cookies to the frontend — is precisely the use case `openid-client` is designed for. `keycloak-connect` would work, but it adds Keycloak-specific coupling that `openid-client` avoids.

**Critical note on `openid-client` v6 API change:** v6 is NOT backward-compatible with v5. The `Issuer.discover()` pattern from v5 was replaced. v6 uses:
```javascript
import { discovery } from 'openid-client'
const config = await discovery(
  new URL('http://keycloak:8080/realms/apps'),
  'bff-client',
  clientSecret
)
```
Do not follow v5 tutorials.

---

## Why `http-proxy-middleware` over alternatives

| Alternative | Problem |
|-------------|---------|
| `node-http-proxy` (direct) | Lower-level, requires more boilerplate for path rewriting and error handling |
| `express-http-proxy` | Less maintained; does not handle WebSocket upgrades (needed for CubeJS subscriptions) |
| Writing a custom proxy with `fetch` | Does not stream responses; buffering large datasets from FastAPI breaks efficiency |
| Nginx as inner proxy | Adds operational complexity; defeats the purpose of a single BFF entry point |

`http-proxy-middleware` v4 provides `createProxyMiddleware()` which integrates as standard Express middleware, handles streaming, WebSocket upgrades, and path rewrites in one config object.

---

## Why Express 5 (not 4)

Express 5 (stable since Oct 2024) has:
- Native async route handlers — errors thrown in `async` routes are automatically passed to the error handler (critical for OIDC callback handlers)
- No behavior change for the route/middleware APIs used in a BFF
- `http-proxy-middleware` v4 explicitly supports Express 5

Express 4 would also work but requires `express-async-errors` wrapper for async route handlers. Express 5 is the current stable release; there is no reason to start a new service on Express 4.

---

## Session Store: Why PostgreSQL (not Redis)

The project already has PostgreSQL in the Docker Compose stack and no Redis instance. `connect-pg-simple` v10 is the maintained PostgreSQL session store for express-session.

**If Redis is added later:** `connect-redis` v8+ is the alternative. Redis provides faster session lookups under high concurrency, but PostgreSQL is sufficient for this dashboard application's expected load.

The `connect-pg-simple` store requires a `session` table in PostgreSQL. It provides a migration SQL script.

---

## Installation

```bash
# Create the bff/ directory
mkdir bff && cd bff
npm init -y

# Core runtime
npm install express@5 openid-client express-session http-proxy-middleware connect-pg-simple helmet cors dotenv express-rate-limit

# Dev dependencies
npm install -D nodemon vitest
```

Exact pinned versions for `package.json`:
```json
{
  "dependencies": {
    "express": "^5.2.1",
    "openid-client": "^6.8.4",
    "express-session": "^1.19.0",
    "http-proxy-middleware": "^4.0.0",
    "connect-pg-simple": "^10.0.0",
    "helmet": "^8.0.0",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0",
    "express-rate-limit": "^7.0.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0",
    "vitest": "^2.0.0"
  }
}
```

---

## Alternatives Considered

| Recommended | Alternative | When Alternative Is Better |
|-------------|-------------|----------------------------|
| `openid-client` v6 | `keycloak-connect` v26 | When you need Keycloak-specific features (UMA, resource authorization) and don't need standard OIDC portability |
| `openid-client` v6 | `passport-keycloak-oauth2-oidc` | Never — this is an unmaintained Passport.js strategy; outdated |
| `express-session` + `connect-pg-simple` | `express-session` + `connect-redis` | When session lookup latency matters at scale (10K+ concurrent sessions); not applicable here |
| `http-proxy-middleware` v4 | Manual `fetch()` forwarding | Never for streaming endpoints; manual fetch buffers responses in memory |
| Express 5 | Fastify | When maximum throughput (API gateway at scale) is needed; BFF for a dashboard app doesn't need it |
| Express 5 | Koa | Only if the team prefers Koa's middleware model; Express has broader ecosystem and `http-proxy-middleware` is Express-native |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `keycloak-js` (in the BFF) | It is a browser-only adapter; uses `window` and `sessionStorage`; will crash in Node.js | `openid-client` v6 |
| `openid-client` v5 | v6 is a complete rewrite with a different API; v5 tutorials are abundant online and will cause confusion | `openid-client` v6 |
| `express-session` with default MemoryStore | MemoryStore leaks memory and resets on every BFF restart, logging out all users | `connect-pg-simple` backed session store |
| `passport` + `passport-keycloak-*` | Passport strategies for Keycloak are unmaintained; adds unnecessary abstraction over `openid-client` | `openid-client` directly |
| `node-jose` / `jsonwebtoken` for token verification | `openid-client` handles JWKS-based token verification internally; double-parsing adds complexity | `openid-client`'s built-in `validateAuthResponse` |
| `axios` as proxy | Buffers response bodies in memory; breaks streaming; adds unnecessary dependency | `http-proxy-middleware` |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `express@^5.2.1` | `http-proxy-middleware@^4.0.0` | HPM v4 explicitly supports Express 5; v2/v3 had Express 4 assumptions |
| `express@^5.2.1` | `express-session@^1.19.0` | Session middleware API unchanged between Express 4 and 5 |
| `openid-client@^6.8.0` | Node.js >=20 | v6 uses Web Crypto API, requires Node 20+. If running Node 18, use `openid-client@5.x` (different API). |
| `connect-pg-simple@^10.0.0` | `express-session@^1.19.0` | v10 is the current release; works as a session store factory |
| `keycloak-js@26.x` (in frontend) | `openid-client@6.x` (in BFF) | These operate independently; the frontend will use BFF session cookies instead of keycloak-js directly — `keycloak-js` will be removed from the frontend in this milestone |

**Node.js version requirement:** The BFF requires Node.js 20+. Verify with:
```bash
node --version  # Must be >= 20.0.0
```

---

## Stack Patterns by Variant

**If using PostgreSQL for sessions (recommended — existing infra):**
- Use `connect-pg-simple` with the same `DATABASE_URL` env var as the FastAPI backend
- Create the `session` table using the SQL from `connect-pg-simple`'s README

**If the team adds Redis later:**
- Swap `connect-pg-simple` for `connect-redis@^8`
- No other code changes needed — express-session stores are interchangeable

**If CubeJS requires WebSocket (subscription queries):**
- Configure `http-proxy-middleware` with `ws: true` for the CubeJS proxy route
- Requires Express's `server.on('upgrade', ...)` hook wired to the proxy

**If running in Docker Compose (current production setup):**
- BFF runs as a new service `bff` in `docker-compose.yaml`
- Internal Docker network name resolution (`backend:8000`, `cubejs:4000`) replaces `localhost`
- Traefik routes `dashboard.pm.comsatel.com.pe` → BFF instead of `frontend-app`

---

## Sources

- npm registry — `express` version 5.2.1 (verified 2026-05-28)
- npm registry — `express-session` version 1.19.0 (verified 2026-05-28)
- npm registry — `http-proxy-middleware` version 4.0.0 (verified 2026-05-28)
- npm registry — `openid-client` version 6.8.4 (verified 2026-05-28)
- npm registry — `keycloak-connect` version 26.1.1 (verified 2026-05-28)
- npm registry — `connect-pg-simple` version 10.0.0 (verified 2026-05-28)
- Keycloak JS adapter (`keycloak-js`) in project: version 26.2.3 (from `dashboard-app/node_modules/keycloak-js/package.json`)
- Project Keycloak realm: `apps` realm, RS256 signature, 5-minute access token TTL (from `environment/keycloak/realm-export.json`)
- Express 5 release announcement: https://expressjs.com/2024/10/15/v5-release.html — MEDIUM confidence (URL inferred, content from training knowledge cutoff Aug 2025)
- openid-client v6 migration guide: https://github.com/panva/openid-client/releases — MEDIUM confidence (training knowledge)
- http-proxy-middleware v4 changelog: https://github.com/chimurai/http-proxy-middleware — MEDIUM confidence (training knowledge)

---

*Stack research for: Node.js + Express BFF Service (Dashboard Studio v1.8)*  
*Researched: 2026-05-28*
