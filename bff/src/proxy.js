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
  ws: true,
  pathRewrite: {
    '^/': '/api/', // Prepends '/api' since '/bff/api' is already stripped by Express mount
  },
  on: {
    proxyReq: (proxyReq, req, res) => {
      console.log(`\n--- [BFF PROXY FASTAPI] ---`);
      console.log(`Request: ${req.method} ${req.url} -> ${config.backendUrl}${proxyReq.path}`);
      console.log(`Session ID: ${req.sessionID}`);
      console.log(`Has session: ${!!req.session}`);
      console.log(`Has user in session: ${!!req.session?.user}`);
      console.log(`Has tokens in session: ${!!req.session?.tokens}`);
      
      if (req.session?.tokens?.access_token) {
        console.log(`Access Token present (len: ${req.session.tokens.access_token.length} chars)`);
        proxyReq.setHeader('Authorization', `Bearer ${req.session.tokens.access_token}`);
      } else {
        console.log(`WARNING: No access_token found in session!`);
      }
      console.log(`---------------------------`);
    },
    proxyRes: (proxyRes, req, res) => {
      // Strip CORS headers from backend to avoid duplication/conflict
      // BFF is the sole owner of CORS
      delete proxyRes.headers['access-control-allow-origin'];
      delete proxyRes.headers['access-control-allow-credentials'];
      delete proxyRes.headers['access-control-allow-methods'];
      delete proxyRes.headers['access-control-allow-headers'];
      delete proxyRes.headers['access-control-expose-headers'];
    },
    error: (err, req, res) => {
      console.error('BFF Proxy Error (FastAPI):', err.message);
      res.status(502).json({ error: 'Backend service unreachable' });
    }
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
    '^/': '/cubejs-api/', // Prepends '/cubejs-api' since '/bff/cubejs' is already stripped by Express mount
  },
  on: {
    proxyReq: (proxyReq, req, res) => {
      if (req.session?.user) {
        try {
          const token = signCubeToken(req.session.user);
          proxyReq.setHeader('Authorization', token);
        } catch (err) {
          console.error('CubeJS Token Signing Error:', err.message);
        }
      }
    },
    proxyRes: (proxyRes, req, res) => {
      // Strip CORS headers from CubeJS
      delete proxyRes.headers['access-control-allow-origin'];
      delete proxyRes.headers['access-control-allow-credentials'];
      delete proxyRes.headers['access-control-allow-methods'];
      delete proxyRes.headers['access-control-allow-headers'];
      delete proxyRes.headers['access-control-expose-headers'];
    },
    error: (err, req, res) => {
      console.error('BFF Proxy Error (CubeJS):', err.message);
      res.status(502).json({ error: 'CubeJS service unreachable' });
    }
  }
});
