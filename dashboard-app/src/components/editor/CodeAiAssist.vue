<template>
  <Teleport to="body">
    <div class="aaa-floating-bar" :class="{ 'aaa-floating-bar--expanded': result || loading }">
      
      <!-- ── Input Row ─────────────────────────────────────────── -->
      <div class="aaa-input-row">
        <div class="aaa-hdr-ico">
          <span class="aaa-msi">auto_awesome</span>
        </div>
        
        <div class="aaa-prompt-wrap">
          <textarea 
            ref="textareaRef"
            v-model="userPrompt" 
            class="aaa-input" 
            placeholder="¿Qué quieres programar? Ej: Calcular el IVA..."
            rows="1"
            @input="adjustTextareaHeight"
            @keydown.enter.exact.prevent="generate"
            autofocus
          ></textarea>
        </div>

        <div class="aaa-lang-selector">
          <select v-model="selectedLang" class="aaa-select">
            <option value="javascript">JS</option>
            <option value="python">PY</option>
            <option value="typescript">TS</option>
          </select>
        </div>

        <div class="aaa-actions">
          <button class="aaa-btn-generate" :disabled="loading || !userPrompt.trim()" @click="generate">
            <svg v-if="loading" class="aaa-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            <span v-else class="aaa-msi" style="font-size:16px">send</span>
          </button>
          
          <div class="aaa-sep"></div>
          
          <button class="aaa-close-btn" @click="$emit('close')" title="Cerrar asistente">
            <span class="aaa-msi">close</span>
          </button>
        </div>
      </div>

      <!-- ── Result Area (Expanded) ────────────────────────────── -->
      <div v-if="loading || result || error" class="aaa-expanded-content">
        <!-- Error -->
        <div v-if="error" class="aaa-error-msg">
          <span class="aaa-msi" style="font-size:16px">error</span>
          {{ error }}
        </div>

        <!-- Loading -->
        <div v-if="loading" class="aaa-loading-state">
          <div class="aaa-shimmer"></div>
          <span>Generando código con {{ modelCfg?.modelLabel }}...</span>
        </div>

        <!-- Result -->
        <div v-else-if="result" class="aaa-result-container">
          <div class="aaa-result-header">
            <span class="aaa-filename">generated_code.{{ extMap[selectedLang] }}</span>
            <div class="aaa-result-actions">
              <button class="aaa-apply-btn" @click="applyCode">
                <span class="aaa-msi">check</span> Aplicar
              </button>
            </div>
          </div>
          <div class="aaa-code-preview">
            <pre><code>{{ result }}</code></pre>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'

const props = defineProps({
  initialLanguage: { type: String, default: 'javascript' },
  context:         { type: String, default: '' },
})
const emit = defineEmits(['close', 'apply'])

const llmStore = useLlmStore()
const modelCfg = computed(() => llmStore.isConfigured ? llmStore.configFor('codeAssist') : null)

const selectedLang = ref(props.initialLanguage)
const userPrompt   = ref('')
const loading      = ref(false)
const error        = ref('')
const result       = ref('')
const textareaRef  = ref(null)

const extMap = {
  javascript: 'js',
  python: 'py',
  typescript: 'ts'
}

async function generate() {
  if (!userPrompt.value.trim()) return
  if (!modelCfg.value) {
    error.value = 'Sin proveedor LLM configurado. Ve a Configuración → LLM para agregar una API Key.'
    return
  }
  loading.value = true
  error.value   = ''
  result.value  = ''

  try {
    const cfg = modelCfg.value
    const systemPrompt = `Eres un asistente experto en programación. Tu tarea es generar código funcional en el lenguaje ${selectedLang.value}.
Genera SOLO el código solicitado, sin explicaciones ni bloques de texto adicionales.
Si el usuario proporciona código existente, úsalo como contexto para tu respuesta.`

    const userMsg = `Lenguaje: ${selectedLang.value}\n\nRequerimiento: ${userPrompt.value}\n\nCódigo actual:\n\`\`\`${selectedLang.value}\n${props.context}\n\`\`\``

    const raw = await callLlm({
      provider:  cfg.provider,
      modelId:   cfg.modelId,
      apiKey:    cfg.apiKey,
      prompt:    `${systemPrompt}\n\n${userMsg}`,
      maxTokens: 4096,
    })

    result.value = raw.replace(/```[a-z]*\n/gi, '').replace(/```/g, '').trim()
  } catch (err) {
    error.value = err.message || 'Error al generar'
  } finally {
    loading.value = false
  }
}

function applyCode() {
  emit('apply', result.value)
  emit('close')
}

function adjustTextareaHeight() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}
</script>

<style scoped>
.aaa-msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 20px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
}

.aaa-floating-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  width: 100%;
  max-width: 800px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: aaa-slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  pointer-events: auto;
}

@keyframes aaa-slide-up {
  from { transform: translate(-50%, 40px); opacity: 0; }
  to { transform: translate(-50%, 0); opacity: 1; }
}

.aaa-input-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 10px 12px;
  min-height: 52px;
}

.aaa-hdr-ico {
  width: 32px; height: 32px; border-radius: 10px;
  background: linear-gradient(135deg, #059669, #10b981);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  margin-bottom: 2px;
}
.aaa-hdr-ico .aaa-msi { color: #fff; font-size: 18px; }

.aaa-prompt-wrap { flex: 1; min-width: 0; padding: 4px 0; }
.aaa-input {
  width: 100%; border: none; background: transparent;
  font-size: 14px; font-weight: 500; color: #1e293b;
  outline: none; padding: 0;
  resize: none;
  display: block;
  max-height: 200px;
  line-height: 1.5;
  font-family: inherit;
}
.aaa-input::placeholder { color: #94a3b8; }

.aaa-lang-selector { flex-shrink: 0; margin-bottom: 4px; }
.aaa-select {
  border: 1px solid #e2e8f0; background: #f8fafc;
  border-radius: 8px; font-size: 11px; font-weight: 700;
  padding: 4px 8px; color: #64748b; outline: none;
  cursor: pointer; transition: all 0.2s;
}
.aaa-select:hover { border-color: #cbd5e1; background: #f1f5f9; }

.aaa-actions { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.aaa-btn-generate {
  width: 32px; height: 32px; border-radius: 8px;
  background: #059669; color: #fff; border: none;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.aaa-btn-generate:hover:not(:disabled) { background: #047857; transform: scale(1.05); }
.aaa-btn-generate:disabled { opacity: 0.5; cursor: default; }

.aaa-sep { width: 1px; height: 20px; background: #e2e8f0; margin: 0 4px; }

.aaa-close-btn {
  width: 28px; height: 28px; border-radius: 50%;
  border: none; background: transparent; color: #94a3b8;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.aaa-close-btn:hover { background: #f1f5f9; color: #475569; }

/* Expanded Content */
.aaa-expanded-content {
  border-top: 1px solid #f1f5f9;
  background: #fcfcfc;
  max-height: 70vh;
  overflow-y: auto;
}

.aaa-error-msg {
  padding: 12px 16px; color: #dc2626; font-size: 13px;
  display: flex; align-items: center; gap: 8px;
  background: #fef2f2;
}

.aaa-loading-state {
  padding: 24px; display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: #64748b; font-size: 13px; font-weight: 500;
}
.aaa-shimmer {
  width: 100%; height: 4px; background: #f1f5f9; border-radius: 2px;
  position: relative; overflow: hidden;
}
.aaa-shimmer::after {
  content: ''; position: absolute; top: 0; left: 0; width: 40%; height: 100%;
  background: linear-gradient(90deg, transparent, #10b981, transparent);
  animation: aaa-shimmer-anim 1.5s infinite;
}
@keyframes aaa-shimmer-anim { from { left: -40%; } to { left: 100%; } }

.aaa-result-container { display: flex; flex-direction: column; }
.aaa-result-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 16px; background: #fff; border-bottom: 1px solid #f1f5f9;
}
.aaa-filename { font-size: 12px; font-weight: 700; color: #64748b; font-family: monospace; }
.aaa-apply-btn {
  display: flex; align-items: center; gap: 6px; padding: 6px 14px;
  background: #059669; color: #fff; border: none; border-radius: 8px;
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
}
.aaa-apply-btn:hover { background: #047857; }

.aaa-code-preview { background: #0f172a; padding: 16px; }
.aaa-code-preview pre { 
  margin: 0; 
  color: #e2e8f0; 
  font-family: monospace; 
  font-size: 12px; 
  line-height: 1.5; 
  tab-size: 2;
  white-space: pre-wrap;
  word-break: break-all;
}

.aaa-spin { animation: aaa-rotate 0.8s linear infinite; }
@keyframes aaa-rotate { to { transform: rotate(360deg) } }

/* Global tweak to ensure parent doesn't capture clicks if needed, 
   but since we Teleport to body it's fine. */
</style>