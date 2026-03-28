import { defineStore } from 'pinia'

function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

function loadModels() {
  try {
    const saved = localStorage.getItem('dimensionalModels')
    return saved ? JSON.parse(saved) : []
  } catch {
    return []
  }
}

export const useDimensionalModelStore = defineStore('dimensionalModel', {
  state: () => ({
    models: loadModels()
  }),

  getters: {
    allModels: (state) => state.models,
    getModel: (state) => (id) => state.models.find(m => m.id === id) || null
  },

  actions: {
    persist() {
      localStorage.setItem('dimensionalModels', JSON.stringify(this.models))
    },

    createModel({ name, description, createdBy }) {
      const model = {
        id: generateId(),
        name,
        description: description || '',
        createdBy: createdBy || '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        nodes: [],
        relationships: []
      }
      this.models.push(model)
      this.persist()
      return model
    },

    updateModel(id, patch) {
      const m = this.models.find(m => m.id === id)
      if (!m) return
      Object.assign(m, patch, { updatedAt: new Date().toISOString() })
      this.persist()
    },

    deleteModel(id) {
      const idx = this.models.findIndex(m => m.id === id)
      if (idx !== -1) { this.models.splice(idx, 1); this.persist() }
    },

    addNode(modelId, { type, name, x = 100, y = 100 }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = { id: generateId(), type, name, x, y, fields: [] }
      m.nodes.push(node)
      m.updatedAt = new Date().toISOString()
      this.persist()
      return node
    },

    updateNode(modelId, nodeId, patch) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      Object.assign(node, patch)
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    deleteNode(modelId, nodeId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      m.nodes = m.nodes.filter(n => n.id !== nodeId)
      m.relationships = m.relationships.filter(r => r.fromNodeId !== nodeId && r.toNodeId !== nodeId)
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    setKeyField(modelId, nodeId, fieldId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      node.fields.forEach(f => { f.isKey = f.id === fieldId })
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    addField(modelId, nodeId, { name, description, dataType, isKey = false, isFk = false }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      const field = { id: generateId(), name, description: description || '', dataType, isKey, isFk }
      node.fields.push(field)
      m.updatedAt = new Date().toISOString()
      this.persist()
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
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    deleteField(modelId, nodeId, fieldId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const node = m.nodes.find(n => n.id === nodeId)
      if (!node) return
      node.fields = node.fields.filter(f => f.id !== fieldId)
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    addRelationship(modelId, { fromNodeId, toNodeId, cardinality = '1:N' }) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const rel = { id: generateId(), fromNodeId, toNodeId, cardinality }
      m.relationships.push(rel)
      m.updatedAt = new Date().toISOString()
      this.persist()
      return rel
    },

    updateRelationship(modelId, relId, patch) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      const rel = m.relationships.find(r => r.id === relId)
      if (!rel) return
      Object.assign(rel, patch)
      m.updatedAt = new Date().toISOString()
      this.persist()
    },

    deleteRelationship(modelId, relId) {
      const m = this.models.find(m => m.id === modelId)
      if (!m) return
      m.relationships = m.relationships.filter(r => r.id !== relId)
      m.updatedAt = new Date().toISOString()
      this.persist()
    }
  }
})
