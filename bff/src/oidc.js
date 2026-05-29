'use strict';

import * as oidc from 'openid-client';
import config from './config.js';

let oidcConfig;

/**
 * Initializes the OIDC client by discovering the provider metadata.
 */
export async function initOIDC() {
  try {
    const issuerUrl = `${config.keycloakUrl}/realms/${config.keycloakRealm}`;
    console.log(`Discovering OIDC provider at ${issuerUrl}...`);
    
    oidcConfig = await oidc.discovery(
      new URL(issuerUrl),
      config.keycloakClientId,
      config.keycloakClientSecret,
      oidc.ClientSecretBasic(config.keycloakClientSecret)
    );
    
    console.log('OIDC provider discovered successfully.');
    return oidcConfig;
  } catch (error) {
    console.error('Failed to discover OIDC provider:', error.message);
    throw error;
  }
}

/**
 * Returns the discovered OIDC configuration.
 */
export function getOIDCConfig() {
  if (!oidcConfig) {
    throw new Error('OIDC client not initialized. Call initOIDC() first.');
  }
  return oidcConfig;
}
