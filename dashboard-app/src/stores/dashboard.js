import { defineStore } from 'pinia'
import { dashboardApi } from '@/services/api'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dashboards: [],
    activeDashboardId: null,
    loading: false,
    error: null,
    lastLoaded: null
  }),

  getters: {
    allDashboards: (state) => state.dashboards,
    activeDashboard: (state) => state.dashboards.find(d => d.id === state.activeDashboardId),
    dashboardsForDesigner: (state) => state.dashboards,
    dashboardsForUser: (state) => (userId) => {
      if (!userId) return state.dashboards.filter(d => d.isPublic)
      return state.dashboards.filter(d => d.assignedUsers?.includes(userId) || d.isPublic)
    }
  },

  actions: {
    async loadFromBackend(force = false) {
      // Avoid redundant loads if loaded recently (within 30s)
      const now = Date.now()
      if (!force && this.dashboards.length > 0 && this.lastLoaded && (now - this.lastLoaded < 30000)) {
        return
      }

      this.loading = true
      this.error = null
      try {
        const dashboards = await dashboardApi.getAll()
        // Transform backend format to frontend format
        this.dashboards = dashboards.map(d => this._transformBackendToFrontend(d))
        this.lastLoaded = now
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

    _transformWidgetBackendToFrontend(w) {
      const chartOptions = { ...(w.chart_options || {}) }
      const pieOptions = chartOptions._pie || null
      delete chartOptions._pie
      return {
        id: w.id,
        title: w.title,
        chartType: w.chart_type,
        position: { x: w.position?.x ?? 0, y: w.position?.y ?? 0, w: w.position?.w ?? 6, h: w.position?.h ?? 3 },
        cubeQuery: w.cube_query || { measures: [], dimensions: [], timeDimension: null, filters: [], limit: 100 },
        chartOptions,
        pieOptions: pieOptions || { showValue: false, showPercent: true, showTotal: false },
        useMockData: w.use_mock_data
      }
    },

    async createDashboard(name, description, createdBy) {
      try {
        const payload = {
          name,
          description: description || '',
          is_public: false,
          assigned_users: []
        }
        const created = await dashboardApi.create(payload)
        const dashboard = this._transformBackendToFrontend(created)
        this.dashboards.push(dashboard)
        return dashboard
      } catch (err) {
        console.error('Failed to create dashboard:', err)
        throw err
      }
    },

    async addWidget(dashboardId, widgetData) {
      try {
        const chart_options = { ...(widgetData.chartOptions || {}) }
        if (widgetData.pieOptions) chart_options._pie = widgetData.pieOptions
        const backendWidget = {
          title: widgetData.title,
          chart_type: widgetData.chartType,
          position: widgetData.position || { x: 0, y: 0, w: 6, h: 3 },
          cube_query: widgetData.cubeQuery,
          chart_options,
          use_mock_data: widgetData.useMockData || false
        }
        
        const created = await dashboardApi.createWidget(dashboardId, backendWidget)
        const frontendWidget = this._transformWidgetBackendToFrontend(created)
        
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          if (!dashboard.widgets) dashboard.widgets = []
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
        const backendUpdates = {}
        if (updates.title !== undefined) backendUpdates.title = updates.title
        if (updates.chartType !== undefined) backendUpdates.chart_type = updates.chartType
        if (updates.position !== undefined) backendUpdates.position = updates.position
        if (updates.cubeQuery !== undefined) backendUpdates.cube_query = updates.cubeQuery
        if (updates.chartOptions !== undefined || updates.pieOptions !== undefined) {
          const chart_options = { ...(updates.chartOptions || {}) }
          if (updates.pieOptions) chart_options._pie = updates.pieOptions
          backendUpdates.chart_options = chart_options
        }
        if (updates.useMockData !== undefined) backendUpdates.use_mock_data = updates.useMockData

        await dashboardApi.updateWidget(dashboardId, widgetId, backendUpdates)
        
        const dashboard = this.dashboards.find(d => d.id === dashboardId)
        if (dashboard) {
          const idx = dashboard.widgets.findIndex(w => w.id === widgetId)
          if (idx !== -1) {
            dashboard.widgets[idx] = { ...dashboard.widgets[idx], ...updates }
          }
        }
      } catch (err) {
        console.error('Failed to update widget:', err)
        throw err
      }
    },

    async updateWidgetPosition(dashboardId, widgetId, position) {
      return this.updateWidget(dashboardId, widgetId, { position })
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

    async deleteDashboard(id) {
      try {
        await dashboardApi.delete(id)
        this.dashboards = this.dashboards.filter(d => d.id !== id)
      } catch (err) {
        console.error('Failed to delete dashboard:', err)
        throw err
      }
    },

    async addDashboardFilter(dashboardId, { dimension, label, type }) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard) return
      if (!dashboard.filters) dashboard.filters = []
      const filter = {
        id: Math.random().toString(36).substr(2, 9),
        dimension,
        label,
        type
      }
      dashboard.filters.push(filter)
      try {
        await dashboardApi.update(dashboardId, { filters: dashboard.filters })
      } catch (err) {
        dashboard.filters.pop()
        console.error('Failed to add dashboard filter:', err)
        throw err
      }
      return filter
    },

    async removeDashboardFilter(dashboardId, filterId) {
      const dashboard = this.dashboards.find(d => d.id === dashboardId)
      if (!dashboard) return
      const prev = dashboard.filters || []
      dashboard.filters = prev.filter(f => f.id !== filterId)
      try {
        await dashboardApi.update(dashboardId, { filters: dashboard.filters })
      } catch (err) {
        dashboard.filters = prev
        console.error('Failed to remove dashboard filter:', err)
        throw err
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
    }
  }
})
