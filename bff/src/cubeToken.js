'use strict';

import jwt from 'jsonwebtoken';
import config from './config.js';

/**
 * Signs a JWT for CubeJS authentication.
 * 
 * @param {Object} user - User object from Keycloak session
 * @returns {string} HS256 JWT
 */
export const signCubeToken = (user) => {
  if (!user || !user.sub) {
    throw new Error('Invalid user session for CubeJS token signing');
  }

  const payload = {
    sub: user.sub,
    name: user.name || user.preferred_username || user.sub,
    roles: user.realm_access?.roles || [],
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
  };

  return jwt.sign(payload, config.cubejsSecret, { algorithm: 'HS256' });
};
