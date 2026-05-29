'use strict';

import express from 'express';
import * as oidc from 'openid-client';
import config from '../config.js';
import { getOIDCConfig } from '../oidc.js';
import { tokenRefresh } from '../middleware/auth.js';

const router = express.Router();

/**
 * Initiates the OIDC Login flow.
 */
router.get('/login', async (req, res) => {
  try {
    const oidcConfig = getOIDCConfig();
    const code_verifier = oidc.randomPKCECodeVerifier();
    const code_challenge = await oidc.calculatePKCECodeChallenge(code_verifier);
    const state = oidc.randomState();

    req.session.code_verifier = code_verifier;
    req.session.state = state;

    const parameters = {
      redirect_uri: config.callbackUrl,
      scope: 'openid profile email',
      code_challenge,
      code_challenge_method: 'S256',
      state,
    };

    const url = oidc.buildAuthorizationUrl(oidcConfig, parameters);

    // Explicitly save session before redirect so the code_verifier/state
    // are committed to Redis before Keycloak redirects back.
    req.session.save((err) => {
      if (err) {
        console.error('Login session save error:', err);
        return res.status(500).json({ error: 'Failed to initiate login' });
      }
      res.redirect(url.href);
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Failed to initiate login' });
  }
});

/**
 * Handles the OIDC callback from Keycloak.
 */
router.get('/callback', async (req, res) => {
  try {
    const oidcConfig = getOIDCConfig();
    
    console.log('BFF Callback: Received request');
    console.log('BFF Session ID:', req.sessionID);
    console.log('BFF Session code_verifier:', req.session.code_verifier ? 'Present' : 'MISSING');
    console.log('BFF Session state:', req.session.state ? 'Present' : 'MISSING');

    const code_verifier = req.session.code_verifier;
    const expectedState = req.session.state;

    if (!code_verifier) {
      console.error('BFF Callback Error: Missing code_verifier in session');
      return res.status(400).send('Authentication state lost. Please try logging in again.');
    }

    // Build currentUrl directly from the configured callbackUrl so the
    // redirect_uri in the token exchange always matches the authorization request.
    const qs = req.originalUrl.includes('?') ? req.originalUrl.split('?')[1] : '';
    const currentUrl = new URL(`${config.callbackUrl}?${qs}`);

    console.log('BFF Callback currentUrl:', currentUrl.href);

    const tokens = await oidc.authorizationCodeGrant(
      oidcConfig,
      currentUrl,
      {
        pkceCodeVerifier: code_verifier,
        expectedState,
      }
    );

    console.log('BFF Callback: Token exchange successful');

    // claims() returns undefined when the server didn't issue an id_token.
    // Fall back to decoding the access token in that case.
    const claims = tokens.claims() ?? decodeJwt(tokens.access_token) ?? {};

    const userRoles = extractRoles(claims, tokens.access_token);

    // Store only plain-serializable token fields (avoid storing class instances in Redis).
    req.session.tokens = {
      access_token: tokens.access_token,
      token_type: tokens.token_type,
      id_token: tokens.id_token,
      refresh_token: tokens.refresh_token,
      expires_in: tokens.expires_in,
      expires_at: tokens.expires_in
        ? Math.floor(Date.now() / 1000) + tokens.expires_in
        : undefined,
    };
    req.session.user = {
      sub: claims.sub,
      email: claims.email,
      name: claims.name || claims.preferred_username,
      roles: userRoles,
      realm_access: {
        roles: userRoles,
      },
    };

    // Cleanup PKCE state
    delete req.session.code_verifier;
    delete req.session.state;

    // Save session explicitly before redirect
    req.session.save((err) => {
      if (err) {
        console.error('Session save error:', err);
        return res.status(500).send('Internal server error');
      }
      // Redirect back to frontend
      const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3000';
      res.redirect(frontendUrl);
    });
  } catch (error) {
    console.error('Callback error:', error);
    res.status(500).send(`Authentication failed: ${error.message}`);
  }
});

/**
 * Returns the currently authenticated user's profile.
 */
router.get('/me', tokenRefresh, (req, res) => {
  if (!req.session.user) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  res.json(req.session.user);
});

/**
 * Handles logout by destroying the local session and redirecting to Keycloak logout.
 */
router.get('/logout', (req, res) => {
  const oidcConfig = getOIDCConfig();
  const idToken = req.session.tokens?.id_token;

  req.session.destroy((err) => {
    if (err) {
      console.error('Logout error during session destroy:', err);
    }
    
    res.clearCookie('bff.sid');

    if (idToken) {
      const logoutUrl = oidc.buildEndSessionUrl(oidcConfig, {
        id_token_hint: idToken,
        post_logout_redirect_uri: process.env.FRONTEND_URL || 'http://localhost:3000'
      });
      res.redirect(logoutUrl.href);
    } else {
      res.redirect('/');
    }
  });
});

/**
 * Helper to decode a JWT payload (base64url format).
 */
function decodeJwt(token) {
  if (!token) return null;
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      Buffer.from(base64, 'base64')
        .toString()
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error('Failed to decode JWT:', e);
    return null;
  }
}

/**
 * Helper to extract Keycloak roles from token claims and access token.
 */
function extractRoles(claims, accessToken) {
  const roles = new Set();
  
  // Realm roles from ID Token
  if (claims?.realm_access?.roles) {
    claims.realm_access.roles.forEach(role => roles.add(role));
  }
  
  // Client roles from ID Token (for this specific client)
  const clientRoles = claims?.resource_access?.[config.keycloakClientId]?.roles;
  if (clientRoles) {
    clientRoles.forEach(role => roles.add(role));
  }

  // Extract roles from Access Token (Keycloak puts realm/client roles in access token by default)
  const decodedAccess = decodeJwt(accessToken);
  if (decodedAccess) {
    if (decodedAccess.realm_access?.roles) {
      decodedAccess.realm_access.roles.forEach(role => roles.add(role));
    }
    const clientRolesAccess = decodedAccess.resource_access?.[config.keycloakClientId]?.roles;
    if (clientRolesAccess) {
      clientRolesAccess.forEach(role => roles.add(role));
    }
  }
  
  return Array.from(roles);
}

export default router;
