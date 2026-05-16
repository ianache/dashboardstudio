<template>
  <div class="fe-root">

    <!-- Top Bar -->
    <header class="fe-topbar">
      <div class="fe-topbar-l">
        <button class="fe-back-btn" @click="$router.push('/integrations')" title="Volver a Integrations">
          <span class="msi">arrow_back</span>
        </button>
        <div class="fe-topbar-sep"></div>
        <span class="msi" :style="{ color: diagramTypeDef?.color || '#2563eb' }" style="font-size:18px">{{ diagramTypeDef?.icon || 'schema' }}</span>
        <div>
          <p class="fe-flow-name">{{ diagramData.metadata?.name || flowName }}</p>
          <p class="fe-flow-type">{{ diagramTypeDef?.name || diagramTypeId }}</p>
        </div>
        <span class="fe-status-pill" :class="`fe-sp--${diagramData.metadata?.status || 'draft'}`">
          {{ STATUS_LABELS[diagramData.metadata?.status] || 'Draft' }}
        </span>
      </div>
      <div class="fe-topbar-r">
        <button
          class="fe-tbr-btn fe-tbr-btn--run"
          :disabled="loading || canvasRef?.execStatus === 'running'"
          @click="canvasRef?.runFlow()"
          :title="canvasRef?.execStatus === 'running' ? 'Ejecutando...' : 'Ejecutar Flujo'">
          <span class="msi" :class="{ 'spin': canvasRef?.execStatus === 'running' }">
            {{ canvasRef?.execStatus === 'running' ? 'sync' : 'play_arrow' }}
          </span>
          Ejecutar
        </button>
        <div class="fe-topbar-sep"></div>
        <button
          class="fe-tbr-btn fe-tbr-btn--ai"
          :disabled="loading"
          @click="showAiAssist = true"
          title="AI Code Assist">
          <span class="msi">auto_awesome</span>AI Assist
        </button>
        <button class="fe-tbr-btn" @click="canvasRef?.centerView()" title="Centrar diagrama" :disabled="loading">
          <span class="msi">center_focus_strong</span>
        </button>
        <button
          class="fe-tbr-btn fe-tbr-btn--save"
          :class="{ 'fe-tbr-btn--dirty': isDirty }"
          :disabled="loading || !isDirty"
          @click="handleSave"
          title="Guardar cambios">
          <span class="msi">save</span>Guardar
        </button>
        <button class="fe-tbr-btn fe-tbr-btn--primary" :disabled="loading">
          <span class="msi">rocket_launch</span>Publicar
        </button>
      </div>
    </header>

    <!-- Loading skeleton -->
    <div v-if="loading" class="fe-loading">
      <span class="msi fe-loading-icon">schema</span>
      <p class="fe-loading-txt">Cargando diagrama...</p>
    </div>

    <!-- Reusable Editor Canvas -->
    <FlowEditorCanvas
      v-else
      ref="canvasRef"
      class="fe-body"
      :diagram-type="diagramTypeId"
      :tools="toolsForDiagram"
      :diagram-data="diagramData"
      :flow-id="flowId"
      @dirty-change="isDirty = $event"
    />

    <!-- AI Code Assist modal -->
    <AiCodeAssist
      v-if="showAiAssist && !loading"
      :diagram-type-id="diagramTypeId"
      :diagram-type-name="diagramTypeDef?.name || diagramTypeId"
      :diagram-type-prompt="diagramTypeDef?.ai_assist_prompt || ''"
      :diagram-data="diagramData"
      @close="showAiAssist = false"
    />

    <!-- Unsaved changes — leave confirmation -->
    <ConfirmModal
      v-if="showLeaveModal"
      question="¿Salir sin guardar?"
      detail="Tienes cambios sin guardar en el diagrama. ¿Qué deseas hacer?"
      warning-icon="warning"
      cancel-label="Descartar y salir"
      cancel-icon="logout"
      accept-label="Guardar y salir"
      accept-icon="save"
      accept-variant="primary"
      @cancel="onLeaveDiscard"
      @accept="onLeaveSave"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { useToolCatalogStore } from '@/stores/toolCatalog'
import { useIntegrationsStore } from '@/stores/integrations'
import { useUIStore } from '@/stores/ui'
import FlowEditorCanvas from '@/components/editor/FlowEditorCanvas.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import AiCodeAssist from '@/components/editor/AiCodeAssist.vue'

const route     = useRoute()
const router    = useRouter()
const catalog   = useToolCatalogStore()
const flowStore = useIntegrationsStore()
const uiStore   = useUIStore()
const canvasRef = ref(null)
const loading      = ref(true)
const showAiAssist = ref(false)

const STATUS_LABELS = { active: 'Activo', scheduled: 'Programado', paused: 'Pausado', error: 'Error', draft: 'Draft' }

// ─── Dirty / unsaved changes ──────────────────────────────────────────────────
const isDirty         = ref(false)
const showLeaveModal  = ref(false)
let   pendingPath     = ''
let   allowLeave      = false

onBeforeRouteLeave((to) => {
  if (allowLeave || !isDirty.value) return true
  pendingPath = to.fullPath
  showLeaveModal.value = true
  return false
})

async function onLeaveDiscard() {
  showLeaveModal.value = false
  allowLeave = true
  router.push(pendingPath)
}

async function onLeaveSave() {
  try {
    await doSave()
    showLeaveModal.value = false
    allowLeave = true
    router.push(pendingPath)
  } catch {
    // error already alerted inside doSave
  }
}

// ─── Diagram type — driven by the flow loaded from backend ────────────────────
const diagramTypeId   = computed(() => flowStore.currentFlow?.diagram_type || '')
const diagramTypeDef  = computed(() => catalog.diagramTypeById(diagramTypeId.value))
const toolsForDiagram = computed(() => catalog.toolsForDiagram(diagramTypeId.value))

// ─── Flow data from backend ───────────────────────────────────────────────────
const flowId   = route.params.id
const flowName = computed(() => flowStore.currentFlow?.name || `Flujo ${flowId}`)

const diagramData = computed(() => {
  const f = flowStore.currentFlow
  if (!f) return { metadata: {}, nodes: [], connections: [] }
  return {
    metadata: {
      name: f.name, description: f.description, status: f.status,
      type: f.flow_type, cron_expression: f.cron_expression, log_level: f.log_level,
      source: f.source_system, target: f.target_system,
    },
    nodes:       f.flow_nodes?.length       ? f.flow_nodes       : [],
    connections: f.flow_connections?.length ? f.flow_connections : [],
  }
})

// ─── Save ─────────────────────────────────────────────────────────────────────
async function doSave() {
  const data = canvasRef.value?.getCurrentDiagramData()
  if (!data) return
  await flowStore.saveDiagram(flowId, { nodes: data.nodes, connections: data.connections, metadata: data.metadata })
  canvasRef.value?.markSaved()
  uiStore.addAlert({ type: 'success', message: 'Diagrama guardado exitosamente' })
}

async function handleSave() {
  try {
    await doSave()
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error al guardar: ' + err.message })
  }
}


// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await Promise.all([catalog.loadAll(), flowStore.loadById(flowId)])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.fe-root {
  position: fixed; inset: 0;
  display: flex; flex-direction: column;
  background: #f8fafc;
  font-family: 'Inter', system-ui, sans-serif;
  z-index: 200; overflow: hidden;
}

/* Top Bar */
.fe-topbar {
  height: 52px; background: #fff; border-bottom: 1px solid #e2e8f0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; flex-shrink: 0; z-index: 10;
  box-shadow: 0 1px 4px rgba(15,23,42,0.06);
}
.fe-topbar-l { display: flex; align-items: center; gap: 10px; }
.fe-topbar-r { display: flex; align-items: center; gap: 8px; }
.fe-back-btn {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  border: 1px solid #e2e8f0; border-radius: 7px; background: #fff; cursor: pointer;
  color: #475569; transition: all 0.15s;
}
.fe-back-btn:hover { background: #f1f5f9; }
.fe-topbar-sep { width: 1px; height: 20px; background: #e2e8f0; }
.fe-flow-name { font-size: 13px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; line-height: 1.2; }
.fe-flow-type { font-size: 10px; color: #94a3b8; }
.fe-status-pill { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.fe-sp--active    { background: #dcfce7; color: #16a34a; }
.fe-sp--scheduled { background: #dbeafe; color: #1d4ed8; }
.fe-sp--paused    { background: #f1f5f9; color: #64748b; }
.fe-sp--error     { background: #fee2e2; color: #dc2626; }
.fe-sp--draft     { background: #fef9c3; color: #854d0e; }
.fe-tbr-btn {
  display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 7px;
  font-size: 12px; font-weight: 500; cursor: pointer;
  border: 1px solid #e2e8f0; background: #fff; color: #475569; transition: all 0.15s;
}
.fe-tbr-btn:hover { background: #f8fafc; }
.fe-tbr-btn--primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.fe-tbr-btn--primary:hover { background: #1d4ed8; }

.fe-tbr-btn--run {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #16a34a;
  font-weight: 600;
}
.fe-tbr-btn--run:hover:not(:disabled) {
  background: #dcfce7;
  border-color: #86efac;
}
.fe-tbr-btn--run:disabled {
  opacity: 0.6;
}

.fe-tbr-btn--ai { background: linear-gradient(135deg, #7c3aed18, #2563eb18); border-color: #7c3aed44; color: #7c3aed; font-weight: 600; }

.spin { animation: fe-spin 2s linear infinite; }
@keyframes fe-spin { 100% { transform: rotate(360deg); } }
.fe-tbr-btn--ai:hover { background: linear-gradient(135deg, #7c3aed28, #2563eb28); }
.fe-tbr-btn--save:disabled { opacity: 0.38; cursor: default; }
.fe-tbr-btn--dirty { border-color: #f59e0b; color: #92400e; background: #fffbeb; }
.fe-tbr-btn--dirty:hover { background: #fef3c7; }

/* Body fills remaining height */
.fe-body { flex: 1; overflow: hidden; }

/* Loading */
.fe-loading {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  background: #f8fafc;
}
.fe-loading-icon { font-size: 40px; color: #cbd5e1; animation: fe-pulse 1.4s ease-in-out infinite; }
.fe-loading-txt  { font-size: 13px; color: #94a3b8; }
@keyframes fe-pulse { 0%,100%{opacity:.4} 50%{opacity:1} }
</style>
