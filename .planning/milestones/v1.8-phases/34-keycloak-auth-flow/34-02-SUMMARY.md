---
phase: 34
plan: 02
subsystem: bff
tags: ["bff", "auth", "oidc", "keycloak", "pkce"]
dependency_graph:
  requires: ["34-01"]
  provides: ["AUTH-01"]
  affects: ["bff"]
tech_stack:
  added: ["openid-client"]
  patterns: ["PKCE OIDC Flow", "Server-side Session Auth"]
key_files:
  created: ["bff/src/routes/auth.js"]
  modified: ["bff/src/index.js"]
  deleted: []
decisions:
  - "Explicit req.session.save() before redirects to ensure PKCE state is committed to Redis before Keycloak redirects back."
  - "Falls back to decoding the access token when Keycloak does not issue an id_token (claims() returns undefined)."
  - "extractRoles() reads from both realm_access and resource_access in ID token and access token to cover all Keycloak configurations."
metrics:
  duration: "verified post-hoc"
  completed_date: "2026-05-30"
---

# Phase 34 Plan 02: Auth Routes Summary

Implemented the core OIDC authentication routes in the BFF: login, callback, me, and logout.

## Key Changes

### 1. `GET /bff/auth/login`
- Generates PKCE `code_verifier` and `code_challenge` via `openid-client`.
- Stores verifier and `state` in session before redirect.
- Calls `req.session.save()` explicitly before redirecting to Keycloak to avoid race conditions with Redis.

### 2. `GET /bff/auth/callback`
- Reconstructs `currentUrl` from the configured `callbackUrl` (not `req.url`) to ensure the `redirect_uri` always matches the authorization request.
- Exchanges authorization code for tokens via `oidc.authorizationCodeGrant()` with PKCE verifier and expected state.
- Stores only plain-serializable token fields in `req.session.tokens` (avoids storing class instances in Redis).
- Cleans up `code_verifier` and `state` from session after successful exchange.
- Saves session explicitly before redirecting to frontend.

### 3. `GET /bff/auth/me`
- Protected by `tokenRefresh` middleware (auto-refreshes before expiry).
- Returns `req.session.user` (sub, email, name, roles).
- Returns 401 if no active session.

### 4. `GET /bff/auth/logout`
- Destroys BFF session.
- Clears `bff.sid` cookie.
- Redirects to Keycloak `end_session_endpoint` with `id_token_hint` if available, otherwise falls back to `/`.

### 5. `bff/src/index.js`
- Auth router mounted at `/bff/auth`.

## Deviations from Plan

None — all routes implemented as specified. Added `decodeJwt()` helper and `extractRoles()` helper to handle Keycloak role extraction from both ID token and access token.

## Verification Results

- `GET /bff/auth/login` → redirects to Keycloak authorization endpoint with PKCE params.
- `GET /bff/auth/callback` → exchanges code, stores tokens in session, redirects to frontend.
- `GET /bff/auth/me` → returns user profile from session, 401 when unauthenticated.
- `GET /bff/auth/logout` → destroys session, redirects to Keycloak end-session URL.

## Self-Check: PASSED
- [x] /auth/login implemented with PKCE
- [x] /auth/callback implements token exchange
- [x] /auth/me returns session user
- [x] /auth/logout destroys session and redirects to Keycloak
- [x] authRouter mounted at /bff/auth in index.js
