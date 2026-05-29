# Research: Phase 36 - CubeJS Proxy + Network Isolation

## Goal
Proxy CubeJS queries through the BFF, sign tokens server-side using user context, and isolate backend services from public access.

## Tech Stack
- **Express 5**: BFF service.
- **http-proxy-middleware v3**: For proxying.
- **jsonwebtoken**: For HS256 JWT signing.
- **CubeJS**: Analytical API to be proxied and isolated.
- **Docker Compose**: For network configuration.

## Key Findings

### 1. CubeJS JWT Signing
CubeJS expects an HS256 JWT signed with `CUBEJS_API_SECRET`.
The payload can include a `securityContext` for row-level security.
```javascript
import jwt from 'jsonwebtoken';

const token = jwt.sign(
  {
    sub: user.sub,
    name: user.name,
    roles: user.roles,
    // Add any other security context fields needed by Cube schemas
  },
  config.cubejsSecret,
  { expiresIn: '1h' }
);
```

### 2. Proxying CubeJS
CubeJS requests should be proxied from `/bff/cubejs/*` to `http://cubejs:4000/*`.
The path rewrite should handle `/bff/cubejs/v1/load` -> `/cubejs-api/v1/load`.
Wait, CubeJS default path is often `/cubejs-api/v1`. Let's verify the existing configuration.
Looking at `environment/docker-compose.yml`, it doesn't specify a base path, so it's likely default.

### 3. Network Isolation
To isolate services:
- **Remove `ports`**: Backend and CubeJS should not expose ports to the host.
- **Remove Traefik labels**: Prevent Traefik from routing public traffic to them.
- **Shared Network**: Ensure BFF, Backend, and CubeJS are on the same internal Docker network.

### 4. WebSocket Support
CubeJS can use WebSockets for real-time updates. `http-proxy-middleware` supports WebSocket proxying:
```javascript
const proxy = createProxyMiddleware({
  target: config.cubejsUrl,
  ws: true,
  // ...
});
```

## Proposed Architecture

1.  **Cube Token Utility**: `bff/src/cubeToken.js` to handle JWT generation.
2.  **Cube Proxy**: In `bff/src/proxy.js`, add `cubejsProxy`.
3.  **BFF Integration**: Mount `cubejsProxy` at `/bff/cubejs`.
4.  **Docker Config**: Update `docker-compose.yaml` (and/or `environment/docker-compose.yml`) to remove public exposure for `backend` and `cubejs`.

## Risks & Mitigations

- **Token Expiry**: User session tokens (Keycloak) might expire while CubeJS tokens are still valid, or vice versa. BFF should generate a fresh CubeJS token per request (or per session with short TTL).
- **Network Connectivity**: Ensure internal DNS (service names) works correctly within Docker.
- **CORS**: CubeJS might have its own CORS settings. BFF must strip them as it did for FastAPI.

## Success Criteria
1. CubeJS queries work via `/bff/cubejs`.
2. CubeJS receives a JWT with user roles/sub.
3. Backend and CubeJS ports are closed to the host machine.
4. Traefik only routes to BFF and Frontend.
