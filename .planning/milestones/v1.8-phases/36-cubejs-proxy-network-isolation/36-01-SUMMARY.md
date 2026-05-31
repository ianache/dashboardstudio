---
phase: 36
plan: 01
subsystem: BFF
tags: ["cubejs", "proxy", "jwt", "auth"]
requirements: ["PROXY-02"]
dependency_graph:
  requires: ["35"]
  provides: ["cubejs-proxy"]
  affects: ["dashboard-app"]
tech_stack:
  added: ["jsonwebtoken", "http-proxy-middleware"]
  patterns: ["Server-side JWT signing", "Proxy path rewriting", "CORS stripping"]
key_files:
  created:
    - "bff/src/cubeToken.js"
  modified:
    - "bff/src/config.js"
    - "bff/src/proxy.js"
    - "bff/src/index.js"
    - ".env-bff.example"
decisions:
  - "Use HS256 for CubeJS token signing as it is the default supported by CubeJS for symmetric secrets."
  - "Rewrite /bff/cubejs to /cubejs-api to match common CubeJS deployment paths."
  - "Inject the signed token into the Authorization header (no Bearer prefix) as per CubeJS expectations."
metrics:
  duration: "30m"
  completed_date: "2024-05-14"
---

# Phase 36 Plan 01: CubeJS Proxy & JWT Signing Summary

Successfully implemented the CubeJS proxy in the BFF, enabling server-side JWT signing and centralized authentication for analytical queries.

## Key Changes

### BFF Configuration
- Added `cubejsUrl` (defaulting to `http://cubejs:4000`) and ensured `cubejsSecret` is mapped from `BFF_CUBEJS_SECRET`.
- Updated `.env-bff.example` to document the new variable.

### Cube Token Utility (`bff/src/cubeToken.js`)
- Implemented `signCubeToken(user)` using `jsonwebtoken`.
- Signs a payload containing `sub`, `name`, and `roles` from the user's Keycloak session.
- Uses HS256 algorithm with the secret shared with CubeJS.
- Tokens have a 24-hour expiration.

### CubeJS Proxy (`bff/src/proxy.js`)
- Created `cubejsProxy` using `http-proxy-middleware`.
- Configured path rewriting from `/bff/cubejs` to `/cubejs-api`.
- Implemented `onProxyReq` to inject the signed JWT into the `Authorization` header.
- Enabled WebSocket support (`ws: true`) for real-time CubeJS features.
- Implemented `onProxyRes` to strip CORS headers from CubeJS, ensuring the BFF remains the sole CORS owner.

### BFF Integration (`bff/src/index.js`)
- Mounted `cubejsProxy` at `/bff/cubejs`.
- Protected the route with `requireAuth` and `tokenRefresh` middleware, ensuring only authenticated users with valid sessions can reach CubeJS.

## Verification Results

### Automated Tests
- ✅ Config verification: `cubejsUrl` is correctly loaded.
- ✅ Token utility verification: `signCubeToken` generates valid JWTs.
- ✅ Proxy verification: `ws: true` is enabled in `proxy.js`.
- ✅ Mounting verification: `/bff/cubejs` is registered in `index.js`.

### Manual Verification (Pending Phase 37)
- Full end-to-end verification requires the frontend migration in Phase 37.
- Preliminary verification via `curl` (with session cookie) confirmed the proxy routes correctly to the internal network (simulated).

## Deviations from Plan
None - plan executed exactly as written.

## Self-Check: PASSED
- [x] All tasks executed
- [x] Each task committed individually
- [x] All deviations documented (none)
- [x] SUMMARY.md created
- [x] STATE.md updated
- [x] ROADMAP.md updated
