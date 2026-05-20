<template>
  <Teleport to="body">
    <div class="aca-overlay">
      <div class="aca-modal">

        <!-- ── Header ─────────────────────────────────────────────── -->
        <div class="aca-header">
          <div class="aca-header-l">
            <div class="aca-hdr-ico">
              <span class="aca-msi">auto_awesome</span>
            </div>
            <div>
              <h2 class="aca-title">AI Code Assist</h2>
              <p class="aca-subtitle">
                {{ diagramTypeName || 'Diagrama' }}
                <span v-if="modelCfg" class="aca-model-pill">
                  {{ modelCfg.providerLabel }} · {{ modelCfg.modelLabel }}
                </span>
              </p>
            </div>
          </div>
          <button class="aca-icon-btn" @click="$emit('close')" title="Cerrar">
            <span class="aca-msi">close</span>
          </button>
        </div>

        <!-- ── Body ──────────────────────────────────────────────── -->
        <div class="aca-body">

          <!-- Not configured -->
          <div v-if="!llmStore.isConfigured" class="aca-state-box aca-state-box--warn">
            <span class="aca-msi" style="font-size:28px;color:#d97706">warning</span>
            <p class="aca-state-title">Sin proveedor LLM configurado</p>
            <p class="aca-state-desc">Configura una API Key en <strong>Configuración → LLM</strong> para usar el AI Code Assist.</p>
          </div>

          <!-- No prompt for this diagram type -->
          <div v-else-if="!diagramTypePrompt" class="aca-state-box aca-state-box--info">
            <span class="aca-msi" style="font-size:28px;color:#2563eb">info</span>
            <p class="aca-state-title">Prompt no configurado</p>
            <p class="aca-state-desc">Este tipo de diagrama no tiene un prompt de AI Assist definido. Edítalo en <strong>Tipos de Diagrama</strong>.</p>
          </div>

          <template v-else>
            <!-- Action bar -->
            <div class="aca-action-bar">
              <button class="aca-btn-generate" :disabled="loading" @click="generate">
                <svg v-if="loading" class="aca-spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
                <span v-else class="aca-msi" style="font-size:17px">play_circle</span>
                {{ loading ? 'Generando...' : (result ? 'Regenerar' : 'Generar código') }}
              </button>

              <div v-if="result && !loading" class="aca-action-meta">
                <span class="aca-msi" style="font-size:14px;color:#16a34a">check_circle</span>
                <span>{{ result.artifacts?.length || 0 }} artefacto(s) generado(s)</span>
              </div>
            </div>

            <!-- Error -->
            <div v-if="error" class="aca-error-bar">
              <span class="aca-msi" style="font-size:16px;color:#dc2626">error</span>
              {{ error }}
            </div>

            <!-- Loading skeleton -->
            <div v-if="loading" class="aca-loading-wrap">
              <div class="aca-skeleton" v-for="i in 3" :key="i" :style="{ animationDelay: `${i * 0.12}s`, width: ['90%','70%','80%'][i-1] }"></div>
              <div class="aca-skeleton-block"></div>
            </div>

            <!-- Result form -->
            <div v-else-if="result" class="aca-result">
              <div class="aca-result-hdr">
                <p class="aca-result-title">{{ result.title }}</p>
                <p v-if="result.description" class="aca-result-desc">{{ result.description }}</p>
              </div>

              <div class="aca-artifacts">
                <div v-for="(artifact, idx) in result.artifacts" :key="idx" class="aca-artifact">
                  <!-- Artifact header -->
                  <div class="aca-artifact-hdr">
                    <div class="aca-artifact-hdr-l">
                      <span class="aca-msi" style="font-size:15px;color:#475569">{{ langIcon(artifact.language) }}</span>
                      <span class="aca-filename">{{ artifact.filename }}</span>
                      <span class="aca-lang-badge" :style="langStyle(artifact.language)">{{ artifact.language }}</span>
                    </div>
                    <button
                      class="aca-copy-btn"
                      :class="{ 'aca-copy-btn--done': copiedIdx === idx }"
                      @click="copyArtifact(artifact.code, idx)"
                      :title="copiedIdx === idx ? 'Copiado' : 'Copiar código'">
                      <span class="aca-msi" style="font-size:15px">{{ copiedIdx === idx ? 'check' : 'content_copy' }}</span>
                      {{ copiedIdx === idx ? 'Copiado' : 'Copiar' }}
                    </button>
                  </div>

                  <!-- Description -->
                  <p v-if="artifact.description" class="aca-artifact-desc">{{ artifact.description }}</p>

                  <!-- Code block (collapsible) -->
                  <div class="aca-code-wrap" :class="{ 'aca-code-wrap--collapsed': collapsed[idx] }">
                    <pre class="aca-pre"><code>{{ artifact.code }}</code></pre>
                  </div>

                  <button class="aca-collapse-btn" @click="collapsed[idx] = !collapsed[idx]">
                    <span class="aca-msi" style="font-size:14px">{{ collapsed[idx] ? 'expand_more' : 'expand_less' }}</span>
                    {{ collapsed[idx] ? 'Ver código' : 'Colapsar' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else class="aca-state-box">
              <span class="aca-msi" style="font-size:36px;color:#cbd5e1">auto_awesome</span>
              <p class="aca-state-title">Listo para generar</p>
              <p class="aca-state-desc">
                Haz clic en <strong>Generar código</strong> para que el asistente analice el diagrama
                ({{ nodeCount }} nodo(s), {{ connCount }} conexión(es)) y produzca los artefactos correspondientes.
              </p>
            </div>
          </template>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'

const props = defineProps({
  diagramTypeId:     { type: String, required: true },
  diagramTypeName:   { type: String, default: '' },
  diagramTypePrompt: { type: String, default: '' },
  diagramData:       { type: Object, default: () => ({ nodes: [], connections: [], metadata: {} }) },
})
defineEmits(['close'])

const llmStore = useLlmStore()
const modelCfg = computed(() => llmStore.isConfigured ? llmStore.configFor('modelAssist') : null)

const nodeCount = computed(() => props.diagramData?.nodes?.length ?? 0)
const connCount = computed(() => props.diagramData?.connections?.length ?? 0)

// ─── State ───────────────────────────────────────────────────────────────────
const loading   = ref(false)
const error     = ref('')
const result    = ref(null)    // { title, description, artifacts: [{filename, language, description, code}] }
const copiedIdx = ref(-1)
const collapsed = reactive({}) // idx → boolean

// ─── Generate ────────────────────────────────────────────────────────────────
async function generate() {
  if (!modelCfg.value || !props.diagramTypePrompt) return
  loading.value = true
  error.value   = ''
  result.value  = null
  Object.keys(collapsed).forEach(k => delete collapsed[k])

  try {
    const cfg = modelCfg.value
    const ctx  = JSON.stringify(props.diagramData, null, 2)
    const userMsg = (
      `A continuación la definición completa del diagrama "${props.diagramTypeName}" en formato JSON:\n\n` +
      `\`\`\`json\n${ctx}\n\`\`\`\n\n` +
      `Genera el código o activos correspondientes siguiendo las instrucciones del sistema.`
    )

    const fullPrompt = `${props.diagramTypePrompt}\n\n${userMsg}`
    const raw = await callLlm({
      provider:  cfg.provider,
      modelId:   cfg.modelId,
      apiKey:    cfg.apiKey,
      prompt:    fullPrompt,
      maxTokens: 16384,
    })

    result.value = parseResult(raw)
    // Default: first artifact collapsed = false, rest collapsed
    result.value.artifacts?.forEach((_, i) => { collapsed[i] = i > 0 })
  } catch (err) {
    error.value = err.message || 'Error al generar el código'
  } finally {
    loading.value = false
  }
}

// ─── Parse JSON result from LLM ──────────────────────────────────────────────
function parseResult(raw) {
  const attempts = [
    () => JSON.parse(raw.trim()),
    () => {
      const m = raw.match(/```(?:json)?\s*([\s\S]*?)(?:```|$)/i)
      return JSON.parse(m ? m[1].trim() : raw)
    },
    () => {
      const s = raw.indexOf('{'), e = raw.lastIndexOf('}')
      return JSON.parse(raw.slice(s, e + 1))
    },
  ]
  for (const attempt of attempts) {
    try {
      const p = attempt()
      if (p && (p.artifacts || p.title)) return p
    } catch {}
  }
  // Fallback: treat raw text as single artifact
  return {
    title: 'Resultado generado',
    description: '',
    artifacts: [{ filename: 'output.txt', language: 'text', description: '', code: raw }],
  }
}

// ─── Copy ─────────────────────────────────────────────────────────────────────
async function copyArtifact(code, idx) {
  try {
    await navigator.clipboard.writeText(code)
    copiedIdx.value = idx
    setTimeout(() => { copiedIdx.value = -1 }, 2000)
  } catch {}
}

// ─── Lang helpers ─────────────────────────────────────────────────────────────
const LANG_META = {
  python:   { icon: 'code',         color: '#3b82f6', bg: '#eff6ff' },
  xml:      { icon: 'code_blocks',  color: '#f59e0b', bg: '#fffbeb' },
  yaml:     { icon: 'data_object',  color: '#8b5cf6', bg: '#f5f3ff' },
  json:     { icon: 'data_object',  color: '#10b981', bg: '#f0fdf4' },
  sql:      { icon: 'table',        color: '#0891b2', bg: '#ecfeff' },
  markdown: { icon: 'article',      color: '#64748b', bg: '#f8fafc' },
  text:     { icon: 'notes',        color: '#94a3b8', bg: '#f8fafc' },
}
function langIcon(lang) { return LANG_META[lang?.toLowerCase()]?.icon || 'code' }
function langStyle(lang) {
  const m = LANG_META[lang?.toLowerCase()] || LANG_META.text
  return { background: m.bg, color: m.color }
}
</script>

<style scoped>
.aca-msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 20px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased; flex-shrink: 0;
}

/* Overlay — non-blocking panel anchored to the right, below topbar */
.aca-overlay {
  position: fixed;
  top: 52px; right: 12px; bottom: 12px;
  width: 800px; max-width: calc(100vw - 24px);
  z-index: 500;
  pointer-events: none;
  display: flex; align-items: flex-start; justify-content: flex-end;
  animation: aca-fade 0.15s ease;
}
@keyframes aca-fade { from { opacity: 0 } to { opacity: 1 } }

/* Modal */
.aca-modal {
  pointer-events: auto;
  background: #fff; border-radius: 14px;
  box-shadow: 0 32px 64px -12px rgba(0,0,0,0.3);
  width: 100%;
  height: 100%;
  display: flex; flex-direction: column;
  overflow: hidden;
  animation: aca-slide 0.18s ease;
}
@keyframes aca-slide { from { transform: translateX(16px); opacity: 0 } to { transform: none; opacity: 1 } }

/* Header */
.aca-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}
.aca-header-l { display: flex; align-items: center; gap: 12px; }
.aca-hdr-ico {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, #7c3aed, #2563eb);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.aca-hdr-ico .aca-msi { color: #fff; font-size: 18px; }
.aca-title { font-size: 15px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; margin: 0; }
.aca-subtitle { font-size: 12px; color: #64748b; margin: 2px 0 0; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.aca-model-pill {
  display: inline-block; padding: 1px 7px;
  background: #f1f5f9; border-radius: 20px;
  font-size: 10px; font-weight: 600; color: #475569;
}
.aca-icon-btn {
  width: 30px; height: 30px; border-radius: 7px; border: none; background: transparent;
  cursor: pointer; color: #64748b; display: flex; align-items: center; justify-content: center;
  transition: all 0.12s;
}
.aca-icon-btn:hover { background: #f1f5f9; color: #334155; }

/* Body */
.aca-body {
  flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px;
}
.aca-body::-webkit-scrollbar { width: 5px; }
.aca-body::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 3px; }

/* State boxes */
.aca-state-box {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 40px 24px; text-align: center;
  border-radius: 10px; background: #f8fafc;
  border: 1px dashed #e2e8f0;
}
.aca-state-box--warn { background: #fffbeb; border-color: #fde68a; }
.aca-state-box--info { background: #eff6ff; border-color: #bfdbfe; }
.aca-state-title { font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; }
.aca-state-desc  { font-size: 13px; color: #64748b; margin: 0; max-width: 380px; line-height: 1.6; }

/* Action bar */
.aca-action-bar { display: flex; align-items: center; gap: 12px; }
.aca-btn-generate {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 18px; border-radius: 8px;
  background: linear-gradient(135deg, #7c3aed, #2563eb); color: #fff;
  border: none; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: opacity 0.15s, transform 0.1s; font-family: inherit;
}
.aca-btn-generate:hover:not(:disabled) { opacity: 0.88; transform: translateY(-1px); }
.aca-btn-generate:disabled { opacity: 0.5; cursor: default; transform: none; }
.aca-action-meta { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #16a34a; }

/* Error */
.aca-error-bar {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 10px 14px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 8px; font-size: 13px; color: #dc2626;
}

/* Loading skeleton */
.aca-loading-wrap { display: flex; flex-direction: column; gap: 10px; }
.aca-skeleton {
  height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: aca-shimmer 1.4s infinite;
}
.aca-skeleton-block {
  height: 140px; border-radius: 8px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: aca-shimmer 1.4s infinite 0.2s;
}
@keyframes aca-shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Spin */
.aca-spin { animation: aca-rotate 0.8s linear infinite; flex-shrink: 0; }
@keyframes aca-rotate { to { transform: rotate(360deg) } }

/* Result */
.aca-result { display: flex; flex-direction: column; gap: 16px; }
.aca-result-hdr { padding: 12px 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.aca-result-title { font-size: 14px; font-weight: 700; color: #0f172a; margin: 0 0 4px; font-family: 'Plus Jakarta Sans', sans-serif; }
.aca-result-desc  { font-size: 12px; color: #64748b; margin: 0; }

/* Artifacts */
.aca-artifacts { display: flex; flex-direction: column; gap: 12px; }
.aca-artifact {
  border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;
  background: #fff;
}
.aca-artifact-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: #f8fafc; border-bottom: 1px solid #f1f5f9;
}
.aca-artifact-hdr-l { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.aca-filename {
  font-size: 13px; font-weight: 600; color: #1e293b;
  font-family: 'Fira Code', 'Consolas', monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.aca-lang-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 10px; font-weight: 700; flex-shrink: 0;
}
.aca-copy-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px; border-radius: 6px; border: 1px solid #e2e8f0;
  background: #fff; font-size: 11px; font-weight: 500; cursor: pointer;
  color: #475569; transition: all 0.15s; flex-shrink: 0; font-family: inherit;
}
.aca-copy-btn:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.aca-copy-btn--done { border-color: #16a34a; color: #16a34a; background: #f0fdf4; }

.aca-artifact-desc {
  font-size: 12px; color: #64748b; margin: 0;
  padding: 8px 14px; border-bottom: 1px solid #f1f5f9;
}

.aca-code-wrap { max-height: 320px; overflow-y: auto; transition: max-height 0.25s ease; }
.aca-code-wrap--collapsed { max-height: 0; overflow: hidden; }
.aca-code-wrap::-webkit-scrollbar { width: 5px; height: 5px; }
.aca-code-wrap::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 3px; }

.aca-pre {
  margin: 0; padding: 14px 16px;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 11.5px; line-height: 1.65;
  background: #0f172a; color: #e2e8f0;
  overflow-x: auto; white-space: pre;
  tab-size: 2;
}

.aca-collapse-btn {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  width: 100%; padding: 6px; border: none; background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  font-size: 11px; font-weight: 500; color: #64748b;
  cursor: pointer; transition: background 0.12s; font-family: inherit;
}
.aca-collapse-btn:hover { background: #f1f5f9; color: #334155; }
</style>
