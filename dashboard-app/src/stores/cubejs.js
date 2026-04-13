import { defineStore } from 'pinia'
import cubejs from '@cubejs-client/core'
import { cubeConfigApi } from '@/services/api'

const dimValuesCache = new Map()
const dimValuesLoading = new Map()

export const useCubeStore = defineStore('cubejs', {
  state: () => ({
    // Primary source is now backend - start empty and load from API
    apiUrl: import.meta.env.VITE_CUBEJS_API_URL || 'http://localhost:4000/cubejs-api/v1',
    token: import.meta.env.VITE_CUBEJS_TOKEN || '',
    // Backend config info
    configId: null,
    configName: 'Default',
    // Meta state
    meta: null,
    metaLoading: false,
    metaError: null,
    connected: false,
    // Loading states
    loading: false,
    error: null
  }),

  getters: {
    client: (state) => {
      if (!state.token || !state.apiUrl) return null
      return cubejs(state.token, { apiUrl: state.apiUrl })
    },

    cubes: (state) => state.meta?.cubes || [],

    getMeasuresForCube: (state) => (cubeName) => {
      const cube = state.meta?.cubes?.find(c => c.name === cubeName)
      return cube?.measures || []
    },

    getDimensionsForCube: (state) => (cubeName) => {
      const cube = state.meta?.cubes?.find(c => c.name === cubeName)
      return cube?.dimensions || []
    },

    allMeasures: (state) => {
      return (state.meta?.cubes || []).flatMap(c =>
        c.measures.map(m => {
          const fullName = m.name.startsWith(c.name + '.') ? m.name : `${c.name}.${m.name}`
          return { ...m, cubeName: c.name, fullName }
        })
      )
    },

    allDimensions: (state) => {
      return (state.meta?.cubes || []).flatMap(c =>
        c.dimensions.map(d => {
          const fullName = d.name.startsWith(c.name + '.') ? d.name : `${c.name}.${d.name}`
          return { ...d, cubeName: c.name, fullName }
        })
      )
    }
  },

  actions: {
    setConfig(apiUrl, token) {
      this.apiUrl = apiUrl
      this.token = token
      dimValuesCache.clear()
      this.meta = null
      this.connected = false
    },

    async loadConfigFromBackend() {
      // Load active CubeJS configuration from backend
      this.loading = true
      this.error = null
      try {
        const config = await cubeConfigApi.getActive()
        this.configId = config.id
        this.configName = config.name
        this.apiUrl = config.api_url || this.apiUrl
        this.token = config.api_token || ''
        this.connected = false // Will be set true after successful meta load
      } catch (err) {
        this.error = err.message
        // Keep fallback values on error
        console.warn('Failed to load CubeJS config from backend:', err)
      } finally {
        this.loading = false
      }
    },

    async saveConfigToBackend(name, apiUrl, apiToken, isActive = true) {
      // Save or update CubeJS configuration in backend
      this.loading = true
      this.error = null
      try {
        const configData = {
          name: name || 'Default',
          api_url: apiUrl,
          api_token: apiToken,
          is_active: isActive
        }

        let config
        if (this.configId && this.configId !== 'demo') {
          // Update existing
          config = await cubeConfigApi.update(this.configId, configData)
        } else {
          // Create new
          config = await cubeConfigApi.create(configData)
        }

        this.configId = config.id
        this.configName = config.name
        this.apiUrl = config.api_url
        this.token = config.api_token

        return { success: true, config }
      } catch (err) {
        this.error = err.message
        return { success: false, error: err.message }
      } finally {
        this.loading = false
      }
    },

    async loadMeta() {
      if (!this.client) return
      this.metaLoading = true
      this.metaError = null
      try {
        const meta = await this.client.meta()
        this.meta = meta
        this.connected = true
      } catch (err) {
        this.metaError = err.message
        this.connected = false
      } finally {
        this.metaLoading = false
      }
    },

    async executeQuery(query) {
      if (!this.client) throw new Error('CubeJS no configurado')
      const result = await this.client.load(query)
      return result
    },

    async loadDimensionValues(dimension) {
      if (dimValuesCache.has(dimension)) return dimValuesCache.get(dimension)
      if (dimValuesLoading.has(dimension)) return dimValuesLoading.get(dimension)

      const promise = this.executeQuery({ dimensions: [dimension], limit: 500 })
        .then(result => {
          const rows = result.tablePivot ? result.tablePivot() : []
          const values = rows.map(r => r[dimension]).filter(v => v != null)
          dimValuesCache.set(dimension, values)
          dimValuesLoading.delete(dimension)
          return values
        })
        .catch(err => { dimValuesLoading.delete(dimension); throw err })

      dimValuesLoading.set(dimension, promise)
      return promise
    },

    clearDimensionValuesCache() {
      dimValuesCache.clear()
    },

    async testConnection() {
      try {
        await this.loadMeta()
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }
  }
})
