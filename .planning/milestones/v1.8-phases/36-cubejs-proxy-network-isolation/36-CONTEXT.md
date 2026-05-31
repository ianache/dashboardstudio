# Context: Phase 36 - CubeJS Proxy + Network Isolation

## Decisions
- **HS256 Signing**: CubeJS will use HS256 symmetric signing with `CUBEJS_API_SECRET`.
- **Security Context**: The JWT will include `sub`, `name`, and `roles` to enable future row-level security in Cube schemas.
- **WebSocket Proxy**: The proxy will support WebSockets (ws: true) to ensure real-time charts continue working.
- **One-Way Isolation**: Isolation happens after the proxy is verified to ensure no downtime during transition.

## Deferred Ideas
- **RS256 Signing**: Asymmetric signing is deferred until a broader security audit.
- **Multiple Cube Instances**: Proxying multiple Cube instances is not required for the current milestone.

## Risks
- **CubeJS Pathing**: If CubeJS is configured with a custom prefix, the proxy rewrite must match.
- **Network DNS**: Internal service names must resolve correctly in Docker networks.

## Requirements Mapping
- **PROXY-02**: Implemented in 36-01-PLAN.
- **BE-02**: Implemented in 36-02-PLAN.
