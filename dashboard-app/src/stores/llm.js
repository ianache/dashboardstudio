import { defineStore } from 'pinia'
import { llmConfigApi } from '@/services/api'

// ── Providers & models ────────────────────────────────────────
export const PROVIDERS = [
  {
    id: 'anthropic',
    label: 'Anthropic',
    icon: '◆',
    apiKeyLabel: 'API Key Anthropic',
    apiKeyPlaceholder: 'sk-ant-...',
    docsUrl: 'https://console.anthropic.com/',
    models: [
      { id: 'claude-opus-4-6',           label: 'Claude Opus 4.6',    description: 'Máxima capacidad. Ideal para tareas complejas.',       tier: 'premium'  },
      { id: 'claude-sonnet-4-6',         label: 'Claude Sonnet 4.6',  description: 'Balance entre capacidad y velocidad.',                  tier: 'balanced' },
      { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5',   description: 'Rápido y eficiente. Ideal para asistencia en tiempo real.', tier: 'fast' }
    ]
  },
  {
    id: 'gemini',
    label: 'Google Gemini',
    icon: '◈',
    apiKeyLabel: 'API Key Google AI Studio',
    apiKeyPlaceholder: 'AIza...',
    docsUrl: 'https://aistudio.google.com/apikey',
    models: [
      { id: 'gemini-2.5-pro',       label: 'Gemini 2.5 Pro',        description: 'Máxima capacidad de Google. Razonamiento avanzado.',      tier: 'premium'  },
      { id: 'gemini-2.5-flash',     label: 'Gemini 2.5 Flash',      description: 'Balance ideal entre capacidad y velocidad.',               tier: 'balanced' },
      { id: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite', description: 'Más rápido y económico. Ideal para tareas sencillas.',    tier: 'fast'     }
    ]
  },
  {
    id: 'moonshot',
    label: 'Moonshot AI (Kimi)',
    icon: '🌙',
    apiKeyLabel: 'API Key Moonshot',
    apiKeyPlaceholder: 'sk-...',
    docsUrl: 'https://platform.moonshot.ai/',
    models: [
      { id: 'moonshot-v1-128k', label: 'Kimi 128k',  description: 'Contexto enorme de 128k tokens. Ideal para documentos grandes.', tier: 'premium'  },
      { id: 'moonshot-v1-32k',  label: 'Kimi 32k',   description: 'Balance entre contexto amplio y velocidad.',                     tier: 'balanced' },
      { id: 'moonshot-v1-8k',   label: 'Kimi 8k',    description: 'Rápido y eficiente paro tareas de asistencia diaria.',            tier: 'fast'     }
    ]
  },
  {
    id: 'groq',
    label: 'Groq',
    icon: '⚡',
    apiKeyLabel: 'API Key Groq',
    apiKeyPlaceholder: 'gsk_...',
    docsUrl: 'https://console.groq.com/',
    models: [
      { id: 'llama-3.3-70b-versatile',  label: 'Llama 3.3 70B',      description: 'Meta Llama 70B ultra-rápido. Ideal para tareas complejas.', tier: 'premium'  },
      { id: 'llama3-groq-8b-8192-tool-use-preview', label: 'Llama 3 8B Tools', description: 'Balance rendimiento / velocidad con tool-use.',         tier: 'balanced' },
      { id: 'gemma2-9b-it',             label: 'Gemma 2 9B',         description: 'Google Gemma 2 9B rápido y eficiente.',                     tier: 'fast'     }
    ]
  }
]

// Flat lookup: all models with provider info attached
export const ALL_MODELS = PROVIDERS.flatMap(p =>
  p.models.map(m => ({ ...m, provider: p.id, providerLabel: p.label }))
)

// ── Operations ────────────────────────────────────────────────
// defaultModel uses "providerId:modelId" format
export const LLM_OPERATIONS = [
  {
    id: 'chartAssist',
    label: 'IA Assist — Visualización',
    description: 'Genera opciones ECharts personalizadas para widgets',
    defaultModel: 'anthropic:claude-haiku-4-5-20251001'
  },
  {
    id: 'modelAssist',
    label: 'IA Assist — Modelado Dimensional',
    description: 'Diseña tablas de hechos y dimensiones con sus campos',
    defaultModel: 'anthropic:claude-sonnet-4-6'
  }
]

// ── Helpers ───────────────────────────────────────────────────
function buildDefaultModels() {
  return Object.fromEntries(LLM_OPERATIONS.map(op => [op.id, op.defaultModel]))
}

/** Split "providerId:modelId" → { provider, modelId } */
export function parseProviderModel(value) {
  const sep = value?.indexOf(':') ?? -1
  if (sep === -1) return { provider: 'anthropic', modelId: value ?? '' }
  return { provider: value.slice(0, sep), modelId: value.slice(sep + 1) }
}

/** Look up provider config by id */
export function getProvider(providerId) {
  return PROVIDERS.find(p => p.id === providerId) ?? PROVIDERS[0]
}

// ── Store ─────────────────────────────────────────────────────
export const useLlmStore = defineStore('llm', {
  state: () => ({
    // One API key per provider (loaded from backend)
    keys: {
      anthropic: '',
      gemini: '',
      moonshot: '',
      groq: ''
    },
    // "providerId:modelId" per operation
    models: { ...buildDefaultModels() },
    // Backend loading states
    loading: false,
    saving: false,
    error: null
  }),

  getters: {
    /** True if at least one provider has a key configured */
    isConfigured: (state) => Object.values(state.keys).some(k => k.trim().length > 0),

    /** Key for a specific provider */
    keyFor: (state) => (providerId) => state.keys[providerId] ?? '',

    /**
     * Returns full config for an operation:
     * { provider, modelId, providerLabel, modelLabel, apiKey, providerModel }
     */
    configFor: (state) => (operationId) => {
      const raw = state.models[operationId]
        ?? LLM_OPERATIONS.find(o => o.id === operationId)?.defaultModel
        ?? 'anthropic:claude-haiku-4-5-20251001'
      const { provider, modelId } = parseProviderModel(raw)

      // If the chosen provider has no key, fall back to the first provider that does
      const hasKey = (id) => !!state.keys[id]?.trim()
      const effectiveProvId = hasKey(provider)
        ? provider
        : (PROVIDERS.find(p => hasKey(p.id))?.id ?? provider)

      const prov  = PROVIDERS.find(p => p.id === effectiveProvId) ?? PROVIDERS[0]
      // Keep the chosen model if same provider; otherwise use the provider's default (last = fast)
      const model = effectiveProvId === provider
        ? (prov.models.find(m => m.id === modelId) ?? prov.models[0])
        : prov.models[prov.models.length - 1]

      return {
        provider:      prov.id,
        modelId:       model.id,
        providerLabel: prov.label,
        modelLabel:    model.label,
        apiKey:        state.keys[prov.id] ?? '',
        providerModel: `${prov.id}:${model.id}`
      }
    }
  },

  actions: {
    setKey(providerId, key) {
      this.keys[providerId] = key.trim()
    },

    setModel(operationId, providerModelId) {
      this.models[operationId] = providerModelId
    },

    async loadConfigFromBackend() {
      // Load LLM configurations from backend
      this.loading = true
      this.error = null
      try {
        const configs = await llmConfigApi.getAll()
        // Reset keys first
        this.keys = { anthropic: '', gemini: '', moonshot: '', groq: '' }
        // Populate from backend response
        for (const config of configs) {
          if (config.provider in this.keys) {
            this.keys[config.provider] = config.api_key || ''
          }
        }
      } catch (err) {
        this.error = err.message
        console.warn('Failed to load LLM config from backend:', err)
      } finally {
        this.loading = false
      }
    },

    async saveConfigToBackend() {
      // Save all configured API keys to backend
      this.saving = true
      this.error = null
      const errors = []

      try {
        for (const [provider, key] of Object.entries(this.keys)) {
          if (key.trim()) {
            try {
              await llmConfigApi.save(provider, key.trim())
            } catch (err) {
              errors.push(`${provider}: ${err.message}`)
            }
          }
        }

        if (errors.length > 0) {
          this.error = errors.join(', ')
          return { success: false, error: this.error }
        }

        return { success: true }
      } catch (err) {
        this.error = err.message
        return { success: false, error: err.message }
      } finally {
        this.saving = false
      }
    },

    async deleteProviderConfig(providerId) {
      // Delete a specific provider configuration
      try {
        await llmConfigApi.delete(providerId)
        this.keys[providerId] = ''
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    },

    /** One-time migration from the old localStorage format to backend */
    async migrateFromLegacy() {
      const legacyAiKey = localStorage.getItem('aiApiKey')
      const legacyLlmRaw = localStorage.getItem('llmConfig')

      let hasLegacyData = false

      // Migrate single key format
      if (legacyAiKey) {
        this.keys.anthropic = legacyAiKey.trim()
        hasLegacyData = true
        localStorage.removeItem('aiApiKey')
      }

      // Migrate old config format
      if (legacyLlmRaw) {
        try {
          const old = JSON.parse(legacyLlmRaw)
          if (old.keys) {
            Object.assign(this.keys, old.keys)
            hasLegacyData = true
          }
          if (old.models) {
            Object.assign(this.models, old.models)
          }
        } catch {
          // Ignore parse errors
        }
        localStorage.removeItem('llmConfig')
      }

      // If we have legacy data, save it to backend
      if (hasLegacyData) {
        await this.saveConfigToBackend()
      }
    }
  }
})
