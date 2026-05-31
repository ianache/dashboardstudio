# Research: Phase 34 - Keycloak Auth Flow

## Goal
Implement a full OIDC Authorization Code + PKCE flow in the BFF using `openid-client` v6, ensuring tokens never reach the browser.

## Tech Stack
- **Express 5**: Already in use.
- **openid-client v6**: Functional API, ESM-only.
- **express-session**: Already in use with Redis store.

## Key Findings (openid-client v6)

### 1. ESM Requirement
`openid-client` v6 is ESM-only. The BFF must be converted to an ES Module:
- Add `"type": "module"` to `package.json`.
- Replace `require()` with `import`.
- Use `export default` or named exports.
- Use `import.meta.url` for path-related logic if needed.

### 2. Functional API
Discovery and flow initiation are now functional:
```javascript
import * as oidc from 'openid-client';

// Discovery
const config = await oidc.discovery(
  new URL(issuerUrl),
  clientId,
  clientSecret
);

// Authorization URL
const code_verifier = oidc.generateRandomCodeVerifier();
const code_challenge = await oidc.calculatePKCECodeChallenge(code_verifier);
const url = oidc.buildAuthorizationUrl(config, {
  redirect_uri,
  scope: 'openid profile email',
  code_challenge,
  code_challenge_method: 'S256',
});

// Callback
const tokens = await oidc.authorizationCodeGrant(
  config,
  currentUrl,
  { pkceCodeVerifier: code_verifier }
);
```

### 3. Session Management
- `code_verifier` must be stored in the session during the redirect.
- `state` and `nonce` (if used) should also be managed. `openid-client` v6 handles some of this if configured.
- Tokens (access, refresh, id) will be stored in `req.session.tokens`.

### 4. Token Refresh
Tokens can be refreshed using `oidc.refreshTokenGrant()`:
```javascript
const refreshedTokens = await oidc.refreshTokenGrant(config, tokens.refresh_token);
```

## Proposed Architecture

1.  **ESM Migration**: Atomic conversion of all `bff/` files.
2.  **OIDC Helper**: A module to handle discovery and provide the `config` object.
3.  **Auth Controller**: Handlers for login, callback, me, and logout.
4.  **Auth Middleware**: 
    - `requireAuth`: Protects routes.
    - `refreshTokens`: Ensures tokens are valid before proxying.

## Risks & Mitigations

- **Breaking Change (CommonJS -> ESM)**: Use `node --watch` to verify everything starts correctly.
- **Keycloak Connectivity**: BFF must be able to reach Keycloak's `.well-known/openid-configuration`.
- **Callback URL**: Must match exactly what is registered in Keycloak.

## Success Criteria (Verification)
1. `/bff/auth/login` -> Keycloak Login.
2. Keycloak Login -> `/bff/auth/callback` -> BFF Session.
3. `/bff/auth/me` -> User profile data (no tokens).
4. `/bff/auth/logout` -> Redirect to Keycloak Logout.
5. Tokens are refreshed automatically (can be tested with short-lived tokens if configurable).
