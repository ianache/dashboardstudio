import { defineStore } from 'pinia'
import { useDashboardStore } from '@/stores/dashboard'

function defaultUsage() {
  return { input_tokens: 0, output_tokens: 0, cost: 0, cache_hit: 0 }
}

function ensureSession(sessions, id) {
  if (!sessions[id]) sessions[id] = { messages: [], usage: defaultUsage() }
  return sessions[id]
}

export const useAiAnalystStore = defineStore('aiAnalyst', {
  state: () => ({
    sessions: {},           // { [dashboardId]: { messages: [], usage: defaultUsage() } }
    activeDashboardId: null,
    loading: false,
    isPanelOpen: false,
    selectedModel: 'gemini-2.5-flash-lite',  // default — backward compatible
    availableModels: []                        // populated from /bff/ai/models
  }),

  getters: {
    messages: (state) => {
      const id = state.activeDashboardId
      return id ? (state.sessions[id]?.messages || []) : []
    },
    usage: (state) => {
      const id = state.activeDashboardId
      return id ? (state.sessions[id]?.usage || defaultUsage()) : defaultUsage()
    }
  },

  actions: {
    togglePanel() {
      this.isPanelOpen = !this.isPanelOpen
      if (this.isPanelOpen) {
        const dashboardStore = useDashboardStore()
        this.activeDashboardId = dashboardStore.activeDashboardId
      }
    },

    async fetchModels() {
      try {
        // Read user's DeepSeek key from llm store (loaded in SettingsView)
        const { useLlmStore } = await import('@/stores/llm')
        const llmStore = useLlmStore()
        const deepseekKey = llmStore.keys?.deepseek || ''

        const headers = { 'Content-Type': 'application/json' }
        if (deepseekKey) {
          headers['X-Deepseek-Api-Key'] = deepseekKey
        }
        const res = await fetch('/bff/ai/models', { credentials: 'include', headers })
        if (res.ok) {
          const data = await res.json()
          this.availableModels = data.models || []
        }
      } catch (err) {
        console.warn('[aiAnalyst] fetchModels error:', err)
        // Fallback: just Gemini
        this.availableModels = [
          { id: 'gemini-2.5-flash-lite', label: 'Gemini Flash', provider: 'google', enabled: true }
        ]
      }
    },

    switchModel(modelId) {
      if (modelId === this.selectedModel) return
      const model = this.availableModels.find(m => m.id === modelId)
      if (!model || !model.enabled) return
      this.selectedModel = modelId
      const id = this.activeDashboardId
      if (id && this.sessions[id]?.messages.length > 0) {
        this.sessions[id].messages.push({
          role: 'divider',
          model: modelId,
          label: `Switched to ${model.label}`
        })
      }
    },

    captureScreenContext() {
      const dashboardStore = useDashboardStore()
      const dashboard = dashboardStore.activeDashboard

      if (!dashboard) {
        return { dashboard: null, widgets: [] }
      }

      const widgets = (dashboard.widgets || []).map(w => ({
        title: w.title,
        type: w.chartType,
        cubeQuery: w.cubeQuery
      }))

      return {
        dashboard: {
          name: dashboard.name,
          description: dashboard.description
        },
        widgets
      }
    },

    async sendMessage(text, resolvedFilters = []) {
      const dashboardStore = useDashboardStore()
      if (!this.activeDashboardId) {
        this.activeDashboardId = dashboardStore.activeDashboardId
      }
      const id = this.activeDashboardId
      if (!id) return  // no active dashboard, ignore

      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      const sessionId = `${id}-${authStore.user?.sub || 'anon'}`

      ensureSession(this.sessions, id)
      const context = this.captureScreenContext()

      // Add user message
      this.sessions[id].messages.push({ role: 'user', content: text })

      // Add placeholder assistant message
      const assistantMsg = {
        role: 'assistant', content: '', thought: '', actions: [], skills: [],
        streaming: true, error: false,
        model: this.selectedModel   // track which model produced this message
      }
      this.sessions[id].messages.push(assistantMsg)
      const msgIndex = this.sessions[id].messages.length - 1

      this.loading = true

      try {
        const { useLlmStore } = await import('@/stores/llm')
        const llmStore = useLlmStore()
        const deepseekKey = this.selectedModel.startsWith('deepseek/') ? (llmStore.keys?.deepseek || '') : undefined

        const response = await fetch('/bff/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
            context,
            model: this.selectedModel,
            ...(resolvedFilters.length > 0 ? { filters: resolvedFilters } : {}),
            ...(deepseekKey !== undefined ? { deepseek_api_key: deepseekKey } : {})
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete lines from buffer
          const lines = buffer.split('\n')
          buffer = lines.pop() // Keep incomplete last line in buffer

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed) continue

            let cleanLine = trimmed
            if (cleanLine.startsWith('data:')) {
              cleanLine = cleanLine.substring(5).trim()
            }
            if (!cleanLine) continue

            try {
              const event = JSON.parse(cleanLine)
              this._processStreamEvent(id, msgIndex, event)
            } catch {
              // Non-JSON line — skip silently
            }
          }
        }

        // Process any remaining buffer content
        const remaining = buffer.trim()
        if (remaining) {
          try {
            let cleanLine = remaining
            if (cleanLine.startsWith('data:')) {
              cleanLine = cleanLine.substring(5).trim()
            }
            if (cleanLine) {
              const event = JSON.parse(cleanLine)
              this._processStreamEvent(id, msgIndex, event)
            }
          } catch {
            // Ignore
          }
        }
      } catch (err) {
        console.error('[aiAnalyst] sendMessage error:', err)
        this.sessions[id].messages[msgIndex].error = true
        this.sessions[id].messages[msgIndex].content = 'Error al obtener respuesta. Intenta nuevamente.'
        this.sessions[id].messages[msgIndex].streaming = false
      } finally {
        // Ensure streaming flag is cleared
        if (this.sessions[id]?.messages[msgIndex]?.streaming) {
          this.sessions[id].messages[msgIndex].streaming = false
        }
        this.loading = false
      }
    },

    _processStreamEvent(id, msgIndex, event) {
      const msg = this.sessions[id]?.messages[msgIndex]
      if (!msg) return

      switch (event.type) {
        case 'error':
          msg.error = true
          msg.content = event.message || 'Error al obtener respuesta.'
          msg.streaming = false
          break
        case 'thought':
          msg.thought = (msg.thought || '') + (event.content || '')
          break
        case 'actions':
          if (Array.isArray(event.data)) {
            msg.actions = event.data
          } else if (event.content) {
            msg.actions = [...(msg.actions || []), event.content]
          }
          break
        case 'skills':
          msg.skills = Array.isArray(event.data) ? event.data : []
          break
        case 'answer':
          msg.content = (msg.content || '') + (event.content || '')
          break
        case 'usage':
          if (event.data) {
            const currentUsage = this.sessions[id].usage
            this.sessions[id].usage = {
              input_tokens: event.data.input_tokens ?? currentUsage.input_tokens,
              output_tokens: event.data.output_tokens ?? currentUsage.output_tokens,
              cost: event.data.cost ?? currentUsage.cost,
              cache_hit: event.data.cache_hit ?? currentUsage.cache_hit
            }
          }
          break
        case 'done':
          msg.streaming = false
          break
      }
    },

    clearMessages() {
      const id = this.activeDashboardId
      if (id) {
        this.sessions[id] = { messages: [], usage: defaultUsage() }
      }
    },

    async executeSkill(skillName, params = {}) {
      const id = this.activeDashboardId
      if (!id) return

      ensureSession(this.sessions, id)

      this.loading = true
      try {
        const response = await fetch('/bff/ai/skill', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ skill: skillName, params })
        })
        const result = await response.json()
        const resultText = result.output || result.result || JSON.stringify(result)
        this.sessions[id].messages.push({
          role: 'assistant',
          content: `**Skill ejecutada: ${skillName}**\n\n${resultText}`,
          thought: '',
          actions: [],
          skills: [],
          streaming: false,
          error: !response.ok
        })
      } catch (err) {
        console.error('[aiAnalyst] executeSkill error:', err)
        this.sessions[id].messages.push({
          role: 'assistant',
          content: `Error al ejecutar skill "${skillName}". Intenta nuevamente.`,
          thought: '',
          actions: [],
          skills: [],
          streaming: false,
          error: true
        })
      } finally {
        this.loading = false
      }
    }
  }
})
