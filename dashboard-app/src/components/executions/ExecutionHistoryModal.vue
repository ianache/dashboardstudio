<template>
  <div class="panel-overlay" @click.self="$emit('close')">
    <div class="slide-panel">
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
                <td><button class="btn-detail" @click="selectExecution(ex)">Ver</button></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="selectedExec" class="detail-panel">
          <h3>Detalle de Nodos (ID: {{ selectedExec.id }})</h3>
          <div v-for="log in selectedExec.node_logs" :key="log.node_id" class="node-log">
            <div class="node-log-header">
              <strong>Nodo: {{ log.node_id }}</strong>
              <span :class="['badge', log.status]">{{ log.status }}</span>
            </div>
            <div class="log-grid">
              <div>
                <small>Input:</small>
                <pre>{{ JSON.stringify(log.input_data, null, 2) }}</pre>
              </div>
              <div>
                <small>Output:</small>
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
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps(['flowId', 'flowName'])
const emit = defineEmits(['close'])
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

onMounted(fetchHistory)
</script>

<style scoped>
.panel-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; }
.slide-panel { 
  position: fixed; top: 0; right: 0; bottom: 0; width: 500px; 
  background: white; box-shadow: -5px 0 15px rgba(0,0,0,0.1);
  display: flex; flex-direction: column;
  animation: slideIn 0.3s ease-out;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid #e2e8f0; }
.panel-body { padding: 20px; overflow-y: auto; flex: 1; }
.close-btn { background: none; border: none; cursor: pointer; font-size: 18px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.selected { background: #eff6ff; }
.btn-detail { background: #2563eb; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; }
.badge { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.badge.success { background: #dcfce7; color: #16a34a; }
.badge.error { background: #fee2e2; color: #dc2626; }
.detail-panel { border-top: 2px solid #e2e8f0; padding-top: 20px; margin-top: 20px; }
.node-log { background: #f8fafc; padding: 12px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #f1f5f9; }
.node-log-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
pre { background: #1e293b; color: #e2e8f0; padding: 8px; border-radius: 4px; font-size: 11px; overflow-x: auto; }
</style>
