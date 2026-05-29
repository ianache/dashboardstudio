import { defineStore } from 'pinia'

// App-side dashboard assignments persist in localStorage keyed by user ID
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

function mapBffUser(bffUser) {
  if (!bffUser) return null

  // Roles defined in Keycloak realm: admin, designer, viewer
  const allRoles = bffUser.roles || []
  const appRoles = allRoles.filter(r => ['admin', 'designer', 'viewer'].includes(r))

  // Priority: admin > designer > viewer
  const role = appRoles.includes('admin') ? 'admin'
             : appRoles.includes('designer') ? 'designer'
             : 'viewer'

  const name = bffUser.name || 'Usuario'
  const parts = name.trim().split(' ')
  const avatar = parts.length >= 2
    ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    : name.substring(0, 2).toUpperCase()

  return {
    id: bffUser.sub,
    name,
    email: bffUser.email || '',
    username: bffUser.name || '',
    roles: appRoles,
    role,
    avatar,
    assignedDashboards: loadAssignedDashboards(bffUser.sub)
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    initialized: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => state.user?.role === 'admin',
    isDesigner: (state) => ['admin', 'designer'].includes(state.user?.role),
    isViewer: (state) => state.user?.role === 'viewer',
    currentUser: (state) => state.user,
    viewers: () => []
  },

  actions: {
    async initialize() {
      const bffUrl = import.meta.env.VITE_BFF_URL || ''
      try {
        const response = await fetch(`${bffUrl}/bff/auth/me`, {
          credentials: 'include'
        })
        
        if (response.ok) {
          const bffUser = await response.json()
          this.user = mapBffUser(bffUser)
        } else {
          this.user = null
          window.location.href = `${bffUrl}/bff/auth/login`
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        this.user = null
        window.location.href = `${bffUrl}/bff/auth/login`
      } finally {
        this.initialized = true
      }
    },

    logout() {
      const bffUrl = import.meta.env.VITE_BFF_URL || ''
      this.user = null
      window.location.href = `${bffUrl}/bff/auth/logout`
    },

    getUserById(id) {
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
