import { defineStore } from 'pinia'
import { dimensionalModelApi } from '@/services/api'

function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

export const useDimensionalModelStore = defineStore('dimensionalModel', {
  state: () => ({
    models: [],
    loading: false,
    error: null
  }),

  getters: {
    allModels: (state) => state.models,
    getModel: (state) => (id) => state.models.find(m => m.id === id) || null,
    globalModel: (state) => state.models.find(m => m.isGlobal) || null
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        const models = await dimensionalModelApi.getAll()
        // Transform backend format to frontend format
        this.models = models.map(m => this._transformBackendToFrontend(m))
      } catch (err) {
        this.error = err.message
        console.error('Failed to load dimensional models:', err)
      } finally {
        this.loading = false
      }
    },

    _transformBackendToFrontend(m) {
      const nodes = (m.nodes || []).map(n => this._transformNodeBackendToFrontend(n))
      const diagrams = Array.isArray(m.diagrams) && m.diagrams.length
        ? m.diagrams
        : [{
            id: 'main',
            name: 'Principal',
            description: '',
            isMain: true,
            diagramNodes: nodes.map(n => ({ nodeId: n.id, x: n.x || 100, y: n.y || 100 }))
          }]
      return {
        id: m.id,
        name: m.name,
        description: m.description,
        isGlobal: m.is_global,
        createdBy: m.created_by,
        createdAt: m.created_at,
        updatedAt: m.updated_at,
        nodes,
        relationships: (m.relationships || []).map(r => this._transformRelationshipBackendToFrontend(r)),
        diagrams
      }
    },

    _transformNodeBackendToFrontend(n) {
      return {
        id: n.id,
        type: n.type,
        name: n.name,
        x: n.x || 100,
        y: n.y || 100,
        globalRef: n.global_ref || null,
        fields: (n.fields || []).map(f => this._transformFieldBackendToFrontend(f))
      }
    },

    _transformFieldBackendToFrontend(f) {
      return {
        id: f.id,
        name: f.name,
        description: f.description || '',
        dataType: f.dataType || f.data_type || 'dt-varchar',
        isKey: f.isKey || f.is_key || false,
        isFk: f.isFk || f.is_fk || false
      }
    },

    _transformRelationshipBackendToFrontend(r) {
      return {
        id: r.id,
        fromNodeId: r.fromNodeId || r.from_node_id,
        toNodeId: r.toNodeId || r.to_node_id,
        cardinality: r.cardinality || '1:N'
      }
    },

    _transformModelFrontendToBackend(model) {
      return {
        name: model.name,
        description: model.description,
        is_global: model.isGlobal,
        nodes: model.nodes.map(n => this._transformNodeFrontendToBackend(n)),
        relationships: model.relationships.map(r => this._transformRelationshipFrontendToBackend(r)),
        diagrams: model.diagrams || []
      }
    },

    _transformNodeFrontendToBackend(n) {
      return {
        id: n.id,
        type: n.type,
        name: n.name,
        x: n.x,
        y: n.y,
        global_ref: n.globalRef,
        fields: n.fields.map(f => this._transformFieldFrontendToBackend(f))
      }
    },

    _transformFieldFrontendToBackend(f) {
      return {
        id: f.id,
        name: f.name,
        description: f.description,
        dataType: f.dataType,
        isKey: f.isKey,
        isFk: f.isFk
      }
    },

    _transformRelationshipFrontendToBackend(r) {
      return {
        id: r.id,
        fromNodeId: r.fromNodeId,
        toNodeId: r.toNodeId,
        cardinality: r.cardinality
      }
    },

    async createModel({ name, description, createdBy }) {
      try {
        const modelData = {
          name,
          description: description || '',
          is_global: false,
          nodes: [],
          relationships: []
        }
        const created = await dimensionalModelApi.create(modelData)
        const frontendModel = this._transformBackendToFrontend(created)
        frontendModel.createdBy = createdBy
        this.models.push(frontendModel)
        return frontendModel
      } catch (err) {
        console.error('Failed to create model:', err)
        throw err
      }
    },

    async updateModel(id, patch) {
      try {
        const model = this.models.find(m => m.id === id)
        if (!model) return

        // Transform to backend format
        const backendPatch = {}
        if (patch.name !== undefined) backendPatch.name = patch.name
        if (patch.description !== undefined) backendPatch.description = patch.description
        if (patch.isGlobal !== undefined) backendPatch.is_global = patch.isGlobal
        if (patch.nodes !== undefined) backendPatch.nodes = patch.nodes.map(n => this._transformNodeFrontendToBackend(n))
        if (patch.relationships !== undefined) backendPatch.relationships = patch.relationships.map(r => this._transformRelationshipFrontendToBackend(r))
        if (patch.diagrams !== undefined) backendPatch.diagrams = patch.diagrams

        await dimensionalModelApi.update(id, backendPatch)

        // Update local state
        const idx = this.models.findIndex(m => m.id === id)
        if (idx !== -1) {
          this.models[idx] = { ...this.models[idx], ...patch }
        }
      } catch (err) {
        console.error('Failed to update model:', err)
        throw err
      }
    },

    async deleteModel(id) {
      try {
        await dimensionalModelApi.delete(id)
        const model = this.models.find(m => m.id === id)
        if (model?.isGlobal) return // Global model cannot be deleted
        this.models = this.models.filter(m => m.id !== id)
      } catch (err) {
        console.error('Failed to delete model:', err)
        throw err
      }
    },

    async setGlobal(modelId) {
      try {
        await dimensionalModelApi.setGlobal(modelId)
        // Update local state
        this.models.forEach(m => {
          m.isGlobal = m.id === modelId
        })
      } catch (err) {
        console.error('Failed to set global model:', err)
        throw err
      }
    },

    addNode(modelId, { type, name, x = 100, y = 100 }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = { id: generateId(), type, name, x, y, globalRef: null, fields: [] }
      m.nodes.push(node)
      // Keep main diagram in sync
      const mainDiagram = m.diagrams?.find(d => d.isMain)
      if (mainDiagram) {
        mainDiagram.diagramNodes.push({ nodeId: node.id, x, y })
      }
      return node
    },

    addGlobalDimRef(modelId, globalNodeId, position) {
      const m = this.models.find(m => m.id === modelId)
      const globalModel = this.models.find(m => m.isGlobal)
      const globalNode = globalModel?.nodes.find(n => n.id === globalNodeId)
      if (!m || !globalNode) return null
      const node = {
        id: generateId(),
        type: globalNode.type,
        name: globalNode.name,
        x: position?.x ?? 60,
        y: position?.y ?? 60,
        globalRef: { modelId: globalModel.id, nodeId: globalNodeId },
        fields: []
      }
      m.nodes.push(node)
      return node
    },

    updateNode(modelId, nodeId, patch) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      Object.assign(node, patch)
    },

    deleteNode(modelId, nodeId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      m.nodes = m.nodes.filter(n => n.id !== nodeId)
      m.relationships = m.relationships.filter(r => r.fromNodeId !== nodeId && r.toNodeId !== nodeId)
      // Remove dangling references from all diagrams
      if (m.diagrams) {
        m.diagrams.forEach(diag => {
          diag.diagramNodes = diag.diagramNodes.filter(dn => dn.nodeId !== nodeId)
        })
      }
    },

    setKeyField(modelId, nodeId, fieldId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      node.fields.forEach(f => { f.isKey = f.id === fieldId })
    },

    addField(modelId, nodeId, { name, description, dataType, isKey = false, isFk = false }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      const field = { id: generateId(), name, description: description || '', dataType, isKey, isFk }
      node.fields.push(field)
      return field
    },

    updateField(modelId, nodeId, fieldId, patch) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      const field = node.fields.find(f => f.id === fieldId)
      if (!field) return
      Object.assign(field, patch)
    },

    deleteField(modelId, nodeId, fieldId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      node.fields = node.fields.filter(f => f.id !== fieldId)
    },

    addRelationship(modelId, { fromNodeId, toNodeId, cardinality = '1:N' }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const rel = { id: generateId(), fromNodeId, toNodeId, cardinality }
      m.relationships.push(rel)
      return rel
    },

    updateRelationship(modelId, relId, patch) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const rel = m.relationships.find(r => r.id === relId)
      if (!rel) return
      Object.assign(rel, patch)
    },

    deleteRelationship(modelId, relId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      m.relationships = m.relationships.filter(r => r.id !== relId)
    },

    // ─── Diagram actions ─────────────────────────────────────────────────────────

    createDiagram(modelId, { name = 'Nuevo diagrama' } = {}) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      if (!m.diagrams) m.diagrams = []
      const diag = {
        id: generateId(),
        name,
        description: '',
        isMain: false,
        diagramNodes: []
      }
      m.diagrams.push(diag)
      return diag
    },

    renameDiagram(modelId, diagramId, newName) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const diag = m.diagrams?.find(d => d.id === diagramId)
      if (diag) diag.name = newName
    },

    updateDiagramDescription(modelId, diagramId, description) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const diag = m.diagrams?.find(d => d.id === diagramId)
      if (diag) diag.description = description
    },

    deleteDiagram(modelId, diagramId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      // Never delete the main diagram
      const diag = m.diagrams?.find(d => d.id === diagramId)
      if (!diag || diag.isMain) return
      m.diagrams = m.diagrams.filter(d => d.id !== diagramId)
    },

    addNodeToDiagram(modelId, diagramId, nodeId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const diag = m.diagrams?.find(d => d.id === diagramId)
      if (!diag) return
      // Avoid duplicates
      if (diag.diagramNodes.some(dn => dn.nodeId === nodeId)) return
      const canonical = m.nodes.find(n => n.id === nodeId)
      if (!canonical) return
      diag.diagramNodes.push({ nodeId, x: canonical.x || 100, y: canonical.y || 100 })
    },

    removeNodeFromDiagram(modelId, diagramId, nodeId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const diag = m.diagrams?.find(d => d.id === diagramId)
      // Never remove from main diagram via this action — use deleteNode for canonical removal
      if (!diag || diag.isMain) return
      diag.diagramNodes = diag.diagramNodes.filter(dn => dn.nodeId !== nodeId)
    },

    updateDiagramNodePosition(modelId, diagramId, nodeId, x, y) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const diag = m.diagrams?.find(d => d.id === diagramId)
      if (!diag) return
      const dn = diag.diagramNodes.find(dn => dn.nodeId === nodeId)
      if (dn) { dn.x = x; dn.y = y }
    },

    async saveModelToBackend(modelId) {
      try {
        const model = this.models.find(m => m.id === modelId)
        if (!model) return
        await this.updateModel(modelId, model)
      } catch (err) {
        console.error('Failed to save model to backend:', err)
        throw err
      }
    },

    persist() {
      console.log('persist() called - data is already in memory')
    },

    ensureGlobalModel() {
      const global = this.models.find(m => m.isGlobal)
      if (!global) return
      this.models.forEach(m => {
        if (m.isGlobal) {
          m.nodes.forEach(n => {
            n.globalRef = { modelId: m.id, nodeId: n.id }
          })
        }
      })
    }
  }
})
