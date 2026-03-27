import { defineStore } from 'pinia'
import cubejs from '@cubejs-client/core'

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
        c.measures.map(m => ({ ...m, cubeName: c.name, fullName: `${c.name}.${m.name}` }))
      )
    },

    allDimensions: (state) => {
      return (state.meta?.cubes || []).flatMap(c =>
        c.dimensions.map(d => ({ ...d, cubeName: c.name, fullName: `${c.name}.${d.name}` }))
      )
    }
  },

  actions: {
    setConfig(apiUrl, token) {
      this.apiUrl = apiUrl
      this.token = token
      localStorage.setItem('cubeApiUrl', apiUrl)
      localStorage.setItem('cubeToken', token)
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
