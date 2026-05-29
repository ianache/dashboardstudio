'use strict';

import config from './config.js';
import express from 'express';
import cors from 'cors';
import { sessionMiddleware } from './session.js';
import healthRouter from './routes/health.js';
import authRouter from './routes/auth.js';
import { fastapiProxy, cubejsProxy } from './proxy.js';
import { requireAuth, tokenRefresh } from './middleware/auth.js';
import { initOIDC } from './oidc.js';

const app = express();

console.log('--- BFF CONFIG DIAGNOSTICS ---');
console.log('Active BFF Client ID:', config.keycloakClientId);
console.log('Active BFF Keycloak URL:', config.keycloakUrl);
console.log('Active BFF Callback URL:', config.callbackUrl);
console.log('Active BFF Port:', config.port);
console.log('------------------------------');

// CORS configuration - BFF is the sole owner
app.use(cors({
  origin: config.spaOrigins,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept'],
}));

// Trust proxy MUST come before session middleware
app.set('trust proxy', 1);

app.use(express.json());
app.use(sessionMiddleware);

// Mount routes
app.use('/bff', healthRouter);
app.use('/bff/auth', authRouter);

// Proxy routes (protected)
app.use('/bff/api', requireAuth, tokenRefresh, fastapiProxy);
app.use('/bff/cubejs', requireAuth, tokenRefresh, cubejsProxy);

// Initialize OIDC and start server
async function startServer() {
  try {
    // Phase 34: Initialize OIDC Discovery
    await initOIDC();

    const server = app.listen(config.port, () => {
      console.log(`BFF listening on :${config.port}`);
    });

    // Handle WebSocket upgrades for proxies
    server.on('upgrade', (req, socket, head) => {
      console.log(`[BFF WS Upgrade] Original URL: ${req.url}`);
      if (req.url.startsWith('/bff/api')) {
        req.url = req.url.replace('/bff/api', '');
        console.log(`[BFF WS Upgrade] Rewrote to FastAPI: ${req.url}`);
        fastapiProxy.upgrade(req, socket, head);
      } else if (req.url.startsWith('/bff/cubejs')) {
        req.url = req.url.replace('/bff/cubejs', '');
        console.log(`[BFF WS Upgrade] Rewrote to CubeJS: ${req.url}`);
        cubejsProxy.upgrade(req, socket, head);
      }
    });
  } catch (error) {
    console.error('BFF failed to start:', error);
    process.exit(1);
  }
}

startServer();

export default app;
