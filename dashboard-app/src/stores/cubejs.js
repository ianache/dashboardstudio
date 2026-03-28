import { defineStore } from 'pinia'
import cubejs from '@cubejs-client/core'

const dimValuesCache = new Map()
const dimValuesLoading = new Map()

export const useCubeStore = defineStore('cubejs', {
  state: () => ({
    apiUrl: localStorage.getItem('cubeApiUrl') || import.meta.env.VITE_CUBEJS_API_URL || 'http://localhost:4000/cubejs-api/v1',
    token: localStorage.getItem('cubeToken') || import.meta.env.VITE_CUBEJS_TOKEN || '',
    meta: null,
    metaLoading: false,
    metaError: null,
    connected: false
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
      localStorage.setItem('cubeApiUrl', apiUrl)
      localStorage.setItem('cubeToken', token)
      dimValuesCache.clear()
      this.meta = null
      this.connected = false
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
