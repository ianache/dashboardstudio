import { defineStore } from 'pinia'
import { normalizeMember } from '@/composables/useCubeQuery'

function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

const SAMPLE_DASHBOARDS = [
  {
    id: 'demo-1',
    name: 'Demo: Ventas por Región',
    description: 'Dashboard de ejemplo con datos simulados',
    isPublic: true,
    assignedUsers: ['2', '3'],
    createdBy: '1',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    filters: [],
    widgets: [
      {
        id: 'w1',
        title: 'Ventas Mensuales',
        chartType: 'bar',
        position: { x: 0, y: 0, w: 6, h: 3 },
        cubeQuery: {
          measures: [{ key: 'Orders.totalRevenue', label: 'Revenue', color: '#1890ff' }],
          dimensions: [{ key: 'Orders.month', label: 'Mes' }],
          timeDimension: null,
          filters: [],
          limit: 12
        },
        chartOptions: {},
        useMockData: true
      },
      {
        id: 'w2',
        title: 'Distribución por Categoría',
        chartType: 'pie',
        position: { x: 6, y: 0, w: 6, h: 3 },
        cubeQuery: {
          measures: [{ key: 'Products.count', label: 'Cantidad', color: '' }],
          dimensions: [{ key: 'Products.category', label: 'Categoría' }],
          timeDimension: null,
          filters: [],
          limit: 10
        },
        chartOptions: {},
        useMockData: true
      },
      {
        id: 'w3',
        title: 'Tendencia de Pedidos',
        chartType: 'line',
        position: { x: 0, y: 3, w: 8, h: 3 },
        cubeQuery: {
          measures: [{ key: 'Orders.count', label: 'Pedidos', color: '#52c41a' }],
          dimensions: [],
          timeDimension: { dimension: 'Orders.createdAt', granularity: 'month' },
          filters: [],
          limit: 12
        },
        chartOptions: {},
        useMockData: true
      },
      {
        id: 'w4',
        title: 'Meta Cumplida',
        chartType: 'gauge',
        position: { x: 8, y: 3, w: 4, h: 3 },
        cubeQuery: {
          measures: [{ key: 'KPI.achievement', label: 'Logro', color: '#faad14' }],
          dimensions: [],
          timeDimension: null,
          filters: [],
          limit: 1
        },
        chartOptions: {},
        useMockData: true
      }
    ]
  }
]

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dashboards: JSON.parse(localStorage.getItem('dashboards') || JSON.stringify(SAMPLE_DASHBOARDS)),
    activeDashboardId: null
  }),

  getters: {
    allDashboards: (state) => state.dashboards,

    activeDashboard: (state) => state.dashboards.find(d => d.id === state.activeDashboardId),

    dashboardsForDesigner: (state) => state.dashboards,

    dashboardsForUser: (state) => (userId) => {
      return state.dashboards.filter(d => d.assignedUsers.includes(userId) || d.isPublic)
    }
  },

  actions: {
    persist() {
      localStorage.setItem('dashboards', JSON.stringify(this.dashboards))
    },

    createDashboard(name, description = '', createdBy) {
      const dashboard = {
        id: generateId(),
        name,
        description,
        isPublic: false,
        assignedUsers: [],
        createdBy,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        filters: [],
        widgets: []
      }
      this.dashboards.push(dashboard)
      this.persist()
      return dashboard
    },

    updateDashboard(id, updates) {
      const idx = this.dashboards.findIndex(d => d.id === id)
      if (idx !== -1) {
        this.dashboards[idx] = {
          ...this.dashboards[idx],
          ...updates,
          updatedAt: new Date().toISOString()
        }
        this.persist()
      }
    },

    deleteDashboard(id) {
      this.dashboards = this.dashboards.filter(d => d.id !== id)
      this.persist()
    },

    setActiveDashboard(id) {
      this.activeDashboardId = id
    },

    addWidget(dashboardId, widget) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard) return

      const newWidget = {
        id: generateId(),
        title: 'Nuevo Gráfico',
        chartType: 'bar',
        position: this.nextAvailablePosition(dashboard),
        cubeQuery: {
          measures: [],
          dimensions: [],
          timeDimension: null,
          filters: [],
          limit: 100
        },
        chartOptions: {},
        useMockData: false,
        ...widget
      }
      dashboard.widgets.push(newWidget)
      this.persist()
      return newWidget
    },

    updateWidget(dashboardId, widgetId, updates) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard) return
      const widgetIdx = dashboard.widgets.findIndex(w => w.id === widgetId)
      if (widgetIdx !== -1) {
        Object.assign(dashboard.widgets[widgetIdx], updates)
        this.persist()
      }
    },

    removeWidget(dashboardId, widgetId) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (dashboard) {
        dashboard.widgets = dashboard.widgets.filter(w => w.id !== widgetId)
        this.persist()
      }
    },

    updateWidgetPosition(dashboardId, widgetId, position) {
      this.updateWidget(dashboardId, widgetId, { position })
    },

    assignDashboardToUsers(dashboardId, userIds) {
      this.updateDashboard(dashboardId, { assignedUsers: userIds })
    },

    addDashboardFilter(dashboardId, { dimension, label, type }) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard) return
      if (!dashboard.filters) dashboard.filters = []
      dashboard.filters.push({ id: generateId(), dimension: normalizeMember(dimension), label, type })
      this.persist()
    },

    removeDashboardFilter(dashboardId, filterId) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard?.filters) return
      dashboard.filters = dashboard.filters.filter(f => f.id !== filterId)
      this.persist()
    },

    nextAvailablePosition(dashboard) {
      if (dashboard.widgets.length === 0) return { x: 0, y: 0, w: 6, h: 3 }

      // Find the lowest available row
      let maxRow = 0
      dashboard.widgets.forEach(w => {
        const bottom = w.position.y + w.position.h
        if (bottom > maxRow) maxRow = bottom
      })

      // Try to fit in current row first
      const lastRow = maxRow - 3
      const widgetsInLastRow = dashboard.widgets.filter(w => w.position.y === lastRow)
      const usedCols = widgetsInLastRow.reduce((sum, w) => sum + w.position.w, 0)

      if (usedCols + 6 <= 12) {
        return { x: usedCols, y: lastRow, w: 6, h: 3 }
      }

      return { x: 0, y: maxRow, w: 6, h: 3 }
    }
  }
})
