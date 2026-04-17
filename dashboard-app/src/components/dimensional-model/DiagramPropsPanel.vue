<template>
  <div class="diagram-props-panel">
    <!-- Header -->
    <div class="props-header">
      <span class="props-title-icon">◈</span>
      <span class="props-title">Diagrama</span>
      <span v-if="diagram.isMain" class="props-main-badge">Principal</span>
    </div>

    <div class="props-body">
      <!-- Name -->
      <div class="form-group">
        <label class="form-label">Nombre</label>
        <input
          class="form-input"
          :value="diagram.name"
          :disabled="diagram.isMain"
          :title="diagram.isMain ? 'El diagrama principal no puede renombrarse' : ''"
          @change="$emit('rename', $event.target.value)"
          @keydown.enter="$event.target.blur()"
        />
      </div>

      <!-- Description with Markdown preview toggle -->
      <div class="form-group">
        <div class="desc-label-row">
          <label class="form-label">Descripción</label>
          <button class="btn-md-toggle" @click="mdPreview = !mdPreview">
            {{ mdPreview ? 'Editar' : 'Vista previa' }}
          </button>
        </div>
        <textarea
          v-if="!mdPreview"
          class="form-input desc-textarea"
          :value="descDraft"
          rows="8"
          placeholder="Descripción del diagrama (Markdown soportado)..."
          @input="descDraft = $event.target.value"
          @change="$emit('update-description', descDraft)"
        />
        <div
          v-else
          class="md-preview"
          v-html="sanitizedMd"
        />
      </div>

      <!-- Node count info -->
      <div class="form-group">
        <label class="form-label">Tablas en este diagrama</label>
        <span class="node-count">{{ diagram.diagramNodes?.length ?? 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  diagram: { type: Object, required: true }
})

const emit = defineEmits(['rename', 'update-description'])

const mdPreview = ref(false)
const descDraft = ref(props.diagram.description || '')

// Sync descDraft when diagram changes (switching tabs)
watch(() => props.diagram.id, () => {
  descDraft.value = props.diagram.description || ''
  mdPreview.value = false
})

const sanitizedMd = computed(() => {
  const raw = descDraft.value || ''
  if (!raw.trim()) return '<p class="md-empty">Sin descripción</p>'
  return DOMPurify.sanitize(marked.parse(raw))
})
</script>

<style scoped>
.diagram-props-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.props-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px 8px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.props-title-icon {
  color: var(--primary, #1890ff);
  font-size: 16px;
}

.props-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.props-main-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--primary, #1890ff);
  color: #fff;
  margin-left: auto;
}

.props-body {
  padding: 12px 16px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 12px;
  font-weight: 500;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.form-input {
  border: 1px solid #ddd;
  border-radius: var(--border-radius, 8px);
  padding: 6px 10px;
  font-size: 13px;
  font-family: inherit;
  color: #333;
  background: #fff;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary, #1890ff);
}

.form-input:disabled {
  background: #f5f5f5;
  color: #aaa;
  cursor: not-allowed;
}

.desc-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-md-toggle {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--primary, #1890ff);
  border-radius: 4px;
  background: none;
  color: var(--primary, #1890ff);
  cursor: pointer;
  transition: background 0.15s;
}

.btn-md-toggle:hover {
  background: var(--primary, #1890ff);
  color: #fff;
}

.desc-textarea {
  resize: vertical;
  min-height: 120px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.md-preview {
  border: 1px solid #eee;
  border-radius: var(--border-radius, 8px);
  padding: 10px 14px;
  min-height: 120px;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  background: #fafafa;
  overflow-y: auto;
}

.md-preview :deep(h1),
.md-preview :deep(h2),
.md-preview :deep(h3) {
  margin-top: 8px;
  margin-bottom: 4px;
}

.md-preview :deep(p) {
  margin: 4px 0;
}

.md-preview :deep(code) {
  background: #f0f0f0;
  padding: 1px 4px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
}

.md-preview :deep(ul),
.md-preview :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.md-empty {
  color: #bbb;
  font-style: italic;
}

.node-count {
  font-size: 22px;
  font-weight: 600;
  color: var(--primary, #1890ff);
}
</style>
