# Research: Phase 35 - FastAPI Proxy + CORS Consolidation

## Goal
Route all FastAPI requests through the BFF at `/bff/api/*`, injecting the access token from the session, and consolidate CORS ownership in the BFF.

## Tech Stack
- **Express 5**: Already in use.
- **http-proxy-middleware v3**: For robust proxying.
- **FastAPI**: Backend service to be proxied.

## Key Findings

### 1. Proxy Setup with Token Injection
We can use `onProxyReq` to inject the `Authorization` header:
```javascript
import { createProxyMiddleware } from 'http-proxy-middleware';

app.use('/bff/api', createProxyMiddleware({
  target: config.backendUrl,
  changeOrigin: true,
  pathRewrite: {
    '^/bff/api': '/api', // Rewrite /bff/api/v1/health -> /api/v1/health
  },
  onProxyReq: (proxyReq, req, res) => {
    if (req.session?.tokens?.access_token) {
      proxyReq.setHeader('Authorization', `Bearer ${req.session.tokens.access_token}`);
    }
  },
}));
```

### 2. CORS Consolidation
The BFF must be the sole owner of CORS. 
- **BFF side**: Add `cors` middleware to Express.
- **FastAPI side**: Remove `CORSMiddleware` from `backend/app/main.py`.

### 3. Handling Unhandled Exceptions (FastAPI)
FastAPI has a custom exception handler that manually adds CORS headers. This must also be cleaned up to avoid duplicate or conflicting headers.

### 4. Express 5 & ESM
`http-proxy-middleware` v3 is ESM-only, which matches our BFF setup.

## Proposed Architecture

1.  **Proxy Module**: A new module `bff/src/proxy.js` to encapsulate proxy logic.
2.  **CORS Middleware**: Configure `cors` in `bff/src/index.js`.
3.  **Backend Cleanup**: Remove CORS-related code from FastAPI.

## Risks & Mitigations

- **Duplicate Headers**: If FastAPI still sends CORS headers, the browser might reject the response. We should use `onProxyRes` to strip any accidentally sent CORS headers from the backend.
- **Auth required for Proxy**: Proxy should only be accessible for authenticated users (except maybe some public routes if they exist). Use `requireAuth` middleware before the proxy.

## Success Criteria
1. `/bff/api/v1/health` returns response from FastAPI.
2. Request to FastAPI includes `Authorization: Bearer <token>`.
3. No `Access-Control-*` headers from FastAPI in the browser.
4. BFF handles all CORS correctly.
