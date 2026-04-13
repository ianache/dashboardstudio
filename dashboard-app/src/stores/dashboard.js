import { defineStore } from 'pinia'
import { dashboardApi } from '@/services/api'

function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dashboards: [],
    activeDashboardId: null,
    loading: false,
    error: null
  }),

  getters: {
    allDashboards: (state) => state.dashboards,

    activeDashboard: (state) => state.dashboards.find(d => d.id === state.activeDashboardId),

    dashboardsForDesigner: (state) => state.dashboards,

    dashboardsForUser: (state) => (userId) => {
      return state.dashboards.filter(d => d.assignedUsers?.includes(userId) || d.isPublic)
    }
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        const dashboards = await dashboardApi.getAll()
        // Transform backend format to frontend format
        this.dashboards = dashboards.map(d => this._transformBackendToFrontend(d))
      } catch (err) {
        this.error = err.message
        console.error('Failed to load dashboards:', err)
      } finally {
        this.loading = false
      }
    },

    _transformBackendToFrontend(d) {
      return {
        id: d.id,
        name: d.name,
        description: d.description,
        isPublic: d.is_public,
        assignedUsers: d.assigned_users || [],
        createdBy: d.created_by,
        createdAt: d.created_at,
        updatedAt: d.updated_at,
        filters: d.filters || [],
        widgets: (d.widgets || []).map(w => this._transformWidgetBackendToFrontend(w))
      }
    },

    _transformFrontendToBackend(dashboard) {
      return {
        name: dashboard.name,
        description: dashboard.description,
        is_public: dashboard.isPublic,
        filters: dashboard.filters || []
      }
    },

    _transformWidgetBackendToFrontend(w) {
      return {
        id: w.id,
        title: w.title,
        chartType: w.chart_type,
        position: { x: w.position?.x ?? 0, y: w.position?.y ?? 0, w: w.position?.w ?? 6, h: w.position?.h ?? 3 },
        cubeQuery: w.cube_query || { measures: [], dimensions: [], timeDimension: null, filters: [], limit: 100 },
        chartOptions: w.chart_options || {},
        useMockData: w.use_mock_data
      }
    },

    _transformWidgetFrontendToBackend(widget) {
      return {
        title: widget.title,
        chart_type: widget.chartType,
        position: widget.position,
        cube_query: widget.cubeQuery,
        chart_options: widget.chartOptions,
        use_mock_data: widget.useMockData
      }
    },

    async createDashboard(name, description = '', createdBy) {
      try {
        const dashboardData = {
          name,
          description,
          is_public: false,
          filters: []
        }
        const created = await dashboardApi.create(dashboardData)
        const frontendDashboard = this._transformBackendToFrontend(created)
        frontendDashboard.createdBy = createdBy
        frontendDashboard.assignedUsers = []
        frontendDashboard.widgets = []
        this.dashboards.push(frontendDashboard)
        return frontendDashboard
      } catch (err) {
        console.error('Failed to create dashboard:', err)
        throw err
      }
    },

    async updateDashboard(id, updates) {
      try {
        // Transform frontend updates to backend format
        const backendUpdates = {}
        if (updates.name !== undefined) backendUpdates.name = updates.name
        if (updates.description !== undefined) backendUpdates.description = updates.description
        if (updates.isPublic !== undefined) backendUpdates.is_public = updates.isPublic
        if (updates.filters !== undefined) backendUpdates.filters = updates.filters

        await dashboardApi.update(id, backendUpdates)
        
        // Update local state
        const idx = this.dashboards.findIndex(d => d.id === id)
        if (idx !== -1) {
          this.dashboards[idx] = {
            ...this.dashboards[idx],
            ...updates,
            updatedAt: new Date().toISOString()
          }
        }
      } catch (err) {
        console.error('Failed to update dashboard:', err)
        throw err
      }
    },

    async deleteDashboard(id) {
      try {
        await dashboardApi.delete(id)
        this.dashboards = this.dashboards.filter(d => d.id !== id)
        if (this.activeDashboardId === id) {
          this.activeDashboardId = null
        }
      } catch (err) {
        console.error('Failed to delete dashboard:', err)
        throw err
      }
    },

    setActiveDashboard(id) {
      this.activeDashboardId = id
    },

    async addWidget(dashboardId, widget) {
      try {
        const position = this.nextAvailablePosition(this.dashboards.find(d => d.id === dashboardId))
        const widgetData = {
          title: widget.title || 'Nuevo Gráfico',
          chart_type: widget.chartType || 'bar',
          position: widget.position || position,
          cube_query: widget.cubeQuery || { measures: [], dimensions: [], timeDimension: null, filters: [], limit: 100 },
          chart_options: widget.chartOptions || {},
          use_mock_data: widget.useMockData ?? false
        }

        const created = await dashboardApi.createWidget(dashboardId, widgetData)
        const frontendWidget = this._transformWidgetBackendToFrontend(created)

        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          dashboard.widgets.push(frontendWidget)
        }
        return frontendWidget
      } catch (err) {
        console.error('Failed to add widget:', err)
        throw err
      }
    },

    async updateWidget(dashboardId, widgetId, updates) {
      try {
        // Transform frontend updates to backend format
        const backendUpdates = {}
        if (updates.title !== undefined) backendUpdates.title = updates.title
        if (updates.chartType !== undefined) backendUpdates.chart_type = updates.chartType
        if (updates.position !== undefined) backendUpdates.position = updates.position
        if (updates.cubeQuery !== undefined) backendUpdates.cube_query = updates.cubeQuery
        if (updates.chartOptions !== undefined) backendUpdates.chart_options = updates.chartOptions
        if (updates.useMockData !== undefined) backendUpdates.use_mock_data = updates.useMockData

        await dashboardApi.updateWidget(dashboardId, widgetId, backendUpdates)

        // Update local state
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          const widgetIdx = dashboard.widgets.findIndex(w => w.id === widgetId)
          if (widgetIdx !== -1) {
            dashboard.widgets[widgetIdx] = { ...dashboard.widgets[widgetIdx], ...updates }
          }
        }
      } catch (err) {
        console.error('Failed to update widget:', err)
        throw err
      }
    },

    async removeWidget(dashboardId, widgetId) {
      try {
        await dashboardApi.deleteWidget(dashboardId, widgetId)
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          dashboard.widgets = dashboard.widgets.filter(w => w.id !== widgetId)
        }
      } catch (err) {
        console.error('Failed to remove widget:', err)
        throw err
      }
    },

    updateWidgetPosition(dashboardId, widgetId, position) {
      // Optimistic update - will be synced to backend
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (dashboard) {
        const widget = dashboard.widgets.find(w => w.id === widgetId)
        if (widget) {
          widget.position = position
        }
      }
    },

    async assignDashboardToUsers(dashboardId, userIds) {
      try {
        await dashboardApi.assign(dashboardId, userIds)
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          dashboard.assignedUsers = userIds
        }
      } catch (err) {
        console.error('Failed to assign dashboard:', err)
        throw err
      }
    },

    async addDashboardFilter(dashboardId, { dimension, label, type }) {
      const filterData = { dimension, label, type }
      try {
        const updated = await dashboardApi.addFilter(dashboardId, filterData)
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          dashboard.filters = updated.filters || []
        }
      } catch (err) {
        console.error('Failed to add filter:', err)
        throw err
      }
    },

    async removeDashboardFilter(dashboardId, filterId) {
      try {
        await dashboardApi.removeFilter(dashboardId, filterId)
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard?.filters) {
          dashboard.filters = dashboard.filters.filter(f => f.id !== filterId)
        }
      } catch (err) {
        console.error('Failed to remove filter:', err)
        throw err
      }
    },

    nextAvailablePosition(dashboard) {
      if (!dashboard || !dashboard.widgets || dashboard.widgets.length === 0) {
        return { x: 0, y: 0, w: 6, h: 3 }
      }

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
