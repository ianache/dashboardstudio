import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'

export const useAiAnalystStore = defineStore('aiAnalyst', () => {
  // ─── State ──────────────────────────────────────────────────────────────────
  const sessions = reactive({})
  const activeDashboardId = ref(null)
  const loading = ref(false)
  const isPanelOpen = ref(false)
  const selectedModel = ref('gemini-2.5-flash-lite')
  const availableModels = ref([])
  const widgetData = reactive({})
  // Tracks how many divider splices occurred during current sendMessage call,
  // so msgIndex references after a splice remain accurate.
  let _indexOffset = 0

  // ─── Helpers ────────────────────────────────────────────────────────────────
  function defaultUsage() {
    return { input_tokens: 0, output_tokens: 0, cost: 0, cache_hit: 0 }
  }

  function ensureSession(id) {
    if (!sessions[id]) {
      sessions[id] = { messages: [], usage: defaultUsage() }
    }
    return sessions[id]
  }

  // ─── Getters ────────────────────────────────────────────────────────────────
  const messages = computed(() => {
    const id = activeDashboardId.value
    return id ? (sessions[id]?.messages || []) : []
  })

  const usage = computed(() => {
    const id = activeDashboardId.value
    return id ? (sessions[id]?.usage || defaultUsage()) : defaultUsage()
  })

  // ─── Actions ────────────────────────────────────────────────────────────────
  function togglePanel() {
    isPanelOpen.value = !isPanelOpen.value
    if (isPanelOpen.value) {
      const dashboardStore = useDashboardStore()
      activeDashboardId.value = dashboardStore.activeDashboardId
    }
  }

  function setWidgetData(widgetId, data) {
    widgetData[widgetId] = data
  }

  function captureScreenContext() {
    const dashboardStore = useDashboardStore()
    const dashboard = dashboardStore.activeDashboard

    if (!dashboard) {
      return { dashboard: null, widgets: [] }
    }

    const widgets = (dashboard.widgets || []).map(w => {
      const widgetContext = {
        title: w.title,
        type: w.chartType,
        cubeQuery: w.cubeQuery
      }
      if (widgetData[w.id] && widgetData[w.id].length > 0) {
        widgetContext.data = widgetData[w.id]
      }
      return widgetContext
    })

    return {
      dashboard: {
        name: dashboard.name,
        description: dashboard.description
      },
      widgets
    }
  }

  async function fetchModels() {
    try {
      const { useLlmStore } = await import('@/stores/llm')
      const llmStore = useLlmStore()
      const deepseekKey = llmStore.keys?.deepseek || ''
      const groqKey = llmStore.keys?.groq || ''
      const geminiKey = llmStore.keys?.gemini || ''
      const ollamaBase = llmStore.keys?.ollama || ''

      const headers = { 'Content-Type': 'application/json' }
      if (deepseekKey) {
        headers['X-Deepseek-Api-Key'] = deepseekKey
      }
      if (groqKey) {
        headers['X-Groq-Api-Key'] = groqKey
      }
      if (geminiKey) {
        headers['X-Gemini-Api-Key'] = geminiKey
      }
      if (ollamaBase) {
        headers['X-Ollama-Api-Base'] = ollamaBase
      }
      const res = await fetch('/bff/ai/models', { credentials: 'include', headers })
      if (res.ok) {
        const data = await res.json()
        availableModels.value = data.models || []
      }
    } catch (err) {
      console.warn('[aiAnalyst] fetchModels error:', err)
      availableModels.value = [
        { id: 'gemini-2.5-flash-lite', label: 'Gemini Flash', provider: 'google', enabled: true }
      ]
    }
  }

  function switchModel(modelId) {
    if (modelId === selectedModel.value) return
    const model = availableModels.value.find(m => m.id === modelId)
    if (!model || !model.enabled) return
    selectedModel.value = modelId
    const id = activeDashboardId.value
    if (id && sessions[id]?.messages.length > 0) {
      sessions[id].messages.push({
        role: 'divider',
        model: modelId,
        label: `Switched to ${model.label}`
      })
    }
  }

  async function sendMessage(text, resolvedFilters = []) {
    const dashboardStore = useDashboardStore()
    if (!activeDashboardId.value) {
      activeDashboardId.value = dashboardStore.activeDashboardId
    }
    const id = activeDashboardId.value
    if (!id) return

    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const sessionId = `${id}-${authStore.user?.sub || 'anon'}`

    ensureSession(id)
    const context = captureScreenContext()

    // Add user message
    sessions[id].messages.push({ role: 'user', content: text })

    // Add placeholder assistant message
    const assistantMsg = reactive({
      role: 'assistant', content: '', thought: '', thinking: '',
      toolCalls: [], toolResults: [], actions: [], skills: [],
      streaming: true, error: false,
      model: selectedModel.value
    })
    sessions[id].messages.push(assistantMsg)
    const msgIndex = sessions[id].messages.length - 1

    loading.value = true
    _indexOffset = 0

    try {
      const { useLlmStore } = await import('@/stores/llm')
      const llmStore = useLlmStore()
      const deepseekKey = selectedModel.value.startsWith('deepseek/') ? (llmStore.keys?.deepseek || '') : undefined
      const groqKey = selectedModel.value.startsWith('groq/') ? (llmStore.keys?.groq || '') : undefined
      const geminiKey = selectedModel.value.startsWith('gemini') ? (llmStore.keys?.gemini || '') : undefined
      const ollamaBase = selectedModel.value.startsWith('ollama/') ? (llmStore.keys?.ollama || '') : undefined

      const response = await fetch('/bff/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          context,
          model: selectedModel.value,
          ...(resolvedFilters.length > 0 ? { filters: resolvedFilters } : {}),
          ...(deepseekKey !== undefined ? { deepseek_api_key: deepseekKey } : {}),
          ...(groqKey !== undefined ? { groq_api_key: groqKey } : {}),
          ...(geminiKey !== undefined ? { gemini_api_key: geminiKey } : {}),
          ...(ollamaBase !== undefined ? { ollama_api_base: ollamaBase } : {})
        })
      })

      if (!response.ok) {
        if (response.status === 401) {
          authStore.login()
          return
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

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
            _processStreamEvent(id, msgIndex + _indexOffset, event)
          } catch {
            // Ignore
          }
        }
      }

      const remaining = buffer.trim()
      if (remaining) {
        try {
          let cleanLine = remaining
          if (cleanLine.startsWith('data:')) {
            cleanLine = cleanLine.substring(5).trim()
          }
          if (cleanLine) {
            const event = JSON.parse(cleanLine)
            _processStreamEvent(id, msgIndex + _indexOffset, event)
          }
        } catch {
          // Ignore
        }
      }
    } catch (err) {
      console.error('[aiAnalyst] sendMessage error:', err)
      const effectiveMsgIndex = msgIndex + _indexOffset
      sessions[id].messages[effectiveMsgIndex].error = true
      sessions[id].messages[effectiveMsgIndex].content = 'Error al obtener respuesta. Intenta nuevamente.'
      sessions[id].messages[effectiveMsgIndex].streaming = false
    } finally {
      const effectiveMsgIndex = msgIndex + _indexOffset
      if (sessions[id]?.messages[effectiveMsgIndex]?.streaming) {
        sessions[id].messages[effectiveMsgIndex].streaming = false
      }
      loading.value = false
    }
  }

  function _processStreamEvent(id, msgIndex, event) {
    const msg = sessions[id]?.messages[msgIndex]
    if (!msg) return

    switch (event.type) {
      case 'context_summarized':
        // Insert a visual divider before the current streaming placeholder.
        // After splice, the streaming message shifts to msgIndex+1.
        // _indexOffset is incremented so all subsequent accesses use the correct index.
        sessions[id].messages.splice(msgIndex, 0, {
          role: 'divider',
          label: 'Contexto resumido para mantener respuestas precisas',
          model: null
        })
        _indexOffset += 1
        break
      case 'error':
        msg.error = true
        msg.content = event.message || 'Error al obtener respuesta.'
        msg.streaming = false
        break
      case 'thinking':
        msg.thinking = (msg.thinking || '') + (event.content || '')
        break
      case 'tool_call':
        if (!msg.toolCalls) msg.toolCalls = []
        msg.toolCalls.push({ name: event.name, args: event.args || {} })
        break
      case 'tool_result':
        if (!msg.toolResults) msg.toolResults = []
        msg.toolResults.push({ name: event.name, rows: event.rows })
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
          const currentUsage = sessions[id].usage
          sessions[id].usage = {
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
  }

  function clearMessages() {
    const id = activeDashboardId.value
    if (id) {
      sessions[id] = { messages: [], usage: defaultUsage() }
    }
  }

  async function executeSkill(skillName, params = {}) {
    const id = activeDashboardId.value
    if (!id) return

    ensureSession(id)
    loading.value = true

    try {
      const response = await fetch('/bff/ai/skill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ skill: skillName, params })
      })
      const result = await response.json()
      const resultText = result.output || result.result || JSON.stringify(result)
      sessions[id].messages.push({
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
      sessions[id].messages.push({
        role: 'assistant',
        content: `Error al ejecutar skill "${skillName}". Intenta nuevamente.`,
        thought: '',
        actions: [],
        skills: [],
        streaming: false,
        error: true
      })
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    activeDashboardId,
    loading,
    isPanelOpen,
    selectedModel,
    availableModels,
    widgetData,
    messages,
    usage,
    togglePanel,
    setWidgetData,
    captureScreenContext,
    fetchModels,
    switchModel,
    sendMessage,
    clearMessages,
    executeSkill
  }
})
