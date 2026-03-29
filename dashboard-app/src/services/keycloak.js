import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://keycloak.local',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'dashboard',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'dashboard-app'
})

export default keycloak
