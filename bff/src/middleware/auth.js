'use strict';

import * as oidc from 'openid-client';
import { getOIDCConfig } from '../oidc.js';

/**
 * Middleware that requires an active session.
 */
export function requireAuth(req, res, next) {
  if (!req.session.user) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  next();
}

// Map to coordinate concurrent token refreshes for the same session ID
const activeRefreshes = new Map();

/**
 * Middleware that checks if tokens are expired and refreshes them if necessary.
 * This should be applied BEFORE any route that needs to proxy requests with a token.
 */
export async function tokenRefresh(req, res, next) {
  if (!req.session.tokens || !req.session.tokens.refresh_token) {
    return next();
  }

  const { tokens } = req.session;
  
  // openid-client v6 tokens have expires_at (seconds since epoch)
  const expiresAt = tokens.expires_at;
  const now = Math.floor(Date.now() / 1000);
  const buffer = 30; // 30 seconds buffer

  if (expiresAt && (expiresAt - now) < buffer) {
    const sessionId = req.sessionID;
    
    // Check if there's already an active refresh promise for this session
    let refreshPromise = activeRefreshes.get(sessionId);
    const isInitiator = !refreshPromise;
    
    if (isInitiator) {
      console.log(`BFF [${sessionId}]: Access token expiring soon, initiating refresh...`);
      const oidcConfig = getOIDCConfig();
      refreshPromise = oidc.refreshTokenGrant(
        oidcConfig,
        tokens.refresh_token
      );
      activeRefreshes.set(sessionId, refreshPromise);
    } else {
      console.log(`BFF [${sessionId}]: Access token expiring soon, waiting for existing refresh to complete...`);
    }

    try {
      const refreshedTokens = await refreshPromise;
      
      // Store plain-serializable token fields (same shape as callback handler)
      req.session.tokens = {
        access_token: refreshedTokens.access_token,
        token_type: refreshedTokens.token_type,
        id_token: refreshedTokens.id_token,
        refresh_token: refreshedTokens.refresh_token,
        expires_in: refreshedTokens.expires_in,
        expires_at: refreshedTokens.expires_in
          ? Math.floor(Date.now() / 1000) + refreshedTokens.expires_in
          : undefined,
      };

      if (refreshedTokens.id_token) {
        const claims = refreshedTokens.claims() ?? {};
        if (req.session.user) {
          req.session.user.name = claims.name || claims.preferred_username || req.session.user.name;
        }
      }

      if (isInitiator) {
        console.log(`BFF [${sessionId}]: Token refreshed successfully.`);
      }
      
      // Save session explicitly to ensure it's persisted before next middleware
      req.session.save((err) => {
        if (err) console.error(`BFF [${sessionId}]: Session save error after refresh:`, err);
        next();
      });
      return; // Exit to prevent double next()
    } catch (error) {
      console.error(`BFF [${sessionId}]: Failed to refresh token:`, error.message);
      if (error.error) {
        console.error(`BFF [${sessionId}]: Refresh error code:`, error.error);
      }
      if (error.error_description) {
        console.error(`BFF [${sessionId}]: Refresh error description:`, error.error_description);
      }

      // Cleanup and clear cookies if token refresh failed
      if (isInitiator) {
        activeRefreshes.delete(sessionId);
        req.session.destroy((err) => {
          if (err) console.error(`BFF [${sessionId}]: Session destroy error:`, err);
          res.clearCookie('bff.sid');
          res.status(401).json({ error: 'Session expired. Please login again.' });
        });
      } else {
        res.status(401).json({ error: 'Session expired. Please login again.' });
      }
      return;
    } finally {
      // Ensure initiator cleans up its reference in the map
      if (isInitiator) {
        activeRefreshes.delete(sessionId);
      }
    }
  }

  next();
}
