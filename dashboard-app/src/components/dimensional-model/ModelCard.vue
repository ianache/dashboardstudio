<template>
  <div class="mcard" @click="$emit('edit')">
    <!-- Gradient header -->
    <div class="mcard-header" :style="{ background: gradients[colorIndex % gradients.length] }">
      <div class="mcard-header-overlay" />
      <!-- Category icon badge -->
      <div class="mcard-category-badge">
        <MIcon icon="account_tree" :size="22" :fill="1" style="color: var(--primary)" />
      </div>
      <!-- Global badge -->
      <div v-if="isGlobal" class="mcard-global-badge">
        <MIcon icon="public" :size="12" />
        GLOBAL
      </div>
    </div>

    <!-- Body -->
    <div class="mcard-body">
      <!-- Name row -->
      <div class="mcard-title-row">
        <template v-if="editingField !== 'name'">
          <h3 class="mcard-name editable" @click.stop="startEdit('name')">
            {{ name }}
            <MIcon icon="edit" :size="13" class="mcard-edit-hint" />
          </h3>
        </template>
        <input
          v-else
          ref="nameInputRef"
          :value="editValue"
          type="text"
          class="form-input mcard-inline-input"
          @input="editValue = $event.target.value"
          @blur="saveEdit"
          @keyup.enter="saveEdit"
          @keyup.escape="cancelEdit"
          @click.stop
        />
        <span class="mcard-table-chip">{{ factCount + dimCount }} tablas</span>
      </div>

      <!-- Description -->
      <template v-if="editingField !== 'description'">
        <p class="mcard-desc editable" @click.stop="startEdit('description')">
          {{ description || 'Sin descripción' }}
        </p>
      </template>
      <textarea
        v-else
        ref="descInputRef"
        :value="editValue"
        class="form-input mcard-inline-textarea"
        rows="2"
        placeholder="Sin descripción"
        @input="editValue = $event.target.value"
        @blur="saveEdit"
        @keyup.escape="cancelEdit"
        @click.stop
      />

      <!-- Footer -->
      <div class="mcard-footer">
        <!-- Meta stats -->
        <div class="mcard-meta">
          <span class="mcard-meta-item">
            <MIcon icon="table_chart" :size="13" />
            {{ factCount }} hechos
          </span>
          <span class="mcard-meta-sep">·</span>
          <span class="mcard-meta-item">
            <MIcon icon="view_column" :size="13" />
            {{ dimCount }} dims
          </span>
          <template v-if="relCount">
            <span class="mcard-meta-sep">·</span>
            <span class="mcard-meta-item mcard-meta-item--rel">
              <MIcon icon="share" :size="13" />
              {{ relCount }}
            </span>
          </template>
        </div>

        <!-- Actions -->
        <div class="mcard-actions" @click.stop>
          <button class="mcard-action" data-tooltip="Editar" @click.stop="$emit('edit')">
            <MIcon icon="edit" :size="19" />
          </button>
          <button class="mcard-action" data-tooltip="Exportar YAML" @click.stop="$emit('export')">
            <MIcon icon="download" :size="19" />
          </button>
          <button
            v-if="!isGlobal"
            class="mcard-action mcard-action--danger"
            data-tooltip="Eliminar"
            @click.stop="$emit('delete')"
          >
            <MIcon icon="delete" :size="19" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import MIcon from '@/components/common/MIcon.vue'

const props = defineProps({
  name: { type: String, required: true },
  description: { type: String, default: '' },
  isGlobal: { type: Boolean, default: false },
  factCount: { type: Number, default: 0 },
  dimCount: { type: Number, default: 0 },
  relCount: { type: Number, default: 0 },
  colorIndex: { type: Number, default: 0 },
})
const emit = defineEmits(['edit', 'export', 'delete', 'update:name', 'update:description'])

const gradients = [
  'linear-gradient(135deg, #1e3a5f 0%, #2170e4 100%)',
  'linear-gradient(135deg, #2d1b69 0%, #6063ee 100%)',
  'linear-gradient(135deg, #064e3b 0%, #059669 100%)',
  'linear-gradient(135deg, #7c2d12 0%, #ea580c 100%)',
  'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
  'linear-gradient(135deg, #4a044e 0%, #a21caf 100%)',
]

const editingField = ref(null)
const editValue = ref('')
const nameInputRef = ref(null)
const descInputRef = ref(null)

async function startEdit(field) {
  editingField.value = field
  editValue.value = field === 'name' ? props.name : (props.description || '')
  await nextTick()
  if (field === 'name') nameInputRef.value?.focus()
  else descInputRef.value?.focus()
}

function saveEdit() {
  if (!editingField.value) return
  const val = editValue.value.trim()
  if (editingField.value === 'name' && val) {
    emit('update:name', val)
  } else if (editingField.value === 'description') {
    emit('update:description', val)
  }
  cancelEdit()
}

function cancelEdit() {
  editingField.value = null
  editValue.value = ''
}
</script>

<style scoped>
.mcard {
  background: #fff;
  border: 1px solid var(--outline-variant);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.mcard:hover {
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.1);
  transform: translateY(-2px);
}

/* ── Header ── */
.mcard-header {
  height: 160px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px;
}
.mcard-header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(2, 6, 23, 0.55) 0%, transparent 50%);
  z-index: 1;
}

.mcard-category-badge {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border-radius: 8px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.15);
}

.mcard-global-badge {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  background: #7c3aed;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 4px 8px;
  border-radius: 6px;
  height: fit-content;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
}

/* ── Body ── */
.mcard-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mcard-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 2px;
}
.mcard-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  line-height: 1.3;
  font-family: 'Plus Jakarta Sans', sans-serif;
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.mcard-edit-hint {
  color: var(--on-surface-variant);
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.mcard-name:hover .mcard-edit-hint { opacity: 1; }

.mcard-table-chip {
  font-size: 12px;
  font-weight: 500;
  color: var(--secondary);
  background: var(--surface-container-low);
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.mcard-desc {
  font-size: 13px;
  color: var(--on-surface-variant);
  line-height: 1.5;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.editable {
  cursor: text;
  border-radius: 4px;
  padding: 2px 4px;
  margin-left: -4px;
  transition: background 0.15s;
}
.editable:hover { background: var(--surface-container-low); }

.mcard-inline-input {
  font-size: 16px;
  font-weight: 600;
  width: 100%;
  height: 34px;
  padding: 2px 8px;
  margin-bottom: 2px;
}
.mcard-inline-textarea {
  font-size: 13px;
  width: 100%;
  padding: 4px 8px;
  resize: none;
  line-height: 1.5;
}

/* ── Footer ── */
.mcard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
  margin-top: auto;
  gap: 8px;
}

.mcard-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.mcard-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 500;
  color: var(--on-surface-variant);
}
.mcard-meta-item--rel { color: #d97706; }
.mcard-meta-sep { color: var(--outline-variant); font-size: 11px; }

/* ── Actions ── */
.mcard-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.mcard-action {
  position: relative;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 7px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.15s, background 0.15s;
}
.mcard-action:hover {
  color: var(--primary);
  background: rgba(0, 88, 190, 0.07);
}
.mcard-action--danger:hover {
  color: var(--error);
  background: rgba(186, 26, 26, 0.07);
}

.mcard-action[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #fff;
  font-size: 11px;
  padding: 3px 7px;
  border-radius: 5px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 50;
}
.mcard-action[data-tooltip]:hover::after { opacity: 1; }
</style>
