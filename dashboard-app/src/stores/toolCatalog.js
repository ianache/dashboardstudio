import { defineStore } from 'pinia'
import { diagramTypesApi, editorToolsApi } from '@/services/api'

// ─── Category display metadata (UI only, not stored in DB) ────────────────────
export const CAT_META = {
  source:       { label: 'Fuentes',          icon: 'input',         color: '#2563eb', bg: '#eff6ff' },
  transform:    { label: 'Transformaciones', icon: 'transform',     color: '#7c3aed', bg: '#f5f3ff' },
  destination:  { label: 'Destinos',         icon: 'output',        color: '#059669', bg: '#f0fdf4' },
  notification: { label: 'Notificaciones',   icon: 'notifications', color: '#d97706', bg: '#fffbeb' },
  validator:    { label: 'Validadores',      icon: 'verified',      color: '#dc2626', bg: '#fef2f2' },
  processor:    { label: 'Procesadores',     icon: 'memory',        color: '#0891b2', bg: '#ecfeff' },
  annotations:  { label: 'Anotaciones',     icon: 'edit_note',     color: '#d97706', bg: '#fffbeb' },
}

export const useToolCatalogStore = defineStore('toolCatalog', {
  state: () => ({
    diagramTypes: [],
    tools: [],
    loading: false,
    error: null,
  }),

  getters: {
    toolsForDiagram: (state) => (diagramTypeId) =>
      state.tools.filter(t => (t.applicable_diagram_types || []).includes(diagramTypeId)),

    diagramTypeById: (state) => (id) =>
      state.diagramTypes.find(dt => dt.id === id) || null,

    toolById: (state) => (id) =>
      state.tools.find(t => t.id === id) || null,

    toolByType: (state) => (type) =>
      state.tools.find(t => t.type === type) || null,
  },

  actions: {
    // ── Load ──────────────────────────────────────────────────────────────────
    async loadDiagramTypes() {
      try {
        this.diagramTypes = await diagramTypesApi.getAll()
      } catch (err) {
        this.error = err.message
        console.error('Failed to load diagram types:', err)
      }
    },

    async loadTools() {
      try {
        this.tools = await editorToolsApi.getAll()
      } catch (err) {
        this.error = err.message
        console.error('Failed to load editor tools:', err)
      }
    },

    async loadAll() {
      this.loading = true
      this.error = null
      try {
        await Promise.all([this.loadDiagramTypes(), this.loadTools()])
      } finally {
        this.loading = false
      }
    },

    async loadToolsForDiagram(diagramTypeId) {
      try {
        const tools = await editorToolsApi.getForDiagram(diagramTypeId)
        // Merge into state (avoid duplicates)
        for (const tool of tools) {
          const idx = this.tools.findIndex(t => t.id === tool.id)
          if (idx !== -1) this.tools[idx] = tool
          else this.tools.push(tool)
        }
        return tools
      } catch (err) {
        console.error('Failed to load tools for diagram:', err)
        // Fallback to local filter
        return this.toolsForDiagram(diagramTypeId)
      }
    },

    // ── Diagram Types CRUD ────────────────────────────────────────────────────
    async addDiagramType(dt) {
      const created = await diagramTypesApi.create(dt)
      this.diagramTypes.push(created)
      return created
    },

    async updateDiagramType(id, patch) {
      const updated = await diagramTypesApi.update(id, patch)
      const idx = this.diagramTypes.findIndex(dt => dt.id === id)
      if (idx !== -1) this.diagramTypes[idx] = updated
      return updated
    },

    async deleteDiagramType(id) {
      await diagramTypesApi.delete(id)
      this.diagramTypes = this.diagramTypes.filter(dt => dt.id !== id)
    },

    // ── Tools CRUD ────────────────────────────────────────────────────────────
    async addTool(tool) {
      const created = await editorToolsApi.create(tool)
      this.tools.push(created)
      return created
    },

    async updateTool(id, patch) {
      const updated = await editorToolsApi.update(id, patch)
      const idx = this.tools.findIndex(t => t.id === id)
      if (idx !== -1) this.tools[idx] = updated
      return updated
    },

    async deleteTool(id) {
      await editorToolsApi.delete(id)
      this.tools = this.tools.filter(t => t.id !== id)
    },
  },
})
