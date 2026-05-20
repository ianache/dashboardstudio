<template>
  <div class="panel-overlay" @click.self="$emit('close')">
    <div class="slide-panel" :style="{ width: panelWidth + 'px' }">
      <div class="panel-resizer" @mousedown.stop="onResizeMousedown"></div>
      <div class="panel-header">
        <h2>{{ flowName }} - Historial</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="panel-body">
        <ExecutionHistoryPanel 
          :flow-id="flowId" 
          :flow-name="flowName"
          @view-graph="$emit('view-graph', $event)" 
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import ExecutionHistoryPanel from './ExecutionHistoryPanel.vue'

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
</style>
