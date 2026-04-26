<template>
  <div class="model-list-view">
    <!-- Page header -->
    <div class="ds-page-header">
      <div>
        <h2 class="ds-page-title">Modelos Dimensionales</h2>
        <p class="ds-page-subtitle">Diseña y gestiona tus modelos de datos dimensionales</p>
      </div>
      <div class="ds-header-actions">
        <input ref="importInput" type="file" accept=".yaml,.yml" style="display:none" @change="handleImport" />
        <button class="ds-btn-secondary" @click="importInput.click()">
          <MIcon icon="upload" :size="18" />
          Importar
        </button>
        <button class="ds-btn-primary" @click="showNewModal = true">
          <MIcon icon="add" :size="18" />
          Nuevo
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="modelStore.allModels.length === 0" class="empty-state card">
      <MIcon icon="account_tree" :size="48" style="color: var(--outline-variant)" />
      <h3>Sin modelos dimensionales</h3>
      <p>Crea tu primer modelo dimensional para documentar la estructura de tus datos.</p>
      <button class="ds-btn-primary" @click="showNewModal = true">Crear modelo</button>
    </div>

    <!-- Models grid -->
    <div v-else class="designer-grid">
      <ModelCard
        v-for="(model, idx) in modelStore.allModels"
        :key="model.id"
        :name="model.name"
        :description="model.description"
        :is-global="model.isGlobal"
        :fact-count="factCount(model)"
        :dim-count="dimCount(model)"
        :rel-count="model.relationships.length"
        :color-index="idx"
        @edit="openEditor(model.id)"
        @export="exportModel(model.id)"
        @delete="confirmDelete(model)"
        @update:name="val => modelStore.updateModel(model.id, { name: val })"
        @update:description="val => modelStore.updateModel(model.id, { description: val })"
      />
      <!-- New model card -->
      <button class="designer-new-card" @click="showNewModal = true">
        <MIcon icon="add_circle" :size="32" style="color: var(--outline)" />
        <span>Nuevo modelo</span>
      </button>
    </div>

    <!-- Modal: Nuevo Modelo -->
    <div v-if="showNewModal" class="modal-overlay" @click.self="cancelNew">
      <div class="modal card">
        <div class="modal-header">
          <h3>Nuevo Modelo Dimensional</h3>
          <button class="btn-icon" @click="cancelNew">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Nombre *</label>
            <input
              v-model="newName"
              type="text"
              class="form-input"
              placeholder="Ej: Modelo de Ventas"
              @keyup.enter="createModel"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Descripción</label>
            <textarea
              v-model="newDescription"
              class="form-input"
              rows="3"
              placeholder="Describe el propósito de este modelo..."
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelNew">Cancelar</button>
          <button class="btn btn-primary" :disabled="!newName.trim()" @click="createModel">Crear</button>
        </div>
      </div>
    </div>

    <!-- Modal: Confirmar eliminar -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal card">
        <div class="modal-header">
          <h3>Eliminar modelo</h3>
        </div>
        <div class="modal-body">
          <p>¿Eliminar <strong>{{ deleteTarget.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDimensionalModelStore } from '@/stores/dimensionalModel'
import { useUIStore } from '@/stores/ui'
import yaml from 'js-yaml'
import ModelCard from '@/components/dimensional-model/ModelCard.vue'
import MIcon from '@/components/common/MIcon.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const modelStore = useDimensionalModelStore()
const uiStore = useUIStore()

// Load data from backend on mount
onMounted(async () => {
  await modelStore.loadFromBackend()
})

const showNewModal = ref(false)
const newName = ref('')
const newDescription = ref('')
const deleteTarget = ref(null)
const importInput = ref(null)

onMounted(() => {
  modelStore.ensureGlobalModel()
  uiStore.setBreadcrumbs(['Modelos'])
  if (route.query.new === '1') showNewModal.value = true
})

function factCount(model) {
  return model.nodes.filter(n => n.type === 'fact').length
}

function dimCount(model) {
  return model.nodes.filter(n => n.type === 'dimension').length
}

function openEditor(id) {
  router.push(`/models/${id}`)
}

function cancelNew() {
  showNewModal.value = false
  newName.value = ''
  newDescription.value = ''
}

function createModel() {
  if (!newName.value.trim()) return
  const model = modelStore.createModel({
    name: newName.value.trim(),
    description: newDescription.value.trim(),
    createdBy: authStore.user?.id || ''
  })
  cancelNew()
  router.push(`/models/${model.id}`)
}

function exportModel(modelId) {
  const model = modelStore.getModel(modelId)
  if (!model) return
  const doc = {
    version: '1.0',
    type: 'dimensional_model',
    name: model.name,
    description: model.description,
    nodes: model.nodes.map(n => ({
      id: n.id, type: n.type, name: n.name, x: n.x, y: n.y,
      fields: n.fields.map(f => ({
        id: f.id, name: f.name, description: f.description,
        dataType: f.dataType, isKey: !!f.isKey, isFk: !!f.isFk
      }))
    })),
    relationships: model.relationships.map(r => ({
      id: r.id, fromNodeId: r.fromNodeId, toNodeId: r.toNodeId, cardinality: r.cardinality
    }))
  }
  const content = yaml.dump(doc, { indent: 2, lineWidth: 120 })
  const slug = model.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'modelo'
  const blob = new Blob([content], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${slug}.yaml`; a.click()
  URL.revokeObjectURL(url)
}

function handleImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const doc = yaml.load(ev.target.result)
      if (!doc || typeof doc !== 'object') throw new Error('Formato inválido')
      
      // Creamos un nuevo modelo en el listado a partir del YAML importado
      const newModel = modelStore.createModel({
        name: doc.name || 'Modelo Importado',
        description: doc.description || '',
        createdBy: authStore.user?.id || ''
      })
      
      const m = modelStore.getModel(newModel.id)
      if (m) {
        m.nodes = Array.isArray(doc.nodes) ? doc.nodes : []
        m.relationships = Array.isArray(doc.relationships) ? doc.relationships : []
        modelStore.persist()
      }
    } catch (err) {
      alert(`Error al importar: ${err.message}`)
    } finally {
      e.target.value = ''
    }
  }
  reader.readAsText(file)
}

function confirmDelete(model) {
  deleteTarget.value = model
}

function doDelete() {
  modelStore.deleteModel(deleteTarget.value.id)
  deleteTarget.value = null
}
</script>

<style scoped>
.model-list-view { display: flex; flex-direction: column; gap: 24px; }

/* ── Page header ── */
.ds-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.ds-page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--on-surface);
  font-family: 'Plus Jakarta Sans', sans-serif;
  line-height: 1.2;
  margin: 0 0 6px;
}
.ds-page-subtitle {
  font-size: 14px;
  color: var(--on-surface-variant);
  margin: 0;
}
.ds-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.ds-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.ds-btn-primary:hover { background: var(--primary-dark); }
.ds-btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--surface-container-low);
  color: var(--on-surface);
  border: 1px solid var(--outline-variant);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.ds-btn-secondary:hover { background: var(--surface-container); }

/* ── Grid ── */
.designer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* ── New model dashed card ── */
.designer-new-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 340px;
  background: transparent;
  border: 2px dashed var(--outline-variant);
  border-radius: 12px;
  cursor: pointer;
  color: var(--on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  transition: border-color 0.2s, background 0.2s, color 0.2s;
}
.designer-new-card:hover {
  border-color: var(--primary);
  background: rgba(0, 88, 190, 0.04);
  color: var(--primary);
}

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
  text-align: center;
}
.empty-state h3 { font-size: 18px; font-weight: 600; color: var(--on-surface); margin: 0; }
.empty-state p { font-size: 14px; color: var(--on-surface-variant); margin: 0; }

/* ── Modals ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  width: 440px;
  max-width: 95vw;
  padding: 0;
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.modal-header h3 { font-size: 16px; font-weight: 600; color: var(--text); margin: 0; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  background: #fafafa;
}

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 13px; font-weight: 500; color: var(--text); }

.btn-danger {
  background: var(--error);
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}
.btn-danger:hover { background: #cf1322; }

.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 20px; gap: 12px; text-align: center;
}
.empty-icon { font-size: 48px; }
.empty-state h3 { font-size: 18px; font-weight: 600; color: var(--text); margin: 0; }
.empty-state p { font-size: 14px; color: var(--text-secondary); margin: 0; }
</style>
