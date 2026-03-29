import { defineStore } from 'pinia'

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

// ── Persistence ───────────────────────────────────────────────
function loadState() {
  try {
    const raw = localStorage.getItem('llmConfig')
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

// ── Store ─────────────────────────────────────────────────────
export const useLlmStore = defineStore('llm', {
  state: () => {
    const saved = loadState()
    return {
      // One API key per provider
      keys: {
        anthropic: saved?.keys?.anthropic ?? saved?.anthropicKey ?? '',
        gemini:    saved?.keys?.gemini    ?? ''
      },
      // "providerId:modelId" per operation
      models: { ...buildDefaultModels(), ...(saved?.models ?? {}) }
    }
  },

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
      this.persist()
    },

    setModel(operationId, providerModelId) {
      this.models[operationId] = providerModelId
      this.persist()
    },

    persist() {
      localStorage.setItem('llmConfig', JSON.stringify({
        keys:   this.keys,
        models: this.models
      }))
    },

    /** One-time migration from the old single-key format */
    migrateFromLegacy() {
      const legacyAiKey  = localStorage.getItem('aiApiKey')
      const legacyLlmRaw = localStorage.getItem('llmConfig')

      // If old format stored anthropicKey at root level, it's already merged via loadState()
      if (legacyAiKey && !this.keys.anthropic) {
        this.keys.anthropic = legacyAiKey.trim()
        this.persist()
      }
      localStorage.removeItem('aiApiKey')

      // Re-persist to normalise if old format was present
      if (legacyLlmRaw) {
        const old = JSON.parse(legacyLlmRaw)
        if ('anthropicKey' in old) this.persist()  // rewrite without legacy key
      }
    }
  }
})
