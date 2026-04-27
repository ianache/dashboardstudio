import { defineStore } from 'pinia'
import { knowledgeSpacesApi } from '@/services/api'

export const useKnowledgeSpacesStore = defineStore('knowledgeSpaces', {
  state: () => ({
    spaces: [],
    loading: false,
    error: null,
    selectedSpace: null
  }),

  getters: {
    allSpaces: (state) => state.spaces,
    getSpaceById: (state) => (id) => state.spaces.find(s => s.id === id) || null,
    getSpaceByName: (state) => (name) => state.spaces.find(s => s.name === name) || null,
    filteredSpaces: (state) => (query) => {
      if (!query) return state.spaces
      const search = query.toLowerCase()
      return state.spaces.filter(space => 
        space.name.toLowerCase().includes(search) ||
        (space.description && space.description.toLowerCase().includes(search))
      )
    }
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        const spaces = await knowledgeSpacesApi.getAll()
        this.spaces = spaces
      } catch (err) {
        this.error = err.message
        console.error('Failed to load knowledge spaces:', err)
      } finally {
        this.loading = false
      }
    },

    async loadById(id) {
      this.loading = true
      this.error = null
      try {
        const space = await knowledgeSpacesApi.getById(id)
        // Update or add to local state
        const idx = this.spaces.findIndex(s => s.id === id)
        if (idx !== -1) {
          this.spaces[idx] = space
        } else {
          this.spaces.push(space)
        }
        return space
      } catch (err) {
        this.error = err.message
        console.error(`Failed to load knowledge space ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async loadByName(name) {
      this.loading = true
      this.error = null
      try {
        const space = await knowledgeSpacesApi.getByName(name)
        return space
      } catch (err) {
        this.error = err.message
        console.error(`Failed to load knowledge space by name ${name}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async search(query) {
      if (!query || query.trim() === '') {
        return this.spaces
      }
      
      this.loading = true
      this.error = null
      try {
        const spaces = await knowledgeSpacesApi.search(query)
        return spaces
      } catch (err) {
        this.error = err.message
        console.error(`Failed to search knowledge spaces:`, err)
        // Fallback to client-side filtering
        return this.filteredSpaces(query)
      } finally {
        this.loading = false
      }
    },

    async createSpace({ name, description, config }) {
      this.loading = true
      this.error = null
      try {
        const newSpace = await knowledgeSpacesApi.create({
          name,
          description: description || '',
          config: config || {}
        })
        this.spaces.push(newSpace)
        return newSpace
      } catch (err) {
        this.error = err.message
        console.error('Failed to create knowledge space:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateSpace(id, { name, description, config }) {
      this.loading = true
      this.error = null
      try {
        const updated = await knowledgeSpacesApi.update(id, {
          name,
          description: description || '',
          config: config || {}
        })
        // Update local state
        const idx = this.spaces.findIndex(s => s.id === id)
        if (idx !== -1) {
          this.spaces[idx] = { ...this.spaces[idx], ...updated }
        }
        return updated
      } catch (err) {
        this.error = err.message
        console.error(`Failed to update knowledge space ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteSpace(id) {
      this.loading = true
      this.error = null
      try {
        await knowledgeSpacesApi.delete(id)
        this.spaces = this.spaces.filter(s => s.id !== id)
      } catch (err) {
        this.error = err.message
        console.error(`Failed to delete knowledge space ${id}:`, err)
        throw err
      } finally {
        this.loading = false
      }
    },

    setSelectedSpace(space) {
      this.selectedSpace = space
    },

    clearSelectedSpace() {
      this.selectedSpace = null
    }
  }
})
