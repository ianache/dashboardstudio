# Research: Phase 37 - Frontend Migration

## Goal
Remove `keycloak-js` from the Vue 3 SPA and transition to a BFF-driven authentication and API proxy model.

## Current State Analysis

### 1. `main.js`
- Initializes `keycloak-js`.
- Manages token persistence in `sessionStorage` (manual sync).
- Sets up `onTokenExpired` callback to call `updateToken`.
- Only mounts the Vue app AFTER successful Keycloak initialization.

### 2. `stores/auth.js`
- Depends on the `keycloak` instance.
- `isAuthenticated` is derived from `user` object presence.
- `logout()` calls `keycloak.logout()`.
- `token` getter returns the raw JWT.

### 3. `services/api.js`
- `getAuthHeaders()` extracts the token from `keycloak-js`.
- Calls `keycloak.updateToken()` if expired.
- Hardcoded `API_BASE_URL` (usually port 8000).

### 4. `stores/cubejs.js`
- Uses `cubejs-client` with a token and `apiUrl`.
- `apiUrl` is usually port 4000.

## Migration Strategy

### 1. BFF Base URL
All requests (API and CubeJS) will now route through the BFF.
In development, the SPA is usually on `localhost:3000` and the BFF on `localhost:3001`.
The BFF becomes the sole endpoint.

### 2. Auth Store Refactor
- Remove all `keycloak-js` imports.
- Add `initialize()` action:
  - Calls `GET /bff/auth/me`.
  - On 200: Populates `user`.
  - On 401: Redirects to `window.location.href = '/bff/auth/login'`.
- `logout()`: Redirects to `window.location.href = '/bff/auth/logout'`.
- Remove `token` and `getToken()`.

### 3. API Service Refactor
- Remove `getAuthHeaders()`.
- Set `API_BASE_URL` to `/bff/api` (relative to the BFF if hosted together, or absolute to BFF).
- In `fetch()`, add `credentials: 'include'` to ensure the session cookie is sent.

### 4. CubeJS Store Refactor
- Set `apiUrl` to `/bff/cubejs`.
- Use a dummy token string (BFF will replace the header).
- Ensure `credentials: 'include'` is handled (usually via transport options in `cubejs-client`).

### 5. `main.js` Refactor
- Remove all Keycloak initialization logic.
- Remove `sessionStorage` token sync.
- Initialize Pinia first, then call `authStore.initialize()`.
- Mount the app.

## Risks & Mitigations

- **Infinite Redirect Loops**: If `/bff/auth/me` returns 401 and the app redirects to `/bff/auth/login`, but login fails or redirects back to a 401, we get a loop. The BFF must ensure `login` establishes a session.
- **WebSocket Compatibility**: CubeJS WebSockets must work through the BFF proxy. Verified in Phase 36 research.
- **CORS**: Verified in Phase 35. BFF is the sole owner.

## Success Criteria
1. `keycloak-js` is removed from `package.json`.
2. No mention of `keycloak-js` or tokens in the codebase.
3. App works end-to-end (Auth -> API -> Charts).
4. No tokens are visible in the browser's Network tab or Storage.
