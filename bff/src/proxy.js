'use strict';

import { createProxyMiddleware } from 'http-proxy-middleware';
import config from './config.js';
import { signCubeToken } from './cubeToken.js';

/**
 * Proxy for FastAPI backend.
 * Routes: /bff/api/* -> http://backend:8000/api/*
 * Injects Authorization: Bearer <token> from session.
 * Strips CORS headers from backend response.
 */
export const fastapiProxy = createProxyMiddleware({
  target: config.backendUrl,
  changeOrigin: true,
  pathRewrite: {
    '^/bff/api': '/api', // Rewrite /bff/api/v1/health -> /api/v1/health
  },
  onProxyReq: (proxyReq, req, res) => {
    // Inject Bearer token if present in session
    if (req.session?.tokens?.access_token) {
      proxyReq.setHeader('Authorization', `Bearer ${req.session.tokens.access_token}`);
    }
    
    // Log proxying for debugging
    // console.log(`BFF Proxy: ${req.method} ${req.url} -> ${config.backendUrl}${proxyReq.path}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    // Strip CORS headers from backend to avoid duplication/conflict
    // BFF is the sole owner of CORS
    delete proxyRes.headers['access-control-allow-origin'];
    delete proxyRes.headers['access-control-allow-credentials'];
    delete proxyRes.headers['access-control-allow-methods'];
    delete proxyRes.headers['access-control-allow-headers'];
    delete proxyRes.headers['access-control-expose-headers'];
  },
  onError: (err, req, res) => {
    console.error('BFF Proxy Error (FastAPI):', err.message);
    res.status(502).json({ error: 'Backend service unreachable' });
  }
});

/**
 * Proxy for CubeJS.
 * Routes: /bff/cubejs/* -> http://cubejs:4000/cubejs-api/*
 * Injects signed JWT from session user context.
 * Supports WebSockets.
 */
export const cubejsProxy = createProxyMiddleware({
  target: config.cubejsUrl,
  changeOrigin: true,
  ws: true,
  pathRewrite: {
    '^/bff/cubejs': '/cubejs-api',
  },
  onProxyReq: (proxyReq, req, res) => {
    if (req.session?.user) {
      try {
        const token = signCubeToken(req.session.user);
        proxyReq.setHeader('Authorization', token);
      } catch (err) {
        console.error('CubeJS Token Signing Error:', err.message);
      }
    }
  },
  onProxyRes: (proxyRes, req, res) => {
    // Strip CORS headers from CubeJS
    delete proxyRes.headers['access-control-allow-origin'];
    delete proxyRes.headers['access-control-allow-credentials'];
    delete proxyRes.headers['access-control-allow-methods'];
    delete proxyRes.headers['access-control-allow-headers'];
    delete proxyRes.headers['access-control-expose-headers'];
  },
  onError: (err, req, res) => {
    console.error('BFF Proxy Error (CubeJS):', err.message);
    res.status(502).json({ error: 'CubeJS service unreachable' });
  }
});
