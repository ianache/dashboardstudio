# Phase 45: BFF Integration - Research

**Researched:** 2024-05-31
**Domain:** Node.js, Express, http-proxy-middleware, FastAPI, SSE (Server-Sent Events)
**Confidence:** HIGH

## Summary

This phase focuses on integrating the `ai-analyst` service into the existing Backend-for-Frontend (BFF) architecture. The BFF acts as a security gate, validating sessions before forwarding requests to the AI service. The integration must support streaming responses via Server-Sent Events (SSE) and pass user context for personalization and auditing.

**Primary recommendation:** Implement a new proxy in `bff/src/proxy.js` using `http-proxy-middleware` v4, specifically configured for streaming (SSE) by disabling timeouts and ensuring headers like `X-User-ID` are injected from the validated session.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| http-proxy-middleware | ^4.0.0 | Request proxying | Standard in this project for BFF; v4 uses modern streams (httpxy). |
| Express | ^5.0.0 | Web Framework | Base for the BFF service. |
| FastAPI | ^0.135.0 | AI Service API | Framework used by `ai-analyst`. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| openid-client | ^6.8.4 | OIDC Auth | Used by BFF for Keycloak session management. |
| redis | ^4.6.13 | Session Store | Persistent session storage for BFF. |

## Architecture Patterns

### Recommended Project Structure
```
bff/src/
├── middleware/
│   └── auth.js       # Existing requireAuth and tokenRefresh
├── proxy.js          # Add aiProxy export here
└── index.js          # Mount /bff/ai to aiProxy
```

### Pattern 1: Session-Protected Proxy
**What:** Use the existing `requireAuth` middleware to protect the AI route and inject user context headers.
**When to use:** All requests to the AI service.

### Pattern 2: SSE-Optimized Proxy (HPM v4)
**What:** Configure the proxy to handle long-lived connections by setting `proxyTimeout` and `timeout` to `0`. Avoid response interceptors that buffer the body.
**Example:**
```javascript
export const aiProxy = createProxyMiddleware({
  target: config.aiServiceUrl,
  changeOrigin: true,
  proxyTimeout: 0,
  timeout: 0,
  pathRewrite: { '^/': '/' },
  on: {
    proxyReq: (proxyReq, req, res) => {
      if (req.session?.user) {
        proxyReq.setHeader('X-User-ID', req.session.user.sub);
        proxyReq.setHeader('X-User-Email', req.session.user.email);
      }
      fixRequestBody(proxyReq, req);
    }
  }
});
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Proxy Logic | Manual http.request | http-proxy-middleware | Handles stream piping, headers, and edge cases (HPM v4 uses httpxy). |
| Session Sync | Manual cookie parsing | express-session | Integrated with OIDC and Redis in the current stack. |

## Common Pitfalls

### Pitfall 1: Proxy Buffering (SSE Death)
**What goes wrong:** The proxy or middleware (like compression) buffers the AI response, so the UI receives nothing until the stream ends.
**How to avoid:** Ensure no `responseInterceptor` is used for the AI proxy. If `compression` middleware is present in `index.js`, exclude `/bff/ai/*` paths.

### Pitfall 2: Session Store Drain
**What goes wrong:** Rapid chat messages could trigger many session writes if not careful.
**How to avoid:** The existing `tokenRefresh` already handles concurrent refreshes efficiently.

## Code Examples

### AI Proxy Implementation (bff/src/proxy.js)
```javascript
// Add to bff/src/proxy.js
export const aiProxy = createProxyMiddleware({
  target: process.env.BFF_AI_URL || 'http://ai-analyst:8001',
  changeOrigin: true,
  proxyTimeout: 0, 
  timeout: 0,
  pathRewrite: {
    '^/': '/', // The /bff/ai prefix is stripped by Express
  },
  on: {
    proxyReq: (proxyReq, req, res) => {
      // Inject User Identity
      if (req.session?.user) {
        proxyReq.setHeader('X-User-ID', req.session.user.sub);
      }
      fixRequestBody(proxyReq, req);
    },
    error: (err, req, res) => {
      console.error('BFF Proxy Error (AI):', err.message);
      res.status(502).json({ error: 'AI service unreachable' });
    }
  }
});
```

### Route Mounting (bff/src/index.js)
```javascript
app.use('/bff/ai', requireAuth, tokenRefresh, aiProxy);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| http-proxy | httpxy (HPM v4) | 2024 | Better streaming support, native ESM. |
| sse-starlette | FastAPI Native SSE | 2025 (v0.135) | Standardized SSE response class in FastAPI. |

## Open Questions

1. **Wait for full response?**
   - What we know: The frontend needs SSE for a "typing" effect.
   - What's unclear: If the Traefik ingress (shown in docker-compose) has buffering enabled.
   - Recommendation: Check Traefik labels if streaming lags in staging.

## Sources

### Primary (HIGH confidence)
- `bff/src/proxy.js`: Existing proxy patterns for FastAPI/CubeJS.
- `bff/package.json`: Confirmed `http-proxy-middleware` v4 usage.
- `ai-analyst/app/main.py`: Confirmed `/chat` endpoint and `ChatRequest` schema.
- HPM v4 Docs: Verified SSE compatibility and timeout settings.
