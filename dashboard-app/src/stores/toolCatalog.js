import { defineStore } from 'pinia'
import { diagramTypesApi, editorToolsApi } from '@/services/api'

// ─── Category display metadata (UI only, not stored in DB) ────────────────────
export const CAT_META = {
  source:       { label: 'Fuentes',          icon: 'input',         color: 'var(--primary)', bg: 'color-mix(in srgb, var(--primary) 10%, transparent)' },
  transform:    { label: 'Transformaciones', icon: 'transform',     color: 'var(--tertiary)', bg: 'color-mix(in srgb, var(--tertiary) 10%, transparent)' },
  destination:  { label: 'Destinos',         icon: 'output',        color: 'var(--success)', bg: 'color-mix(in srgb, var(--success) 10%, transparent)' },
  notification: { label: 'Notificaciones',   icon: 'notifications', color: 'var(--warning)', bg: 'color-mix(in srgb, var(--warning) 10%, transparent)' },
  validator:    { label: 'Validadores',      icon: 'verified',      color: 'var(--error)', bg: 'color-mix(in srgb, var(--error) 10%, transparent)' },
  processor:    { label: 'Procesadores',     icon: 'memory',        color: 'var(--secondary)', bg: 'color-mix(in srgb, var(--secondary) 10%, transparent)' },
  annotations:  { label: 'Anotaciones',     icon: 'edit_note',     color: 'var(--warning)', bg: 'color-mix(in srgb, var(--warning) 10%, transparent)' },
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
