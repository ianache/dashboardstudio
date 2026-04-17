<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <span class="modal-title">Añadir tablas al diagrama</span>
        <button class="modal-close" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <p class="modal-hint">Selecciona las tablas que quieres mostrar en "{{ activeDiagram.name }}":</p>

        <div v-if="availableNodes.length === 0" class="modal-empty">
          Todas las tablas ya están en este diagrama.
        </div>

        <div v-else class="node-list">
          <label
            v-for="node in availableNodes"
            :key="node.id"
            class="node-item"
            :class="{ selected: selected.includes(node.id) }"
          >
            <input
              type="checkbox"
              :value="node.id"
              v-model="selected"
              class="node-checkbox"
            />
            <span class="node-type-badge" :class="node.type">
              {{ node.type === 'fact' ? 'Hecho' : 'Dim' }}
            </span>
            <span class="node-name">{{ node.name }}</span>
          </label>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn" @click="$emit('close')">Cancelar</button>
        <button
          class="btn btn-primary"
          :disabled="selected.length === 0"
          @click="confirm"
        >
          Añadir {{ selected.length > 0 ? `(${selected.length})` : '' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  model: { type: Object, required: true },
  activeDiagram: { type: Object, required: true }
})

const emit = defineEmits(['close', 'add-nodes'])

const selected = ref([])

const availableNodes = computed(() => {
  const inDiagram = new Set((props.activeDiagram.diagramNodes || []).map(dn => dn.nodeId))
  return (props.model.nodes || []).filter(n => !inDiagram.has(n.id))
})

function confirm() {
  if (selected.value.length > 0) {
    emit('add-nodes', [...selected.value])
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: #fff;
  border-radius: var(--border-radius, 8px);
  box-shadow: var(--shadow-md, 0 8px 32px rgba(0,0,0,0.18));
  width: 420px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.modal-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
}

.modal-close:hover { color: #333; }

.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-hint {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px;
}

.modal-empty {
  color: #aaa;
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
  user-select: none;
}

.node-item:hover {
  background: #f5f5f5;
}

.node-item.selected {
  background: #e6f4ff;
  border-color: var(--primary, #1890ff);
}

.node-checkbox {
  accent-color: var(--primary, #1890ff);
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.node-type-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  flex-shrink: 0;
  text-transform: uppercase;
}

.node-type-badge.fact {
  background: #fff7e6;
  color: #d46b08;
}

.node-type-badge.dimension {
  background: #f0f5ff;
  color: #1d39c4;
}

.node-name {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

.btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid #ddd;
  background: #fff;
  color: #333;
  transition: background 0.12s;
}

.btn:hover { background: #f5f5f5; }

.btn-primary {
  background: var(--primary, #1890ff);
  color: #fff;
  border-color: var(--primary, #1890ff);
}

.btn-primary:hover:not(:disabled) {
  background: #096dd9;
  border-color: #096dd9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
