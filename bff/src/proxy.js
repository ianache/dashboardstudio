'use strict';

import { createProxyMiddleware, fixRequestBody } from 'http-proxy-middleware';
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
        console.log('Access Token present (len: ' + req.session.tokens.access_token.length + ' chars)');
        proxyReq.setHeader('Authorization', 'Bearer ' + req.session.tokens.access_token);
      } else {
        console.log('WARNING: No access_token found in session!');
      }
      console.log('---------------------------');
      
      // Fix body-parser stream drain issue for proxied POST/PUT requests
      fixRequestBody(proxyReq, req);
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
      
      // Fix body-parser stream drain issue for CubeJS POST requests
      fixRequestBody(proxyReq, req);
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
      
      const urlPath = req.path || '';
      const isMeta = urlPath.endsWith('/meta') || req.url.endsWith('/meta') || req.originalUrl.endsWith('/meta');
      const isLoad = urlPath.includes('/load') || req.url.includes('/load') || req.originalUrl.includes('/load');

      if ((err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND' || err.code === 'ETIMEDOUT') && (isMeta || isLoad)) {
        console.log(`[BFF CUBEJS FALLBACK] Serving mock response for ${req.method} ${req.originalUrl}`);
        
        if (isMeta) {
          return res.json({
            cubes: [
              {
                name: 'fct_horasreportadas',
                title: 'Horas Reportadas',
                measures: [
                  { name: 'fct_horasreportadas.total_hours', title: 'Total Horas', type: 'number' },
                  { name: 'fct_horasreportadas.cost', title: 'Costo', type: 'number' }
                ],
                dimensions: [
                  { name: 'fct_horasreportadas.area', title: 'Área', type: 'string' },
                  { name: 'fct_horasreportadas.reg_date', title: 'Fecha Registro', type: 'time' },
                  { name: 'fct_horasreportadas.product', title: 'Producto', type: 'string' }
                ]
              },
              {
                name: 'Colaborador',
                title: 'Colaborador',
                measures: [],
                dimensions: [
                  { name: 'Colaborador.role', title: 'Rol', type: 'string' },
                  { name: 'Colaborador.name', title: 'Nombre', type: 'string' }
                ]
              }
            ]
          });
        }
        
        if (isLoad) {
          let queries = [];
          if (req.query && req.query.query) {
            try {
              const parsed = JSON.parse(req.query.query);
              queries = Array.isArray(parsed) ? parsed : [parsed];
            } catch (e) {
              console.error('[BFF CUBEJS FALLBACK] Failed to parse query:', e);
            }
          }
          
          const results = queries.map(q => {
            const measures = q.measures || [];
            const dimensions = q.dimensions || [];
            const limit = q.limit || 100;
            
            const data = [];
            const roles = ['Desarrollador', 'Diseñador', 'Project Manager', 'QA Analyst', 'Consultor'];
            const areas = ['Desarrollo', 'Diseño', 'Proyectos', 'Calidad', 'Consultoría'];
            const products = ['Plataforma Core', 'App Móvil', 'API Gateway', 'Dashboard BI', 'Portal Clientes'];
            
            for (let i = 0; i < Math.min(12, limit); i++) {
              const row = {};
              dimensions.forEach(dim => {
                if (dim === 'Colaborador.role') {
                  row[dim] = roles[i % roles.length];
                } else if (dim === 'Colaborador.name') {
                  row[dim] = `Colaborador ${i + 1}`;
                } else if (dim === 'fct_horasreportadas.area') {
                  row[dim] = areas[i % areas.length];
                } else if (dim === 'fct_horasreportadas.product') {
                  row[dim] = products[i % products.length];
                } else if (dim === 'fct_horasreportadas.reg_date') {
                  row[dim] = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
                } else {
                  row[dim] = `Valor ${i + 1}`;
                }
              });
              measures.forEach(meas => {
                if (meas === 'fct_horasreportadas.total_hours') {
                  row[meas] = Math.floor(Math.random() * 80) + 20;
                } else if (meas === 'fct_horasreportadas.cost') {
                  row[meas] = Math.floor(Math.random() * 2000) + 500;
                } else {
                  row[meas] = Math.floor(Math.random() * 100) + 10;
                }
              });
              data.push(row);
            }
            
            const measuresAnnotation = {};
            measures.forEach(m => {
              measuresAnnotation[m] = {
                title: m.split('.').pop().replace(/_/g, ' '),
                shortTitle: m.split('.').pop().replace(/_/g, ' '),
                type: 'number'
              };
            });
            
            const dimensionsAnnotation = {};
            dimensions.forEach(d => {
              dimensionsAnnotation[d] = {
                title: d.split('.').pop().replace(/_/g, ' '),
                shortTitle: d.split('.').pop().replace(/_/g, ' '),
                type: d.includes('date') ? 'time' : 'string'
              };
            });
            
            return {
              data: data,
              annotation: {
                measures: measuresAnnotation,
                dimensions: dimensionsAnnotation,
                segments: {},
                timeDimensions: {}
              }
            };
          });
          
          return res.json({ results });
        }
      }

      res.status(502).json({ error: 'CubeJS service unreachable' });
    }
  }
});

/**
 * Proxy for AI Analyst Service.
 * Routes: /bff/ai/* -> http://ai-analyst:8001/*
 * Injects X-User-ID and X-User-Email from session.
 * Supports SSE (Server-Sent Events) by disabling timeouts.
 */
export const aiProxy = createProxyMiddleware({
  target: config.aiServiceUrl,
  changeOrigin: true,
  proxyTimeout: 0, // Disable timeout for SSE
  timeout: 0,      // Disable timeout for SSE
  pathRewrite: {
    '^/': '/', // Route /bff/ai/foo -> ai-analyst:8001/foo (express mounts at /bff/ai)
  },
  on: {
    proxyReq: (proxyReq, req, res) => {
      if (req.session?.user) {
        if (req.session.user.sub) {
          proxyReq.setHeader('X-User-ID', req.session.user.sub);
        }
        if (req.session.user.email) {
          proxyReq.setHeader('X-User-Email', req.session.user.email);
        }
      }
      
      // Fix body-parser stream drain issue
      fixRequestBody(proxyReq, req);
    },
    proxyRes: (proxyRes, req, res) => {
      // Strip CORS headers from upstream
      delete proxyRes.headers['access-control-allow-origin'];
      delete proxyRes.headers['access-control-allow-credentials'];
      delete proxyRes.headers['access-control-allow-methods'];
      delete proxyRes.headers['access-control-allow-headers'];
      delete proxyRes.headers['access-control-expose-headers'];
    },
    error: (err, req, res) => {
      console.error('BFF Proxy Error (AI Service):', err.message);
      res.status(502).json({ error: 'AI service unreachable' });
    }
  }
});
