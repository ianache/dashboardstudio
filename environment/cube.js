// cube.js
const jwksClient = require("jwks-rsa");
const jwt = require("jsonwebtoken");

// ─────────────────────────────────────────────────────────────
//  Cliente JWKS apuntando al endpoint de Keycloak
//  Los tokens emitidos por Keycloak se verifican con las
//  claves públicas del realm — sin compartir ningún secret.
// ─────────────────────────────────────────────────────────────
const KEYCLOAK_URL   = process.env.KEYCLOAK_URL   || "http://keycloak:8080";
const KEYCLOAK_REALM = process.env.KEYCLOAK_REALM || "analytics";

const jwks = jwksClient({
  jwksUri: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs`,
  cache: true,
  cacheMaxEntries: 10,
  cacheMaxAge: 10 * 60 * 1000, // 10 minutos
  rateLimit: true,
});

function getSigningKey(header) {
  return new Promise((resolve, reject) => {
    jwks.getSigningKey(header.kid, (err, key) => {
      if (err) return reject(err);
      resolve(key.getPublicKey());
    });
  });
}

// ─────────────────────────────────────────────────────────────
//  Normaliza los claims del token de Keycloak al formato
//  que usan los Cubes en SECURITY_CONTEXT.*
// ─────────────────────────────────────────────────────────────
function buildSecurityContext(payload) {
  // Keycloak pone los roles del realm en realm_access.roles
  // y los roles del cliente en resource_access.<client>.roles
  const realmRoles   = payload.realm_access?.roles    || [];
  const clientRoles  = payload.resource_access?.cubejs?.roles || [];
  const allRoles     = [...new Set([...realmRoles, ...clientRoles])];

  // Prioridad de rol: admin > manager > sales_rep > viewer
  const ROLE_PRIORITY = ["admin", "manager", "sales_rep", "viewer"];
  const role = ROLE_PRIORITY.find((r) => allRoles.includes(r)) || "viewer";

  return {
    user_id:   payload.sub,
    email:     payload.email,
    name:      payload.name,
    role,
    roles:     allRoles,
    // Atributos custom definidos en Keycloak → User Attributes
    tenant_id: payload.tenant_id || payload["custom:tenant_id"] || "default",
    region:    payload.region    || payload["custom:region"]    || null,
  };
}

module.exports = {
  // ─────────────────────────────────────────────────────────────
  //  Aísla la caché de pre-agregaciones por tenant + rol
  // ─────────────────────────────────────────────────────────────
  contextToAppId: ({ securityContext }) =>
    `CUBEJS_APP_${securityContext.tenant_id}_${securityContext.role}`,

  // ─────────────────────────────────────────────────────────────
  //  Contextos para el refresco automático de pre-agregaciones
  // ─────────────────────────────────────────────────────────────
  scheduledRefreshContexts: async () => [
    { securityContext: { tenant_id: "tenant_a", role: "admin"    } },
    { securityContext: { tenant_id: "tenant_a", role: "viewer"   } },
    { securityContext: { tenant_id: "tenant_b", role: "admin"    } },
  ],

  // ─────────────────────────────────────────────────────────────
  //  Verificación del token JWT emitido por Keycloak
  // ─────────────────────────────────────────────────────────────
  checkAuth: async (req, auth) => {
    if (!auth) throw new Error("Token de autenticación no proporcionado");

    try {
      // Decodifica el header para obtener el kid (key ID)
      const decoded = jwt.decode(auth, { complete: true });
      if (!decoded) throw new Error("Token malformado");

      const signingKey = await getSigningKey(decoded.header);

      const payload = jwt.verify(auth, signingKey, {
        algorithms: ["RS256"],
        issuer: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`,
      });

      req.securityContext = buildSecurityContext(payload);
    } catch (err) {
      throw new Error(`Token inválido: ${err.message}`);
    }
  },

  // ─────────────────────────────────────────────────────────────
  //  Expone los roles al motor de acceso de CubeJS
  // ─────────────────────────────────────────────────────────────
  contextToRoles: ({ securityContext }) => securityContext.roles || ["viewer"],
};
