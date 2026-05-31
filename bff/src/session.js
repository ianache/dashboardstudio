'use strict';

import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';
import config from './config.js';

// Create Redis client
const redisClient = createClient({
  url: config.redis.url,
  password: config.redis.password,
});

// Prevent unhandled 'error' event from crashing the process on disconnect/reconnect
redisClient.on('error', (err) => console.error('[Redis] Client error:', err.message));

redisClient.connect().catch(console.error);

// Initialize store
const store = new RedisStore({
  client: redisClient,
  prefix: config.redis.prefix,
});

const sessionMiddleware = session({
  store,
  name: 'bff.sid',
  secret: config.sessionSecret,
  resave: false,
  saveUninitialized: false,
  proxy: true,
  cookie: {
    httpOnly: true,
    secure: config.cookieSecure,
    sameSite: 'lax',
    domain: config.cookieDomain,
    maxAge: 28800000, // 8 hours
  },
});

export { redisClient, sessionMiddleware };
