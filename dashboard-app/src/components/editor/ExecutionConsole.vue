<template>
  <div class="exec-console">
    <div class="exec-header">
      <div class="exec-title">
        <span class="msi" style="font-size:18px">terminal</span>
        Consola de Ejecución
      </div>
      <div class="exec-status" :class="statusClass">
        <div class="status-dot"></div>
        {{ statusLabel }}
      </div>
      <div class="exec-actions">
        <button class="exec-btn" @click="$emit('clear')" title="Limpiar consola">
          <span class="msi" style="font-size:16px">delete_sweep</span>
        </button>
        <button class="exec-btn" @click="$emit('close')" title="Cerrar consola">
          <span class="msi" style="font-size:16px">close</span>
        </button>
      </div>
    </div>
    
    <div class="exec-body" ref="bodyRef">
      <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="`log--${log.type}`">
        <span class="log-ts">{{ formatTime(log.timestamp) }}</span>
        <span class="log-msg">{{ log.message }}</span>
        <pre v-if="log.data" class="log-data">{{ JSON.stringify(log.data, null, 2) }}</pre>
      </div>
      <div v-if="logs.length === 0" class="log-empty">
        Esperando ejecución...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  status: { type: String, default: 'idle' } // idle, running, success, error
})

const emit = defineEmits(['close', 'clear'])

const bodyRef = ref(null)

const statusLabel = computed(() => {
  const map = {
    idle: 'Listo',
    running: 'Ejecutando...',
    success: 'Éxito',
    error: 'Error'
  }
  return map[props.status] || props.status
})

const statusClass = computed(() => `status--${props.status}`)

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// Auto-scroll to bottom
watch(() => props.logs.length, () => {
  nextTick(() => {
    if (bodyRef.value) {
      bodyRef.value.scrollTop = bodyRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.exec-console {
  display: flex;
  flex-direction: column;
  background: #0f172a;
  color: #e2e8f0;
  height: 100%;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
}

.exec-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}

.exec-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

.exec-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
  background: #334155;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.status--running { color: #38bdf8; }
.status--running .status-dot { background: #38bdf8; box-shadow: 0 0 8px #38bdf8; }

.status--success { color: #4ade80; }
.status--success .status-dot { background: #4ade80; }

.status--error { color: #f87171; }
.status--error .status-dot { background: #f87171; }

.exec-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.exec-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  border-radius: 4px;
}

.exec-btn:hover {
  background: #334155;
  color: #f8fafc;
}

.exec-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  font-size: 12px;
  line-height: 1.6;
}

.log-line {
  margin-bottom: 4px;
  word-break: break-all;
}

.log-ts {
  color: #64748b;
  margin-right: 10px;
  user-select: none;
}

.log--info { color: #e2e8f0; }
.log--error { color: #f87171; }
.log--result { color: #38bdf8; font-weight: 600; }

.log-data {
  margin: 4px 0 8px 60px;
  padding: 8px;
  background: #1e293b;
  border-radius: 4px;
  color: #cbd5e1;
  font-size: 11px;
  overflow-x: auto;
}

.log-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  font-style: italic;
}

.msi {
  font-family: 'Material Symbols Outlined' !important;
}
</style>
