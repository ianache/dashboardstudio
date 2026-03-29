import { defineStore } from 'pinia'

// Available Anthropic models with metadata
export const ANTHROPIC_MODELS = [
  {
    id: 'claude-opus-4-6',
    label: 'Claude Opus 4.6',
    description: 'Máxima capacidad. Ideal para tareas complejas.',
    tier: 'premium'
  },
  {
    id: 'claude-sonnet-4-6',
    label: 'Claude Sonnet 4.6',
    description: 'Balance entre capacidad y velocidad.',
    tier: 'balanced'
  },
  {
    id: 'claude-haiku-4-5-20251001',
    label: 'Claude Haiku 4.5',
    description: 'Rápido y eficiente. Ideal para asistencia en tiempo real.',
    tier: 'fast'
  }
]

// All registered operations that can be assigned a model
export const LLM_OPERATIONS = [
  {
    id: 'chartAssist',
    label: 'IA Assist — Visualización',
    description: 'Genera opciones ECharts personalizadas para widgets',
    defaultModel: 'claude-haiku-4-5-20251001'
  }
  // Future operations added here
]

function loadState() {
  try {
    const raw = localStorage.getItem('llmConfig')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function buildDefaultModels() {
  return Object.fromEntries(LLM_OPERATIONS.map(op => [op.id, op.defaultModel]))
}

export const useLlmStore = defineStore('llm', {
  state: () => {
    const saved = loadState()
    return {
      anthropicKey: saved?.anthropicKey ?? '',
      models: { ...buildDefaultModels(), ...(saved?.models ?? {}) }
    }
  },

  getters: {
    isConfigured: (state) => state.anthropicKey.trim().length > 0,
    modelFor: (state) => (operationId) =>
      state.models[operationId] ?? LLM_OPERATIONS.find(o => o.id === operationId)?.defaultModel ?? ANTHROPIC_MODELS[2].id
  },

  actions: {
    setKey(key) {
      this.anthropicKey = key.trim()
      this.persist()
    },

    setModel(operationId, modelId) {
      this.models[operationId] = modelId
      this.persist()
    },

    persist() {
      localStorage.setItem('llmConfig', JSON.stringify({
        anthropicKey: this.anthropicKey,
        models: this.models
      }))
    },

    // Migrate old key stored by the previous implementation
    migrateFromLegacy() {
      const legacy = localStorage.getItem('aiApiKey')
      if (legacy && !this.anthropicKey) {
        this.anthropicKey = legacy.trim()
        this.persist()
      }
      localStorage.removeItem('aiApiKey')
    }
  }
})
