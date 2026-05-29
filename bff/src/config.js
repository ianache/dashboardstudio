'use strict';

import dotenv from 'dotenv';
dotenv.config({ override: true });

const required = (key) => {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required env var: ${key}`);
  }
  return value;
};

const config = {
  port: parseInt(process.env.BFF_PORT || '3001', 10),
  sessionSecret: required('BFF_SESSION_SECRET'),
  callbackUrl: process.env.BFF_CALLBACK_URL || 'http://localhost:3001/bff/auth/callback',
  keycloakUrl: required('BFF_KEYCLOAK_URL'),
  keycloakRealm: required('BFF_KEYCLOAK_REALM'),
  keycloakClientId: required('BFF_KEYCLOAK_CLIENT_ID'),
  keycloakClientSecret: required('BFF_KEYCLOAK_CLIENT_SECRET'),
  cubejsUrl: process.env.BFF_CUBEJS_URL || 'http://cubejs:4000',
  cubejsSecret: required('BFF_CUBEJS_SECRET'),
  backendUrl: process.env.BFF_BACKEND_URL || 'http://backend:8000',
  spaOrigins: (process.env.BFF_SPA_ORIGINS || 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173').split(','),
  cookieDomain: process.env.BFF_COOKIE_DOMAIN || undefined,
  cookieSecure: process.env.BFF_COOKIE_SECURE === 'true',
  redis: {
    url: process.env.BFF_REDIS_URL || 'redis://192.168.100.254:6379',
    password: process.env.BFF_REDIS_PASSWORD || 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81',
    prefix: process.env.BFF_REDIS_PREFIX || 'bff:sess:',
  },
  db: {
    host: process.env.BFF_POSTGRES_HOST,
    port: parseInt(process.env.BFF_POSTGRES_PORT || '5432', 10),
    database: process.env.BFF_POSTGRES_DB,
    user: process.env.BFF_POSTGRES_USER,
    password: process.env.BFF_POSTGRES_PASSWORD,
    schema: process.env.BFF_POSTGRES_SCHEMA || 'biportal',
  }
};

export default Object.freeze(config);
