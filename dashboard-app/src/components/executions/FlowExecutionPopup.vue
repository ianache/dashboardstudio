<template>
  <div class="fep-overlay" @click.self="$emit('close')">
    <div class="fep-modal">
      <div class="fep-header">
        <div class="fep-header-left">
          <span class="msi" style="color: #2563eb; font-size: 24px">monitoring</span>
          <div>
            <h2 class="fep-title">{{ flowName || 'Flujo de Integración' }}</h2>
            <p class="fep-subtitle">ID de Ejecución: {{ executionId }}</p>
          </div>
        </div>
        <div class="fep-header-right">
          <div v-if="executionDetail" class="fep-status-badge" :class="`fep-status--${executionDetail.status}`">
            <span class="msi" style="font-size: 18px">{{ executionDetail.status === 'success' ? 'check_circle' : (executionDetail.status === 'error' ? 'cancel' : 'sync') }}</span>
            {{ executionDetail.status.toUpperCase() }}
          </div>
          <button class="fep-close-btn" @click="$emit('close')">
            <span class="msi">close</span>
          </button>
        </div>
      </div>

      <div class="fep-body">
        <div v-if="loading" class="fep-loading">
          <span class="msi spin" style="font-size: 32px">sync</span>
          <p>Cargando detalles de ejecución...</p>
        </div>
        <FlowEditorCanvas
          v-else-if="diagramData"
          readOnly
          :diagramType="'data-integration'"
          :diagramData="diagramData"
          :executionData="executionDetail"
          :tools="tools"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FlowEditorCanvas from '../editor/FlowEditorCanvas.vue'
import { integrationFlowsApi, editorToolsApi } from '@/services/api'

const props = defineProps({
  executionId: { type: String, required: true },
  flowName:    { type: String, default: '' },
  flowId:      { type: String, default: '' }
})

const emit = defineEmits(['close'])

const loading = ref(true)
const executionDetail = ref(null)
const diagramData = ref(null)
const tools = ref([])

onMounted(async () => {
  try {
    // 1. Fetch tools (needed for canvas)
    tools.value = await editorToolsApi.getForDiagram('data-integration')
    
    // 2. Fetch execution logs
    executionDetail.value = await integrationFlowsApi.getExecutionLogs(props.executionId)
    
    // 3. Fetch flow diagram
    const flowId = props.flowId || executionDetail.value.flow_id
    if (flowId) {
      const flow = await integrationFlowsApi.getById(flowId)
      // Correctly populate the diagram data for the canvas
      diagramData.value = {
        nodes: flow.flow_nodes || [],
        connections: flow.flow_connections || [],
        metadata: flow.flow_metadata || {}
      }
    }
  } catch (e) {
    console.error('[FlowExecutionPopup] Error loading data:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.fep-overlay {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px); z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 40px;
}

@media (max-width: 768px) {
  .fep-overlay {
    padding: 10px;
  }
}

.fep-modal {
  background: #fff; width: 100%; height: 100%; border-radius: 12px;
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.fep-header {
  padding: 16px 24px; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
  background: #fff;
  gap: 12px;
}

@media (max-width: 640px) {
  .fep-header {
    padding: 12px 16px;
  }
}

.fep-header-left { display: flex; align-items: center; gap: 16px; min-width: 0; }
.fep-title { 
  font-size: 18px; font-weight: 700; color: #1e293b; margin: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.fep-subtitle { font-size: 11px; color: #64748b; margin: 2px 0 0; font-family: monospace; }

.fep-header-right { display: flex; align-items: center; gap: 16px; }

.fep-status-badge {
  display: flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 20px; font-size: 11px; font-weight: 700;
}
.fep-status--success { background: #dcfce7; color: #16a34a; }
.fep-status--error   { background: #fee2e2; color: #dc2626; }
.fep-status--running { background: #eff6ff; color: #2563eb; }

.fep-close-btn {
  background: none; border: none; cursor: pointer; color: #94a3b8;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
  width: 32px; height: 32px; border-radius: 50%;
}
.fep-close-btn:hover { color: #475569; background: #f1f5f9; }

.fep-body { flex: 1; position: relative; background: #f1f5f9; }

.fep-loading {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px; color: #64748b;
}

.msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 20px; line-height: 1;
  letter-spacing: normal; text-transform: none; display: inline-flex;
  align-items: center; justify-content: center; white-space: nowrap;
  direction: ltr; -webkit-font-smoothing: antialiased; flex-shrink: 0;
}

.spin { animation: spin 2s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
</style>
