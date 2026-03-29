import { defineStore } from 'pinia'

// Keycloak instance stored outside Pinia to avoid deep reactivity overhead
let _keycloak = null

// App-side dashboard assignments persist in localStorage keyed by user ID
// (Keycloak manages identity; the app manages which dashboards each user can see)
function loadAssignedDashboards(userId) {
  try {
    const stored = localStorage.getItem(`assignedDashboards_${userId}`)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function saveAssignedDashboards(userId, dashboardIds) {
  localStorage.setItem(`assignedDashboards_${userId}`, JSON.stringify(dashboardIds))
}

function buildUserFromToken(keycloak) {
  const parsed = keycloak.tokenParsed
  if (!parsed) return null

  // Roles defined in Keycloak realm: admin, designer, viewer
  const realmRoles = parsed.realm_access?.roles ?? []
  const appRoles = realmRoles.filter(r => ['admin', 'designer', 'viewer'].includes(r))

  // Priority: admin > designer > viewer
  const role = appRoles.includes('admin') ? 'admin'
             : appRoles.includes('designer') ? 'designer'
             : 'viewer'

  const name = parsed.name || parsed.preferred_username || 'Usuario'
  const parts = name.trim().split(' ')
  const avatar = parts.length >= 2
    ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    : name.substring(0, 2).toUpperCase()

  return {
    id: parsed.sub,
    name,
    email: parsed.email || '',
    username: parsed.preferred_username || '',
    roles: appRoles,
    role,
    avatar,
    assignedDashboards: loadAssignedDashboards(parsed.sub)
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    // admin has all designer capabilities
    isAdmin: (state) => state.user?.role === 'admin',
    isDesigner: (state) => ['admin', 'designer'].includes(state.user?.role),
    isViewer: (state) => state.user?.role === 'viewer',
    currentUser: (state) => state.user,
    // Token for API calls (CubeJS, LLM, etc.)
    token: () => _keycloak?.token ?? null,
    // NOTE: user listing requires Keycloak Admin API — not available client-side.
    // Dashboard assignment UI should use Keycloak Admin API or a backend service.
    viewers: () => []
  },

  actions: {
    initFromKeycloak(keycloak) {
      _keycloak = keycloak
      this.user = buildUserFromToken(keycloak)
    },

    logout() {
      const kc = _keycloak
      this.user = null
      _keycloak = null
      kc?.logout({ redirectUri: window.location.origin })
    },

    // Called by main.js when the token is refreshed
    onTokenRefreshed() {
      if (_keycloak) {
        this.user = buildUserFromToken(_keycloak)
      }
    },

    getToken() {
      return _keycloak?.token
    },

    getUserById(id) {
      // Only the current user is available client-side
      return this.user?.id === id ? this.user : null
    },

    updateUserAssignedDashboards(userId, dashboardIds) {
      saveAssignedDashboards(userId, dashboardIds)
      if (this.user?.id === userId) {
        this.user = { ...this.user, assignedDashboards: dashboardIds }
      }
    }
  }
})
