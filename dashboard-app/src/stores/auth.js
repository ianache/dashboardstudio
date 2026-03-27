import { defineStore } from 'pinia'

const MOCK_USERS = [
  {
    id: '1',
    name: 'Ana García',
    email: 'admin@demo.com',
    password: 'admin123',
    role: 'designer',
    avatar: 'AG',
    assignedDashboards: []
  },
  {
    id: '2',
    name: 'Carlos López',
    email: 'viewer@demo.com',
    password: 'viewer123',
    role: 'viewer',
    avatar: 'CL',
    assignedDashboards: []
  },
  {
    id: '3',
    name: 'María Torres',
    email: 'maria@demo.com',
    password: 'maria123',
    role: 'viewer',
    avatar: 'MT',
    assignedDashboards: []
  }
]

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    allUsers: JSON.parse(localStorage.getItem('mockUsers') || JSON.stringify(MOCK_USERS))
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    isDesigner: (state) => state.user?.role === 'designer',
    isViewer: (state) => state.user?.role === 'viewer',
    currentUser: (state) => state.user,
    viewers: (state) => state.allUsers.filter(u => u.role === 'viewer')
  },

  actions: {
    async login(email, password) {
      const user = this.allUsers.find(u => u.email === email && u.password === password)
      if (!user) throw new Error('Credenciales incorrectas')

      const { password: _, ...safeUser } = user
      this.user = safeUser
      this.token = `mock-token-${user.id}-${Date.now()}`

      localStorage.setItem('auth', JSON.stringify({ user: this.user, token: this.token }))
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('auth')
    },

    initFromStorage() {
      const stored = localStorage.getItem('auth')
      if (stored) {
        try {
          const { user, token } = JSON.parse(stored)
          this.user = user
          this.token = token
        } catch {
          localStorage.removeItem('auth')
        }
      }
    },

    getUserById(id) {
      return this.allUsers.find(u => u.id === id)
    },

    updateUserAssignedDashboards(userId, dashboardIds) {
      const idx = this.allUsers.findIndex(u => u.id === userId)
      if (idx !== -1) {
        this.allUsers[idx].assignedDashboards = dashboardIds
        localStorage.setItem('mockUsers', JSON.stringify(this.allUsers))

        // Update current user if it's them
        if (this.user?.id === userId) {
          this.user = { ...this.user, assignedDashboards: dashboardIds }
          localStorage.setItem('auth', JSON.stringify({ user: this.user, token: this.token }))
        }
      }
    }
  }
})
