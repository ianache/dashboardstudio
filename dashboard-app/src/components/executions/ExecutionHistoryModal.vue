<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Historial de Ejecución: {{ flowName }}</h2>
        <button @click="$emit('close')"><MIcon icon="close" /></button>
      </div>

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
            <tr v-for="ex in history" :key="ex.id">
              <td><span :class="['badge', ex.status]">{{ ex.status }}</span></td>
              <td>{{ new Date(ex.start_time).toLocaleString() }}</td>
              <td>{{ ex.duration }} ms</td>
              <td><button @click="selectExecution(ex)">Detalle</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="selectedExec" class="detail-panel">
        <h3>Detalle de Nodos</h3>
        <div v-for="log in selectedExec.node_logs" :key="log.node_id" class="node-log">
          <strong>Nodo: {{ log.node_id }}</strong> - {{ log.status }}
          <pre>{{ JSON.stringify(log.output_data, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import MIcon from '@/components/common/MIcon.vue'

const props = defineProps(['flowId', 'flowName'])
const history = ref([])
const selectedExec = ref(null)

const fetchHistory = async () => {
  const { data } = await api.get(`/execution-history/${props.flowId}`)
  history.value = data
}

const selectExecution = async (ex) => {
  const { data } = await api.get(`/execution-history/detail/${ex.id}`)
  selectedExec.value = data
}

onMounted(fetchHistory)
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; padding: 24px; border-radius: 8px; width: 600px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; }
.table-container { margin: 20px 0; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.badge { padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.badge.success { background: #dcfce7; color: #16a34a; }
.badge.error { background: #fee2e2; color: #dc2626; }
.detail-panel { margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 20px; }
.node-log { background: #f8fafc; padding: 10px; margin-bottom: 8px; border-radius: 4px; }
</style>
