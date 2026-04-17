<template>
  <div class="diagram-tab-bar">
    <div
      v-for="diag in diagrams"
      :key="diag.id"
      class="diagram-tab"
      :class="{ active: diag.id === activeDiagramId, 'is-main': diag.isMain }"
      @click="$emit('update:activeDiagramId', diag.id)"
      @dblclick="diag.isMain ? null : startInlineRename(diag)"
    >
      <span v-if="renamingId !== diag.id" class="tab-label">{{ diag.name }}</span>
      <input
        v-else
        ref="renameInput"
        class="tab-rename-input"
        :value="diag.name"
        @blur="commitRename(diag, $event.target.value)"
        @keydown.enter="commitRename(diag, $event.target.value)"
        @keydown.escape="renamingId = null"
        @click.stop
      />
      <button
        v-if="!diag.isMain"
        class="tab-close"
        @click.stop="$emit('delete-diagram', diag.id)"
        title="Eliminar diagrama"
      >×</button>
    </div>
    <button class="tab-add" @click="$emit('create-diagram')" title="Nuevo diagrama">+</button>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  diagrams: { type: Array, required: true },
  activeDiagramId: { type: String, required: true }
})

const emit = defineEmits(['update:activeDiagramId', 'create-diagram', 'delete-diagram', 'rename-diagram'])

const renamingId = ref(null)
const renameInput = ref(null)

function startInlineRename(diag) {
  renamingId.value = diag.id
  nextTick(() => {
    if (renameInput.value) {
      const el = Array.isArray(renameInput.value) ? renameInput.value[0] : renameInput.value
      el?.focus()
      el?.select()
    }
  })
}

function commitRename(diag, newName) {
  if (newName && newName.trim() && newName.trim() !== diag.name) {
    emit('rename-diagram', diag.id, newName.trim())
  }
  renamingId.value = null
}
</script>

<style scoped>
.diagram-tab-bar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 12px;
  background: var(--bg, #f0f2f5);
  border-bottom: 1px solid #e0e0e0;
  overflow-x: auto;
  flex-shrink: 0;
}

.diagram-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  background: #e8e8e8;
  border: 1px solid transparent;
  border-bottom: none;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  min-width: 0;
}

.diagram-tab.active {
  background: #fff;
  color: var(--primary, #1890ff);
  border-color: #e0e0e0;
  font-weight: 600;
}

.diagram-tab.is-main .tab-label::before {
  content: '★ ';
  font-size: 11px;
  opacity: 0.6;
}

.diagram-tab:hover:not(.active) {
  background: #ddd;
}

.tab-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.tab-rename-input {
  border: 1px solid var(--primary, #1890ff);
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 13px;
  width: 120px;
  outline: none;
}

.tab-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  border-radius: 3px;
  flex-shrink: 0;
}

.tab-close:hover {
  background: #f5222d22;
  color: #f5222d;
}

.tab-add {
  background: none;
  border: 1px dashed #bbb;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 16px;
  color: #888;
  margin-left: 4px;
  transition: border-color 0.15s, color 0.15s;
}

.tab-add:hover {
  border-color: var(--primary, #1890ff);
  color: var(--primary, #1890ff);
}
</style>
