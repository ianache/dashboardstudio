import { defineStore } from 'pinia'
import { dataSourcesApi } from '@/services/api'

export const useDataSourcesStore = defineStore('dataSources', {
  state: () => ({
    dataSources: [],
    loading: false,
    error: null,
    selectedDataSource: null
  }),

  getters: {
    allDataSources: (state) => state.dataSources,
    getDataSourceById: (state) => (id) => state.dataSources.find(ds => ds.id === id) || null,
    getDataSourceByName: (state) => (name) => state.dataSources.find(ds => ds.name === name) || null,
    filteredDataSources: (state) => (query) => {
      if (!query) return state.dataSources
      const search = query.toLowerCase()
      return state.dataSources.filter(ds => 
        ds.name.toLowerCase().includes(search) ||
        ds.type.toLowerCase().includes(search) ||
        (ds.description && ds.description.toLowerCase().includes(search))
      )
    },
    dataSourcesByType: (state) => {
      const grouped = {}
      state.dataSources.forEach(ds => {
        if (!grouped[ds.type]) {
          grouped[ds.type] = []
        }
        grouped[ds.type].push(ds)
      })
      return grouped
    }
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        const dataSources = await dataSourcesApi.getAll()
        this.dataSources = dataSources
      } catch (err) {
        this.error = err.message
        console.error('Failed to load data sources:', err)
      } finally {
        this.loading = false
      }
    },

    async loadById(id) {
      this.loading = true
      this.error = null
      try {
        const dataSource = await dataSourcesApi.getById(id)
        // Update or add to local state
        const idx = this.dataSources.findIndex(ds => ds.id === id)
        if (idx !== -1) {
          this.dataSources[idx] = dataSource
        } else {
          this.dataSources.push(dataSource)
        }
        return dataSource
      } catch (err) {
        this.error = err.message
        console.error(`Failed to load data source ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async loadByName(name) {
      this.loading = true
      this.error = null
      try {
        const dataSource = await dataSourcesApi.getByName(name)
        return dataSource
      } catch (err) {
        this.error = err.message
        console.error(`Failed to load data source by name ${name}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async search(query) {
      if (!query || query.trim() === '') {
        return this.dataSources
      }
      
      this.loading = true
      this.error = null
      try {
        const dataSources = await dataSourcesApi.search(query)
        return dataSources
      } catch (err) {
        this.error = err.message
        console.error(`Failed to search data sources:`, err)
        // Fallback to client-side filtering
        return this.filteredDataSources(query)
      } finally {
        this.loading = false
      }
    },

    async createDataSource({ name, type, connectionUrl, username, password, description }) {
      this.loading = true
      this.error = null
      try {
        const newDataSource = await dataSourcesApi.create({
          name,
          type,
          connection_url: connectionUrl,
          username: username || null,
          password: password || null,
          description: description || '',
          is_active: true
        })
        this.dataSources.push(newDataSource)
        return newDataSource
      } catch (err) {
        this.error = err.message
        console.error('Failed to create data source:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateDataSource(id, { name, type, connectionUrl, username, password, description, isActive }) {
      this.loading = true
      this.error = null
      try {
        const updateData = {}
        if (name !== undefined) updateData.name = name
        if (type !== undefined) updateData.type = type
        if (connectionUrl !== undefined) updateData.connection_url = connectionUrl
        if (username !== undefined) updateData.username = username
        if (password !== undefined) updateData.password = password
        if (description !== undefined) updateData.description = description
        if (isActive !== undefined) updateData.is_active = isActive

        const updated = await dataSourcesApi.update(id, updateData)
        // Update local state
        const idx = this.dataSources.findIndex(ds => ds.id === id)
        if (idx !== -1) {
          this.dataSources[idx] = { ...this.dataSources[idx], ...updated }
        }
        return updated
      } catch (err) {
        this.error = err.message
        console.error(`Failed to update data source ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteDataSource(id) {
      this.loading = true
      this.error = null
      try {
        await dataSourcesApi.delete(id)
        this.dataSources = this.dataSources.filter(ds => ds.id !== id)
      } catch (err) {
        this.error = err.message
        console.error(`Failed to delete data source ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async testConnection(id) {
      this.loading = true
      this.error = null
      try {
        const result = await dataSourcesApi.testConnection(id)
        return result
      } catch (err) {
        this.error = err.message
        console.error(`Failed to test connection for data source ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    setSelectedDataSource(dataSource) {
      this.selectedDataSource = dataSource
    },

    clearSelectedDataSource() {
      this.selectedDataSource = null
    }
  }
})
