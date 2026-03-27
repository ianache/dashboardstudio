import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', {
  state: () => ({
    sidebarCollapsed: false,
    alerts: [],
    alertsOpen: false,
    userMenuOpen: false,
    breadcrumbs: []
  }),

  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },

    setSidebar(collapsed) {
      this.sidebarCollapsed = collapsed
    },

    setBreadcrumbs(crumbs) {
      this.breadcrumbs = crumbs
    },

    toggleAlerts() {
      this.alertsOpen = !this.alertsOpen
      if (this.alertsOpen) this.userMenuOpen = false
    },

    toggleUserMenu() {
      this.userMenuOpen = !this.userMenuOpen
      if (this.userMenuOpen) this.alertsOpen = false
    },

    closeDropdowns() {
      this.alertsOpen = false
      this.userMenuOpen = false
    },

    addAlert(alert) {
      this.alerts.unshift({
        id: Date.now(),
        read: false,
        timestamp: new Date().toISOString(),
        ...alert
      })
      // keep max 20 alerts
      if (this.alerts.length > 20) this.alerts = this.alerts.slice(0, 20)
    },

    markAlertRead(id) {
      const alert = this.alerts.find(a => a.id === id)
      if (alert) alert.read = true
    },

    markAllAlertsRead() {
      this.alerts.forEach(a => { a.read = true })
    }
  },

  getters: {
    unreadAlerts: (state) => state.alerts.filter(a => !a.read).length
  }
})
