# Context: Phase 37 - Frontend Migration

## Phase Goal
Transition the Vue 3 SPA to a BFF-driven architecture. Remove `keycloak-js`, migrate auth state management to use the BFF `/auth/me` endpoint, and route all API/CubeJS calls through the BFF proxies with `credentials: 'include'`.

## Requirements
- **FE-01**: Remove `keycloak-js` library and all its imports.
- **FE-02**: Migrate auth store to use `/bff/auth/me`.
- **FE-03**: Route all API calls through `/bff/api` with session cookies.
- **FE-04**: Route CubeJS calls through `/bff/cubejs` with signed JWTs (managed by BFF).

## Success Criteria
1.  **Zero Tokens**: No JWTs stored in `localStorage`, `sessionStorage`, or visible in the Network tab (replaced by HttpOnly cookie).
2.  **BFF Discovery**: App automatically redirects to `/bff/auth/login` if no session is active.
3.  **End-to-End**: All existing features (Dashboards, Integrations, Models) work correctly.
4.  **No `keycloak-js`**: Library is uninstalled from `package.json`.

## Decisions
- **BFF URL**: The frontend will use relative paths `/bff/*` where possible, or a configurable `VITE_BFF_URL`.
- **Auth Initialization**: `authStore.initialize()` will be called in `main.js` before mounting the app to avoid flash of unauthenticated content.
- **CubeJS Dummy Token**: Use `dummy-token` for `cubejs-client` initialization to satisfy the constructor; the BFF will strip it and inject the real one.

## Risks
- **Session Timeout Handling**: Frontend must handle 401 responses from the proxy and redirect to login.
- **Environment Config**: Deployment URLs for BFF must be correctly set.
