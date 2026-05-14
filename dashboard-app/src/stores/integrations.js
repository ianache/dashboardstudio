import { defineStore } from 'pinia'
import { integrationFlowsApi } from '@/services/api'

export const useIntegrationsStore = defineStore('integrations', {
  state: () => ({
    flows: [],
    currentFlow: null,
    loading: false,
    error: null,
  }),

  getters: {
    allFlows: (state) => state.flows,
    flowById: (state) => (id) => state.flows.find(f => f.id === id) || null,
    flowsByStatus: (state) => (status) => state.flows.filter(f => f.status === status),
    activeCount:    (state) => state.flows.filter(f => f.status === 'active').length,
    errorCount:     (state) => state.flows.filter(f => f.status === 'error').length,
    scheduledCount: (state) => state.flows.filter(f => f.status === 'scheduled').length,
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        this.flows = await integrationFlowsApi.getAll()
      } catch (err) {
        this.error = err.message
        console.error('Failed to load integration flows:', err)
      } finally {
        this.loading = false
      }
    },

    async loadById(id) {
      this.loading = true
      this.error = null
      try {
        const flow = await integrationFlowsApi.getById(id)
        this.currentFlow = flow
        const idx = this.flows.findIndex(f => f.id === id)
        if (idx !== -1) this.flows[idx] = flow
        return flow
      } catch (err) {
        this.error = err.message
        console.error(`Failed to load flow ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async createFlow(data) {
      this.loading = true
      this.error = null
      try {
        const created = await integrationFlowsApi.create(data)
        this.flows.unshift(created)
        return created
      } catch (err) {
        this.error = err.message
        console.error('Failed to create flow:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateFlow(id, data) {
      this.loading = true
      this.error = null
      try {
        const updated = await integrationFlowsApi.update(id, data)
        const idx = this.flows.findIndex(f => f.id === id)
        if (idx !== -1) this.flows[idx] = { ...this.flows[idx], ...updated }
        if (this.currentFlow?.id === id) this.currentFlow = updated
        return updated
      } catch (err) {
        this.error = err.message
        console.error(`Failed to update flow ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async saveDiagram(id, diagramData) {
      try {
        const updated = await integrationFlowsApi.saveDiagram(id, diagramData)
        const idx = this.flows.findIndex(f => f.id === id)
        if (idx !== -1) this.flows[idx] = { ...this.flows[idx], ...updated }
        if (this.currentFlow?.id === id) this.currentFlow = updated
        return updated
      } catch (err) {
        console.error(`Failed to save diagram for flow ${id}:`, err)
        throw err
      }
    },

    async deleteFlow(id) {
      this.loading = true
      this.error = null
      try {
        await integrationFlowsApi.delete(id)
        this.flows = this.flows.filter(f => f.id !== id)
        if (this.currentFlow?.id === id) this.currentFlow = null
      } catch (err) {
        this.error = err.message
        console.error(`Failed to delete flow ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async togglePause(id) {
      const flow = this.flows.find(f => f.id === id)
      if (!flow) return
      const newStatus = flow.status === 'paused' ? 'active' : 'paused'
      return this.updateFlow(id, { status: newStatus })
    },
  },
})
