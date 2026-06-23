<template>
  <div class="nip-root">
    <div v-if="!nodeData" class="nip-empty nip-no-data">
      Sin datos de ejecución
    </div>

    <template v-else>
      <!-- Header -->
      <div class="nip-header">
        <div class="nip-node-name">{{ nodeName }}</div>
        <div class="nip-status-row">
          <span class="nip-chip" :class="`nip-chip--${nodeData.status || 'running'}`">
            <span class="msi" style="font-size:14px">{{ statusIcon }}</span>
            {{ nodeData.status || 'running' }}
          </span>
          <span class="nip-duration">{{ formatDuration(nodeData.duration) }}</span>
          <button class="nip-export-btn" @click="exportData" title="Exportar datos de ejecución">
            <span class="msi" style="font-size:16px">download</span>
          </button>
        </div>
        <div class="nip-timestamps">
          <span>Inicio: {{ formatTime(nodeData.start_time) }}</span>
          <span>Fin: {{ formatTime(nodeData.end_time) }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="nip-tabs">
        <button
          class="nip-tab"
          :class="{ active: innerTab === 'output' }"
          @click="innerTab = 'output'"
        >Salida</button>
        <button
          class="nip-tab"
          :class="{ active: innerTab === 'input' }"
          @click="innerTab = 'input'"
        >Entrada</button>
        <button
          class="nip-tab"
          :class="{ active: innerTab === 'logs' }"
          @click="innerTab = 'logs'"
        >Logs</button>
      </div>

      <!-- Body -->
      <div class="nip-body">
        <template v-if="innerTab === 'input' || innerTab === 'output'">
          <!-- data_object section -->
          <div class="nip-section-hdr">
            <span class="nip-section-title">data_object</span>
            <button class="nip-expand-btn" @click="jsonExpanded = !jsonExpanded">
              {{ jsonExpanded ? 'Contraer todo' : 'Expandir todo' }}
            </button>
          </div>
          <div v-if="isTruncated" class="nip-truncated-warn">
            Payload truncado (demasiado grande)
          </div>
          <pre class="nip-json">{{ displayJson(activePayload) }}</pre>

          <!-- variables section -->
          <div class="nip-section-hdr" style="margin-top: 16px;">
            <span class="nip-section-title">variables</span>
          </div>
          <table v-if="hasVariables" class="nip-vars-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Valor</th>
                <th>Tipo</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(val, key) in activePayload?.variables" :key="key">
                <td>{{ key }}</td>
                <td>{{ formatVarValue(val) }}</td>
                <td>{{ inferType(val) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="nip-empty">Sin variables</div>
        </template>

        <template v-else-if="innerTab === 'logs'">
          <div v-if="!nodeData.logs?.length" class="nip-empty">
            Sin actividad registrada
          </div>
          <div
            v-for="(log, i) in nodeData.logs"
            :key="i"
            class="nip-log-line"
            :class="`nip-log--${log.severity || 'info'}`"
          >
            <span class="nip-log-ts">{{ log.timestamp }}</span>
            <span class="nip-log-msg">{{ log.message }}</span>
          </div>
        </template>
      </div>

      <!-- Panel de Error Colapsable -->
      <div v-if="nodeData.status === 'error' || nodeData.error_message" class="nip-error-panel" :class="{ collapsed: !isErrorExpanded }">
        <div class="nip-error-hdr" @click="isErrorExpanded = !isErrorExpanded">
          <span class="msi nip-error-icon">warning</span>
          <span class="nip-error-title">Causa de la Falla</span>
          <span class="msi nip-error-collapse-icon">{{ isErrorExpanded ? 'expand_more' : 'expand_less' }}</span>
        </div>
        <div v-show="isErrorExpanded" class="nip-error-body">
          <pre class="nip-error-pre">{{ nodeData.error_message || 'Fallo de ejecución sin mensaje detallado.' }}</pre>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const isErrorExpanded = ref(true)

const props = defineProps({
  nodeId:   { type: String, required: true },
  nodeName: { type: String, default: '' },
  nodeData: {
    type: Object,
    default: null
    // shape: { input, output, status, duration, start_time, end_time, logs: [] }
  }
})

// Internal state
const innerTab = ref('output')
const jsonExpanded = ref(true)

// Computed: active payload based on selected tab
const activePayload = computed(() => {
  if (!props.nodeData) return null
  if (innerTab.value === 'input') return props.nodeData.input
  if (innerTab.value === 'output') return props.nodeData.output
  return null
})

// Computed: warn if JSON is very large
const isTruncated = computed(() => {
  if (!activePayload.value) return false
  return JSON.stringify(activePayload.value).length > 2000
})

// Computed: whether variables section has entries
const hasVariables = computed(() => {
  return !!(activePayload.value?.variables && Object.keys(activePayload.value.variables).length > 0)
})

// Computed: status icon name (Material Symbols)
const statusIcon = computed(() => {
  if (!props.nodeData) return 'sync'
  if (props.nodeData.status === 'success') return 'check_circle'
  if (props.nodeData.status === 'error') return 'cancel'
  return 'sync'
})

// Helper functions
function inferType(val) {
  if (val === null) return 'Null'
  if (Array.isArray(val)) return 'Array'
  const t = typeof val
  return t.charAt(0).toUpperCase() + t.slice(1)
}

function formatVarValue(val) {
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function formatDuration(ms) {
  if (!ms && ms !== 0) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleTimeString()
}

function displayJson(data) {
  if (!jsonExpanded.value) return '{...}'
  return JSON.stringify(data, null, 2) || '{}'
}

function exportData() {
  if (!props.nodeData) return
  const payload = {
    node_id: props.nodeId,
    node_name: props.nodeName,
    status: props.nodeData.status,
    duration: props.nodeData.duration,
    input: props.nodeData.input,
    output: props.nodeData.output,
    error_message: props.nodeData.error_message,
    logs: props.nodeData.logs
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `node-${props.nodeId}-execution.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.nip-root {
  background: #0f172a;
  color: #e2e8f0;
  height: 100%;
  display: flex;
  flex-direction: column;
  font-family: sans-serif;
}

.nip-no-data {
  padding: 24px 16px;
}

.nip-header {
  background: #1e293b;
  padding: 12px 16px;
  border-bottom: 1px solid #334155;
}

.nip-node-name {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 8px;
}

.nip-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nip-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  text-transform: capitalize;
}

.nip-chip--success {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.nip-chip--error {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.nip-chip--running {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.nip-duration {
  font-size: 12px;
  color: #64748b;
  margin-left: auto;
}

.nip-export-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.15s;
}

.nip-export-btn:hover {
  color: #e2e8f0;
}

.nip-timestamps {
  font-size: 11px;
  color: #64748b;
  margin-top: 6px;
  display: flex;
  gap: 12px;
}

.nip-tabs {
  display: flex;
  border-bottom: 1px solid #334155;
  background: #1e293b;
}

.nip-tab {
  flex: 1;
  padding: 8px;
  font-size: 12px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #64748b;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.nip-tab.active {
  color: #38bdf8;
  border-bottom-color: #38bdf8;
}

.nip-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.nip-section-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.nip-section-title {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nip-expand-btn {
  font-size: 11px;
  background: none;
  border: 1px solid #334155;
  color: #64748b;
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: color 0.15s;
}

.nip-expand-btn:hover {
  color: #e2e8f0;
}

.nip-truncated-warn {
  font-size: 11px;
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 4px;
  padding: 4px 8px;
  margin-bottom: 8px;
}

.nip-json {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-all;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid #334155;
  border-radius: 4px;
  padding: 8px;
  margin: 0;
}

.nip-vars-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.nip-vars-table th {
  text-align: left;
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-bottom: 1px solid #334155;
}

.nip-vars-table td {
  padding: 4px 8px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  color: #e2e8f0;
  font-family: monospace;
  font-size: 11px;
}

.nip-empty {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  padding: 8px 0;
}

.nip-log-line {
  font-size: 11px;
  padding: 2px 0;
  font-family: monospace;
  display: flex;
  gap: 8px;
}

.nip-log-ts {
  color: #64748b;
  flex-shrink: 0;
}

.nip-log--error .nip-log-msg {
  color: #f87171;
}

.nip-log--result .nip-log-msg {
  color: #38bdf8;
}

.nip-log--info .nip-log-msg {
  color: #e2e8f0;
}

/* Panel de Error Colapsable */
.nip-error-panel {
  border-top: 1px solid rgba(239, 68, 68, 0.4);
  background: #1e1b1b; /* HSL-tailored deep dark red/brown */
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease-in-out;
}

.nip-error-hdr {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.1);
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid rgba(239, 68, 68, 0.15);
  transition: background 0.2s ease;
}

.nip-error-hdr:hover {
  background: rgba(239, 68, 68, 0.18);
}

.nip-error-icon {
  color: #f87171;
  font-size: 16px;
}

.nip-error-title {
  font-size: 11px;
  font-weight: 600;
  color: #f87171;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex: 1;
}

.nip-error-collapse-icon {
  color: #f87171;
  font-size: 18px;
  transition: transform 0.2s ease;
}

.nip-error-panel.collapsed .nip-error-collapse-icon {
  transform: rotate(180deg);
}

.nip-error-body {
  padding: 12px 16px;
  max-height: 180px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.2);
}

.nip-error-pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #fca5a5;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
}
</style>
