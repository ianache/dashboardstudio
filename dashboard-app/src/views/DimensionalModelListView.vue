<template>
  <div class="model-list-view">
    <div class="page-header">
      <div>
        <h2 class="page-title">Modelos Dimensionales</h2>
        <p class="page-subtitle">Diseña y gestiona tus modelos de datos dimensionales</p>
      </div>
      <button class="btn btn-primary" @click="showNewModal = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Nuevo Modelo
      </button>
    </div>

    <div v-if="modelStore.allModels.length === 0" class="empty-state card">
      <div class="empty-icon">🗄️</div>
      <h3>Sin modelos dimensionales</h3>
      <p>Crea tu primer modelo dimensional para documentar la estructura de tus datos.</p>
      <button class="btn btn-primary" @click="showNewModal = true">Crear modelo</button>
    </div>

    <div v-else class="model-grid">
      <div v-for="model in modelStore.allModels" :key="model.id" class="model-card card">
        <div class="model-card-header">
          <div class="model-icon-wrap">
            <span class="model-icon">🗄️</span>
            <span v-if="model.isGlobal" class="global-badge">GLOBAL</span>
          </div>
          <div class="model-card-actions">
            <button class="btn btn-secondary btn-sm" @click="openEditor(model.id)">
              Editar
            </button>
            <button
              v-if="!model.isGlobal"
              class="btn-icon"
              data-tooltip="Eliminar"
              @click="confirmDelete(model)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--error)">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="model-card-body">
          <h3
            v-if="editingId !== model.id + ':name'"
            class="model-name editable"
            @click.stop="startEdit(model, 'name')"
          >{{ model.name }}</h3>
          <input
            v-else
            :ref="el => { if (el) el.focus() }"
            :value="editValue"
            type="text"
            class="form-input inline-edit-input"
            @input="editValue = $event.target.value"
            @blur="saveEdit(model)"
            @keyup.enter="saveEdit(model)"
            @keyup.escape="cancelEdit"
            @click.stop
          />

          <p
            v-if="editingId !== model.id + ':description'"
            class="model-desc editable"
            @click.stop="startEdit(model, 'description')"
          >{{ model.description || 'Sin descripción' }}</p>
          <textarea
            v-else
            :ref="el => { if (el) el.focus() }"
            :value="editValue"
            class="form-input inline-edit-textarea"
            rows="2"
            placeholder="Sin descripción"
            @input="editValue = $event.target.value"
            @blur="saveEdit(model)"
            @keyup.escape="cancelEdit"
            @click.stop
          />
          <div class="model-card-meta">
            <span class="badge badge-blue">{{ factCount(model) }} hechos</span>
            <span class="badge badge-green">{{ dimCount(model) }} dimensiones</span>
            <span v-if="model.relationships.length" class="badge" style="background:#fff7e6;color:#d46b08">
              {{ model.relationships.length }} relaciones
            </span>
          </div>
        </div>
      </div>
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

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const modelStore = useDimensionalModelStore()
const uiStore = useUIStore()

const showNewModal = ref(false)
const newName = ref('')
const newDescription = ref('')
const deleteTarget = ref(null)

// Inline editing: editingId = '{modelId}:{field}'
const editingId = ref(null)
const editValue = ref('')

function startEdit(model, field) {
  editingId.value = `${model.id}:${field}`
  editValue.value = field === 'name' ? model.name : (model.description || '')
}

function saveEdit(model) {
  if (!editingId.value) return
  const field = editingId.value.split(':')[1]
  const val = editValue.value.trim()
  if (field === 'name' && val) {
    modelStore.updateModel(model.id, { name: val })
  } else if (field === 'description') {
    modelStore.updateModel(model.id, { description: val })
  }
  cancelEdit()
}

function cancelEdit() {
  editingId.value = null
  editValue.value = ''
}

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

function confirmDelete(model) {
  deleteTarget.value = model
}

function doDelete() {
  modelStore.deleteModel(deleteTarget.value.id)
  deleteTarget.value = null
}
</script>

<style scoped>
.model-list-view { display: flex; flex-direction: column; gap: 20px; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-title { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); margin: 0; }

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.model-card {
  padding: 0;
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.15s;
}
.model-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }

.model-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--border);
  background: #fafafa;
}
.model-icon-wrap { display: flex; align-items: center; gap: 8px; }
.model-icon { font-size: 28px; line-height: 1; }
.global-badge {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  background: #722ed1; color: #fff;
  padding: 2px 7px; border-radius: 10px;
}
.model-card-actions { display: flex; gap: 6px; align-items: center; }

.model-card-body { padding: 14px 16px; }
.model-name { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.model-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; min-height: 36px; }

.editable {
  cursor: text;
  border-radius: 4px;
  transition: background 0.15s;
  padding: 2px 4px;
  margin-left: -4px;
}
.editable:hover { background: var(--bg); }

.inline-edit-input {
  font-size: 15px;
  font-weight: 600;
  width: 100%;
  margin-bottom: 6px;
  padding: 2px 6px;
  height: 30px;
}
.inline-edit-textarea {
  font-size: 13px;
  width: 100%;
  margin-bottom: 10px;
  padding: 4px 6px;
  resize: none;
  line-height: 1.5;
}
.model-card-meta { display: flex; flex-wrap: wrap; gap: 6px; }

/* Modals */
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
