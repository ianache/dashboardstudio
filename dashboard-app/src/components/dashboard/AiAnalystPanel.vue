<template>
  <div class="ai-panel">
    <!-- Header -->
    <div class="ai-panel-header">
      <div class="ai-panel-title-row">
        <span class="material-symbols-outlined ai-panel-icon">auto_awesome</span>
        <span class="ai-panel-title">AI Analyst</span>
      </div>

      <div class="ai-panel-header-actions">
        <!-- Usage stats -->
        <div v-if="store.usage.input_tokens > 0 || store.usage.output_tokens > 0" class="ai-usage-stats">
          <span class="ai-usage-tokens ai-usage-tokens--in" title="Tokens de entrada">
            <span class="material-symbols-outlined ai-stat-icon">arrow_downward</span>{{ formatTokens(store.usage.input_tokens) }}
          </span>
          <span class="ai-usage-tokens ai-usage-tokens--out" title="Tokens de salida">
            <span class="material-symbols-outlined ai-stat-icon">arrow_upward</span>{{ formatTokens(store.usage.output_tokens) }}
          </span>
          <span v-if="store.usage.cache_hit > 0" class="ai-usage-cache" title="Cache hit %">
            <span class="material-symbols-outlined ai-stat-icon">cached</span>{{ store.usage.cache_hit.toFixed(0) }}%
          </span>
          <span v-if="store.usage.cost > 0" class="ai-usage-cost">
            ${{ store.usage.cost.toFixed(4) }}
          </span>
        </div>

        <!-- Clear button -->
        <button
          v-if="store.messages.length > 0"
          class="ai-panel-btn"
          title="Limpiar conversación"
          @click="store.clearMessages()"
        >
          <span class="material-symbols-outlined">delete_sweep</span>
        </button>

        <!-- Close button -->
        <button class="ai-panel-btn" title="Cerrar" @click="store.togglePanel()">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
    </div>

    <!-- Messages list -->
    <div ref="messagesContainer" class="ai-panel-messages">
      <!-- Empty state -->
      <div v-if="store.messages.length === 0" class="ai-empty-state">
        <span class="material-symbols-outlined ai-empty-icon">psychology_alt</span>
        <p class="ai-empty-title">Analista BI</p>
        <p class="ai-empty-hint">Hazme una pregunta sobre los datos de este dashboard. Puedo analizar tendencias, explicar métricas y sugerir insights.</p>
      </div>

      <!-- Message list -->
      <AiAnalystMessage
        v-for="(msg, idx) in store.messages"
        :key="idx"
        :message="msg"
      />
    </div>

    <!-- Footer / Input -->
    <div class="ai-panel-footer">
      <div class="ai-input-row" :class="{ 'ai-input-row--loading': store.loading }">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="ai-input"
          placeholder="Escribe una pregunta..."
          rows="1"
          :disabled="store.loading"
          @keydown.enter.exact.prevent="send"
          @input="autoResize"
        ></textarea>
        <button
          class="ai-send-btn"
          :disabled="store.loading || !inputText.trim()"
          title="Enviar"
          @click="send"
        >
          <svg v-if="store.loading" class="ai-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span v-else class="material-symbols-outlined">send</span>
        </button>
      </div>
      <p class="ai-input-hint">Enter para enviar · Shift+Enter para nueva línea</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useAiAnalystStore } from '@/stores/aiAnalyst'
import AiAnalystMessage from '@/components/dashboard/AiAnalystMessage.vue'

const store = useAiAnalystStore()

const inputText = ref('')
const messagesContainer = ref(null)
const inputRef = ref(null)

function formatTokens(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k tokens'
  return n + ' tokens'
}

async function send() {
  const text = inputText.value.trim()
  if (!text || store.loading) return
  inputText.value = ''
  await nextTick()
  autoResize()
  store.sendMessage(text)
}

function autoResize() {
  if (!inputRef.value) return
  inputRef.value.style.height = 'auto'
  inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px'
}

// Auto-scroll to bottom when new messages arrive or content streams in
watch(
  () => store.messages.map(m => m.content + m.thought),
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  },
  { deep: false }
)
</script>

<style scoped>
.ai-panel {
  width: 380px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  flex-shrink: 0;
}

/* Header */
.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8faff, #fdf4ff);
  flex-shrink: 0;
}

.ai-panel-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-panel-icon {
  font-size: 20px;
  color: #6366f1;
}

.ai-panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.ai-panel-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Usage stats */
.ai-usage-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;
}

.ai-usage-tokens {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 10px;
  font-family: ui-monospace, monospace;
}

.ai-usage-cost {
  font-size: 11px;
  font-weight: 500;
  color: #059669;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 10px;
  font-family: ui-monospace, monospace;
}

.ai-usage-tokens--in { color: #0369a1; background: #e0f2fe; }
.ai-usage-tokens--out { color: #7c3aed; background: #ede9fe; }

.ai-usage-cache {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 500;
  color: #b45309;
  background: #fef3c7;
  padding: 2px 6px;
  border-radius: 10px;
  font-family: ui-monospace, monospace;
}

.ai-stat-icon {
  font-size: 10px;
  vertical-align: middle;
}

.ai-panel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
}

.ai-panel-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.ai-panel-btn .material-symbols-outlined { font-size: 18px; }

/* Messages area */
.ai-panel-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}

.ai-panel-messages::-webkit-scrollbar { width: 4px; }
.ai-panel-messages::-webkit-scrollbar-track { background: transparent; }
.ai-panel-messages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }

/* Empty state */
.ai-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 16px;
  margin: auto 0;
  gap: 8px;
}

.ai-empty-icon {
  font-size: 48px;
  color: #c7d2fe;
  margin-bottom: 4px;
}

.ai-empty-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.ai-empty-hint {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}

/* Footer / Input */
.ai-panel-footer {
  padding: 10px 12px 12px;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
  background: #fafafa;
}

.ai-input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 6px 8px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ai-input-row:focus-within {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.ai-input-row--loading {
  opacity: 0.75;
}

.ai-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  color: #0f172a;
  background: transparent;
  max-height: 120px;
  overflow-y: auto;
  font-family: inherit;
  min-height: 24px;
}

.ai-input::placeholder { color: #94a3b8; }
.ai-input:disabled { cursor: not-allowed; }

.ai-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}

.ai-send-btn:hover:not(:disabled) {
  opacity: 0.85;
  transform: translateY(-1px);
}

.ai-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.ai-send-btn .material-symbols-outlined { font-size: 16px; }

.ai-spin {
  animation: ai-spin-kf 0.8s linear infinite;
}

@keyframes ai-spin-kf {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.ai-input-hint {
  font-size: 11px;
  color: #94a3b8;
  margin: 6px 0 0;
  text-align: center;
}
</style>
