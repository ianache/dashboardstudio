---
phase: 34
plan: 03
subsystem: bff
tags: ["bff", "auth", "middleware", "token-refresh"]
dependency_graph:
  requires: ["34-02"]
  provides: ["AUTH-02"]
  affects: ["bff"]
tech_stack:
  added: []
  patterns: ["Token Refresh Middleware", "Concurrent Refresh Coordination"]
key_files:
  created: ["bff/src/middleware/auth.js"]
  modified: ["bff/src/routes/auth.js"]
  deleted: []
decisions:
  - "activeRefreshes Map coordinates concurrent token refreshes for the same session, preventing multiple simultaneous refresh calls."
  - "Transient IdP failures (5xx/network) do not destroy the session if the token is still valid — avoids unnecessary logouts during Keycloak downtime."
  - "30-second buffer before token expiry triggers a proactive refresh."
metrics:
  duration: "verified post-hoc"
  completed_date: "2026-05-30"
---

# Phase 34 Plan 03: Token Management & Refresh Summary

Implemented `requireAuth` and `tokenRefresh` middleware for token lifecycle management in the BFF.

## Key Changes

### 1. `requireAuth` middleware
- Checks `req.session.user`; returns 401 if absent.
- Used as guard on `/bff/api` and `/bff/cubejs` proxy routes.

### 2. `tokenRefresh` middleware
- Checks `tokens.expires_at` against current time with a 30-second buffer.
- If token is expiring: calls `oidc.refreshTokenGrant()` and updates `req.session.tokens` with the new plain-serializable token set.
- Updates `req.session.user.name` from refreshed ID token claims if available.
- Calls `req.session.save()` explicitly after refresh to ensure Redis is updated before forwarding the request.

### 3. Concurrent refresh coordination (`activeRefreshes` Map)
- If two requests arrive simultaneously for the same expiring session, only the first creates the refresh Promise; subsequent ones await the same Promise.
- Prevents duplicate refresh calls and potential token invalidation from race conditions.

### 4. Transient failure tolerance
- Distinguishes OAuth2 errors (`invalid_grant`, `invalid_client`) from transient failures (network/5xx).
- On transient failure with a still-valid token: logs a warning and proceeds without destroying the session.
- On definitive OAuth2 failure: destroys session, clears cookie, returns 401.

### 5. Applied to `/bff/auth/me`
- `tokenRefresh` is applied as route middleware on `GET /me`.

## Deviations from Plan

Enhanced beyond the plan spec: added concurrent refresh coordination via `activeRefreshes` Map and transient failure tolerance to avoid unnecessary logouts during Keycloak unavailability.

## Verification Results

- `requireAuth` blocks unauthenticated requests to proxied routes with 401.
- `tokenRefresh` proactively refreshes tokens with <30s remaining.
- Concurrent refresh handled: only one `refreshTokenGrant` call per session per cycle.
- Transient Keycloak failures do not log out users with valid tokens.

## Self-Check: PASSED
- [x] requireAuth middleware implemented
- [x] tokenRefresh middleware with 30s buffer
- [x] oidc.refreshTokenGrant() used for refresh
- [x] Session saved after refresh
- [x] /me route uses tokenRefresh
- [x] Concurrent refresh coordination implemented
