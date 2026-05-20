<template>
  <div class="execution-history-panel">
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Estado</th>
            <th>Inicio</th>
            <th>Duración</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="history.length === 0">
            <td colspan="4" class="text-center py-4 text-slate-500">No hay ejecuciones registradas.</td>
          </tr>
          <tr v-for="ex in history" :key="ex.id" :class="{ 'selected': selectedExec?.id === ex.id }">
            <td><span :class="['badge', ex.status]">{{ ex.status }}</span></td>
            <td>{{ ex.start_time ? new Date(ex.start_time).toLocaleString() : new Date(ex.created_at).toLocaleString() }}</td>
            <td>{{ ex.duration || ex.duration_ms || 0 }} ms</td>
            <td class="actions-cell">
              <button class="btn-icon" @click="selectExecution(ex)" title="Ver detalles">
                <span class="material-symbols-outlined">description</span>
              </button>
              <button class="btn-icon" @click="showGraph(ex)" title="Ver gráfico">
                <span class="material-symbols-outlined">search</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="selectedExec" class="detail-panel">
      <div class="detail-hdr">
        <span class="msi material-symbols-outlined">analytics</span>
        <h3>Detalle de Nodos (ID: {{ selectedExec.id }})</h3>
      </div>
      
      <div v-for="(log, idx) in selectedExec.node_logs" :key="log.node_id + '-' + idx" class="node-log">
        <div class="node-log-header">
          <div class="node-info">
            <span class="msi material-symbols-outlined node-icon">terminal</span>
            <strong>{{ log.node_title || ('Nodo: ' + log.node_id) }}</strong>
          </div>
          <span :class="['badge', log.status]">{{ log.status === 'success' ? 'Completado' : 'Fallido' }}</span>
        </div>

        <div class="node-timing-grid">
          <div class="timing-item">
            <span class="msi material-symbols-outlined">play_arrow</span>
            <div>
              <label>Inicio</label>
              <span>{{ log.start_time ? new Date(log.start_time).toLocaleString() : '—' }}</span>
            </div>
          </div>
          <div class="timing-item">
            <span class="msi material-symbols-outlined">stop</span>
            <div>
              <label>Fin</label>
              <span>{{ log.end_time ? new Date(log.end_time).toLocaleString() : '—' }}</span>
            </div>
          </div>
          <div class="timing-item">
            <span class="msi material-symbols-outlined">timer</span>
            <div>
              <label>Duración</label>
              <span>{{ log.duration || 0 }} ms</span>
            </div>
          </div>
        </div>

        <div class="log-grid">
          <div>
            <div class="payload-hdr">
              <span class="msi material-symbols-outlined">input</span>
              <small>Input Payload:</small>
            </div>
            <pre>{{ JSON.stringify(log.input_data, null, 2) }}</pre>
          </div>
          <div>
            <div class="payload-hdr">
              <span class="msi material-symbols-outlined">output</span>
              <small>Output Payload:</small>
            </div>
            <pre>{{ JSON.stringify(log.output_data, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  flowId: {
    type: String,
    required: true
  },
  flowName: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['view-graph'])

const history = ref([])
const selectedExec = ref(null)

const fetchHistory = async () => {
  if (!props.flowId) return
  try {
    const data = await api.integrationFlows.getHistory(props.flowId)
    history.value = data || []
  } catch (e) { console.error("Error loading history:", e) }
}

const selectExecution = async (ex) => {
  try {
    const data = await api.integrationFlows.getExecutionDetail(ex.id)
    selectedExec.value = data
  } catch (e) { console.error("Error loading detail:", e) }
}

const showGraph = (ex) => {
  emit('view-graph', {
    executionId: ex.id,
    flowId: props.flowId,
    flowName: props.flowName
  })
}

watch(() => props.flowId, () => {
  selectedExec.value = null
  fetchHistory()
})

onMounted(fetchHistory)
</script>

<style scoped>
.execution-history-panel { display: flex; flex-direction: column; height: 100%; overflow-y: auto; }
.table-container { margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.selected { background: #eff6ff; }
.actions-cell { display: flex; gap: 8px; align-items: center; }
.btn-icon { 
  background: transparent; border: none; padding: 4px; border-radius: 4px; 
  cursor: pointer; color: #64748b; display: inline-flex; transition: all 0.2s;
}
.btn-icon:hover { background: #eff6ff; color: #2563eb; }
.btn-icon .material-symbols-outlined { font-size: 20px; }
.badge { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.badge.success { background: #dcfce7; color: #16a34a; }
.badge.error { background: #fee2e2; color: #dc2626; }
.detail-panel { border-top: 2px solid #e2e8f0; padding-top: 20px; margin-top: 20px; }
.detail-hdr { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; color: #1e293b; }
.detail-hdr .msi { color: #2563eb; }
.detail-hdr h3 { margin: 0; font-size: 15px; font-weight: 700; }

.node-log { background: #f8fafc; padding: 16px; margin-bottom: 16px; border-radius: 12px; border: 1px solid #e2e8f0; }
.node-log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.node-info { display: flex; align-items: center; gap: 8px; }
.node-icon { color: #64748b; font-size: 18px; }

.node-timing-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px; padding: 12px; background: #fff; border-radius: 8px; border: 1px solid #f1f5f9; }
.timing-item { display: flex; align-items: flex-start; gap: 8px; }
.timing-item .msi { font-size: 16px; margin-top: 2px; color: #94a3b8; }
.timing-item label { display: block; font-size: 9px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px; }
.timing-item span { font-size: 11px; font-weight: 600; color: #1e293b; }

.payload-hdr { display: flex; align-items: center; gap: 4px; margin-bottom: 6px; color: #64748b; }
.payload-hdr .msi { font-size: 14px; }
.log-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
.log-grid > div { min-width: 0; }
pre { background: #1e293b; color: #cbd5e1; padding: 12px; border-radius: 8px; font-size: 10px; overflow-x: auto; max-height: 200px; margin: 0; }
</style>
