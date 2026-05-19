<template>
  <div class="panel-overlay" @click.self="$emit('close')">
    <div class="slide-panel" :style="{ width: panelWidth + 'px' }">
      <div class="panel-resizer" @mousedown.stop="onResizeMousedown"></div>
      <div class="panel-header">
        <h2>{{ flowName }} - Historial</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="panel-body">
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
              <tr v-for="ex in history" :key="ex.id" :class="{ 'selected': selectedExec?.id === ex.id }">
                <td><span :class="['badge', ex.status]">{{ ex.status }}</span></td>
                <td>{{ new Date(ex.start_time).toLocaleString() }}</td>
                <td>{{ ex.duration || 0 }} ms</td>
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
            <span class="msi">analytics</span>
            <h3>Detalle de Nodos (ID: {{ selectedExec.id }})</h3>
          </div>
          
          <div v-for="(log, idx) in selectedExec.node_logs" :key="log.node_id + '-' + idx" class="node-log">
            <div class="node-log-header">
              <div class="node-info">
                <span class="msi node-icon">terminal</span>
                <strong>{{ log.node_title || ('Nodo: ' + log.node_id) }}</strong>
              </div>
              <span :class="['badge', log.status]">{{ log.status === 'success' ? 'Completado' : 'Fallido' }}</span>
            </div>

            <div class="node-timing-grid">
              <div class="timing-item">
                <span class="msi">play_arrow</span>
                <div>
                  <label>Inicio</label>
                  <span>{{ log.start_time ? new Date(log.start_time).toLocaleString() : '—' }}</span>
                </div>
              </div>
              <div class="timing-item">
                <span class="msi">stop</span>
                <div>
                  <label>Fin</label>
                  <span>{{ log.end_time ? new Date(log.end_time).toLocaleString() : '—' }}</span>
                </div>
              </div>
              <div class="timing-item">
                <span class="msi">timer</span>
                <div>
                  <label>Duración</label>
                  <span>{{ log.duration || 0 }} ms</span>
                </div>
              </div>
            </div>

            <div class="log-grid">
              <div>
                <div class="payload-hdr">
                  <span class="msi">input</span>
                  <small>Input Payload:</small>
                </div>
                <pre>{{ JSON.stringify(log.input_data, null, 2) }}</pre>
              </div>
              <div>
                <div class="payload-hdr">
                  <span class="msi">output</span>
                  <small>Output Payload:</small>
                </div>
                <pre>{{ JSON.stringify(log.output_data, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const panelWidth = ref(600)
const isResizing = ref(false)

const onResizeMousedown = (e) => {
  isResizing.value = true
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', onResizeMousemove)
  window.addEventListener('mouseup', onResizeMouseup)
}

const onResizeMousemove = (e) => {
  if (!isResizing.value) return
  const newWidth = window.innerWidth - e.clientX
  panelWidth.value = Math.max(350, Math.min(newWidth, window.innerWidth * 0.9))
}

const onResizeMouseup = () => {
  isResizing.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', onResizeMousemove)
  window.removeEventListener('mouseup', onResizeMouseup)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onResizeMousemove)
  window.removeEventListener('mouseup', onResizeMouseup)
})

const props = defineProps(['flowId', 'flowName'])
const emit = defineEmits(['close', 'view-graph'])
const history = ref([])
const selectedExec = ref(null)

const fetchHistory = async () => {
  try {
    console.log("Fetching history for flowId:", props.flowId)
    const data = await api.integrationFlows.getHistory(props.flowId)
    console.log("Received history:", data)
    history.value = data
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

onMounted(fetchHistory)
</script>

<style scoped>
.panel-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; }
.slide-panel { 
  position: fixed; top: 0; right: 0; bottom: 0; 
  background: white; box-shadow: -5px 0 15px rgba(0,0,0,0.1);
  display: flex; flex-direction: column;
  animation: slideIn 0.3s ease-out;
}
.panel-resizer {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: ew-resize;
  z-index: 10;
  transition: background-color 0.2s;
}
.panel-resizer:hover,
.panel-overlay:active .panel-resizer {
  background-color: rgba(37, 99, 235, 0.3);
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid #e2e8f0; }
.panel-body { padding: 20px; overflow-y: auto; flex: 1; }
.close-btn { background: none; border: none; cursor: pointer; font-size: 18px; }
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
.log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
pre { background: #1e293b; color: #cbd5e1; padding: 12px; border-radius: 8px; font-size: 10px; overflow-x: auto; max-height: 200px; margin: 0; }

</style>
