<template>
  <aside class="ai-panel">
    <!-- HEADER -->
    <header class="ai-panel-header">
      <div class="ai-header-top">
        <div class="ai-identity">
          <div class="ai-avatar">
            <span class="material-symbols-outlined">psychology</span>
          </div>
          <div>
            <h1 class="ai-title">BI/AI Analyst</h1>
            <p class="ai-subtitle">Analista BI · Dashboard Studio</p>
          </div>
        </div>
        <div class="ai-header-btns">
          <!-- Model selector -->
          <div class="ai-model-selector">
            <button
              class="ai-icon-btn"
              title="Seleccionar modelo"
              @click.stop="showModelMenu = !showModelMenu"
            >
              <span class="material-symbols-outlined">settings</span>
            </button>
            <div v-if="showModelMenu" class="ai-model-menu">
              <div class="ai-model-menu-title">Modelo de IA</div>
              <button
                v-for="m in store.availableModels"
                :key="m.id"
                class="ai-model-option"
                :class="{ 'ai-model-option--active': store.selectedModel === m.id, 'ai-model-option--disabled': !m.enabled }"
                :disabled="!m.enabled"
                :title="m.enabled ? m.label : (m.disabled_reason || 'API key no configurada')"
                @click="selectModel(m.id)"
              >
                <span class="ai-model-option-label">{{ m.label }}</span>
                <span v-if="!m.enabled" class="ai-model-lock">
                  <span class="material-symbols-outlined" style="font-size:12px">lock</span>
                </span>
                <span v-if="store.selectedModel === m.id" class="ai-model-check">
                  <span class="material-symbols-outlined" style="font-size:14px">check</span>
                </span>
              </button>
            </div>
          </div>
          <button
            v-if="store.messages.length > 0"
            class="ai-icon-btn"
            title="Limpiar conversación"
            @click="store.clearMessages()"
          >
            <span class="material-symbols-outlined">delete_sweep</span>
          </button>
          <button class="ai-icon-btn" title="Cerrar" @click="store.togglePanel()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <div class="ai-divider"></div>

      <!-- Usage chips -->
      <div class="ai-chips">
        <div class="ai-chip">
          <span class="ai-chip-lbl">IN</span>
          <span class="ai-chip-val ai-chip-val--in">{{ formatTokens(store.usage.input_tokens) }}</span>
        </div>
        <div class="ai-chip">
          <span class="ai-chip-lbl">OUT</span>
          <span class="ai-chip-val ai-chip-val--out">{{ formatTokens(store.usage.output_tokens) }}</span>
        </div>
        <div v-if="store.usage.cache_hit > 0" class="ai-chip">
          <span class="ai-chip-lbl">CACHE</span>
          <span class="ai-chip-val ai-chip-val--cache">{{ store.usage.cache_hit.toFixed(0) }}%</span>
        </div>
        <div v-if="store.usage.cost > 0" class="ai-chip ai-chip--cost">
          <span class="ai-chip-lbl ai-chip-lbl--cost">COST</span>
          <span class="ai-chip-val ai-chip-val--cost">${{ store.usage.cost.toFixed(3) }}</span>
        </div>
      </div>

      <div class="ai-divider"></div>
    </header>

    <!-- MESSAGES -->
    <main ref="messagesContainer" class="ai-messages">
      <!-- Empty state -->
      <div v-if="store.messages.length === 0" class="ai-empty">
        <div class="ai-empty-icon-wrap">
          <span class="material-symbols-outlined">psychology</span>
        </div>
        <p class="ai-empty-title">BI/AI Analyst</p>
        <p class="ai-empty-hint">
          Hazme una pregunta sobre los datos de este dashboard. Analizo tendencias, explico métricas y sugiero insights.
        </p>
      </div>

      <!-- Date divider when there are messages -->
      <div v-else class="ai-date-row">
        <div class="ai-date-line"></div>
        <span class="ai-date-text">{{ todayLabel }}</span>
        <div class="ai-date-line"></div>
      </div>

      <AiAnalystMessage
        v-for="(msg, idx) in store.messages"
        :key="idx"
        :message="msg"
      />
    </main>

    <!-- FOOTER -->
    <footer class="ai-footer">
      <div class="ai-input-wrap" :class="{ 'ai-input-wrap--loading': store.loading }">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="ai-input"
          placeholder="Pregunta al BI Analyst..."
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
          <svg v-if="store.loading" class="ai-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span v-else class="material-symbols-outlined">play_arrow</span>
        </button>
      </div>
      <p class="ai-footer-hint">Enter para enviar · Shift+Enter para nueva línea</p>
    </footer>
  </aside>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { useAiAnalystStore } from '@/stores/aiAnalyst'
import AiAnalystMessage from '@/components/dashboard/AiAnalystMessage.vue'

const store = useAiAnalystStore()

const inputText = ref('')
const messagesContainer = ref(null)
const inputRef = ref(null)

const todayLabel = computed(() => {
  return new Date().toLocaleDateString('es-PE', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
})

function formatTokens(n) {
  if (!n) return '0'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
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

const showModelMenu = ref(false)

// Close model menu when clicking outside
function onDocClick(e) {
  if (!e.target.closest('.ai-model-selector')) {
    showModelMenu.value = false
  }
}

function selectModel(modelId) {
  store.switchModel(modelId)
  showModelMenu.value = false
}

function modelLabel(modelId) {
  const m = store.availableModels.find(m => m.id === modelId)
  return m ? m.label : modelId
}

onMounted(async () => {
  await store.fetchModels()
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<style scoped>
/* ── Design tokens (MD3 dark palette) ── */
.ai-panel {
  --c-surface:      #111319;
  --c-container:    #1d2026;
  --c-high:         #272a30;
  --c-low:          #191b22;
  --c-lowest:       #0c0e14;
  --c-outline-v:    #424753;
  --c-primary:      #adc6ff;
  --c-primary-c:    #0058bc;
  --c-on-primary:   #002e69;
  --c-on-primary-c: #c3d4ff;
  --c-secondary:    #b7c8e1;
  --c-secondary-c:  #3a4a5f;
  --c-tertiary:     #ffb595;
  --c-on-surface:   #e1e2eb;
  --c-on-sv:        #c2c6d5;

  width: 400px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--c-container);
  border-left: 1px solid var(--c-outline-v);
  flex-shrink: 0;
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--c-on-surface);
}

/* ── Header ── */
.ai-panel-header {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: rgba(39, 42, 48, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.ai-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
}

.ai-identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--c-primary-c);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-on-primary-c);
  box-shadow: 0 4px 12px rgba(173, 198, 255, 0.1);
  flex-shrink: 0;
}

.ai-avatar .material-symbols-outlined { font-size: 24px; }

.ai-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--c-primary);
  margin: 0;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.ai-subtitle {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--c-on-sv);
  opacity: 0.6;
  margin: 3px 0 0;
}

.ai-header-btns {
  display: flex;
  align-items: center;
  gap: 2px;
}

.ai-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: var(--c-on-sv);
  transition: background 0.15s, color 0.15s;
}

.ai-icon-btn:hover {
  background: var(--c-outline-v);
  color: var(--c-on-surface);
}

.ai-icon-btn .material-symbols-outlined { font-size: 20px; }

.ai-divider {
  height: 1px;
  background: rgba(66, 71, 83, 0.3);
}

/* ── Usage chips ── */
.ai-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  overflow-x: auto;
}

.ai-chips::-webkit-scrollbar { display: none; }

.ai-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--c-lowest);
  border: 1px solid rgba(66, 71, 83, 0.5);
  flex-shrink: 0;
}

.ai-chip--cost {
  background: rgba(173, 198, 255, 0.08);
  border-color: rgba(173, 198, 255, 0.2);
  margin-left: auto;
}

.ai-chip-lbl {
  font-size: 10px;
  font-weight: 700;
  color: var(--c-on-sv);
  opacity: 0.6;
  letter-spacing: 0.05em;
}

.ai-chip-lbl--cost { color: var(--c-primary); opacity: 0.8; }

.ai-chip-val {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 13px;
  line-height: 20px;
}

.ai-chip-val--in    { color: var(--c-primary); }
.ai-chip-val--out   { color: var(--c-secondary); }
.ai-chip-val--cache { color: var(--c-tertiary); }
.ai-chip-val--cost  { color: var(--c-primary); font-weight: 700; }

/* ── Messages ── */
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scroll-behavior: smooth;
  background: linear-gradient(to bottom, var(--c-container), var(--c-surface));
}

.ai-messages::-webkit-scrollbar { width: 4px; }
.ai-messages::-webkit-scrollbar-track { background: transparent; }
.ai-messages::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }

/* ── Empty state ── */
.ai-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 20px;
  margin: auto 0;
  gap: 10px;
}

.ai-empty-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(0, 88, 188, 0.2);
  border: 1px solid rgba(173, 198, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.ai-empty-icon-wrap .material-symbols-outlined {
  font-size: 32px;
  color: var(--c-primary);
}

.ai-empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--c-on-surface);
  margin: 0;
}

.ai-empty-hint {
  font-size: 13px;
  color: var(--c-on-sv);
  line-height: 1.6;
  margin: 0;
  opacity: 0.8;
}

/* ── Date divider ── */
.ai-date-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-date-line {
  flex: 1;
  height: 1px;
  background: rgba(66, 71, 83, 0.2);
}

.ai-date-text {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--c-on-sv);
  opacity: 0.4;
  white-space: nowrap;
}

/* ── Footer ── */
.ai-footer {
  padding: 12px 16px 14px;
  background: rgba(39, 42, 48, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--c-outline-v);
  flex-shrink: 0;
}

.ai-input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--c-lowest);
  border: 1px solid var(--c-outline-v);
  border-radius: 12px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ai-input-wrap:focus-within {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 1px rgba(173, 198, 255, 0.2);
}

.ai-input-wrap--loading { opacity: 0.6; }

.ai-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  color: var(--c-on-surface);
  background: transparent;
  max-height: 120px;
  overflow-y: auto;
  font-family: 'Inter', system-ui, sans-serif;
  min-height: 22px;
}

.ai-input::placeholder { color: rgba(194, 198, 213, 0.35); }
.ai-input:disabled { cursor: not-allowed; }

.ai-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  border: none;
  background: var(--c-primary);
  color: var(--c-on-primary);
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.1s, opacity 0.15s;
  box-shadow: 0 4px 12px rgba(173, 198, 255, 0.2);
}

.ai-send-btn:hover:not(:disabled) { transform: scale(1.05); }
.ai-send-btn:active:not(:disabled) { transform: scale(0.95); }
.ai-send-btn:disabled { opacity: 0.3; cursor: not-allowed; transform: none; }
.ai-send-btn .material-symbols-outlined { font-size: 20px; }

.ai-spin { animation: ai-spin-kf 0.8s linear infinite; }

@keyframes ai-spin-kf {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.ai-footer-hint {
  font-size: 10px;
  color: var(--c-on-sv);
  opacity: 0.35;
  text-align: center;
  margin: 8px 0 0;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

/* ── Model selector ── */
.ai-model-selector {
  position: relative;
}

.ai-model-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 200px;
  background: var(--c-container);
  border: 1px solid var(--c-outline-v);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 100;
  overflow: hidden;
}

.ai-model-menu-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--c-on-sv);
  opacity: 0.5;
  padding: 10px 12px 6px;
}

.ai-model-option {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--c-on-surface);
  font-size: 13px;
  font-family: 'Inter', system-ui, sans-serif;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
  gap: 6px;
}

.ai-model-option:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
}

.ai-model-option--active {
  color: var(--c-primary);
}

.ai-model-option--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-model-option-label { flex: 1; }
.ai-model-lock  { color: var(--c-on-sv); opacity: 0.5; }
.ai-model-check { color: var(--c-primary); margin-left: auto; }
</style>
