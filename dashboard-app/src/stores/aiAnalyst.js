import { defineStore } from 'pinia'
import { useDashboardStore } from '@/stores/dashboard'

export const useAiAnalystStore = defineStore('aiAnalyst', {
  state: () => ({
    messages: [],
    loading: false,
    usage: {
      input_tokens: 0,
      output_tokens: 0,
      cost: 0
    },
    isPanelOpen: false
  }),

  actions: {
    togglePanel() {
      this.isPanelOpen = !this.isPanelOpen
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

    async sendMessage(text) {
      const context = this.captureScreenContext()

      // Add user message
      this.messages.push({ role: 'user', content: text })

      // Add placeholder assistant message
      const assistantMsg = { role: 'assistant', content: '', thought: '', streaming: true, error: false }
      this.messages.push(assistantMsg)
      const msgIndex = this.messages.length - 1

      this.loading = true

      try {
        const response = await fetch('/bff/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ message: text, context })
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

            try {
              const event = JSON.parse(trimmed)
              this._processStreamEvent(msgIndex, event)
            } catch {
              // Non-JSON line — skip silently
            }
          }
        }

        // Process any remaining buffer content
        if (buffer.trim()) {
          try {
            const event = JSON.parse(buffer.trim())
            this._processStreamEvent(msgIndex, event)
          } catch {
            // Ignore
          }
        }
      } catch (err) {
        console.error('[aiAnalyst] sendMessage error:', err)
        this.messages[msgIndex].error = true
        this.messages[msgIndex].content = 'Error al obtener respuesta. Intenta nuevamente.'
        this.messages[msgIndex].streaming = false
      } finally {
        // Ensure streaming flag is cleared
        if (this.messages[msgIndex]?.streaming) {
          this.messages[msgIndex].streaming = false
        }
        this.loading = false
      }
    },

    _processStreamEvent(msgIndex, event) {
      const msg = this.messages[msgIndex]
      if (!msg) return

      switch (event.type) {
        case 'thought':
          msg.thought = (msg.thought || '') + (event.content || '')
          break
        case 'answer':
          msg.content = (msg.content || '') + (event.content || '')
          break
        case 'usage':
          if (event.data) {
            this.usage = {
              input_tokens: event.data.input_tokens ?? this.usage.input_tokens,
              output_tokens: event.data.output_tokens ?? this.usage.output_tokens,
              cost: event.data.cost ?? this.usage.cost
            }
          }
          break
        case 'done':
          msg.streaming = false
          break
      }
    },

    clearMessages() {
      this.messages = []
      this.usage = { input_tokens: 0, output_tokens: 0, cost: 0 }
    }
  }
})
