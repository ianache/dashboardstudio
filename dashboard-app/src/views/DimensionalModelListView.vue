<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Page Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <h1 class="font-h1 text-h1 text-slate-900">Modelos Dimensionales</h1>
        <p class="font-body-md text-slate-500 max-w-2xl">Diseña y gestiona tus modelos de datos dimensionales para documentar la estructura de tus datos.</p>
      </div>
      <div class="flex items-center gap-3">
        <input ref="importInput" type="file" accept=".yaml,.yml" style="display:none" @change="handleImport" />
        <button
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm"
          @click="importInput.click()">
          <span class="material-symbols-outlined text-lg">download</span>
          Importar
        </button>
        <button
          class="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 active:scale-95"
          @click="showNewModal = true">
          <span class="material-symbols-outlined text-lg">add</span>
          Nuevo
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="modelStore.allModels.length === 0" class="max-w-[1600px] mx-auto">
      <div class="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
          <span class="material-symbols-outlined text-3xl text-slate-400">account_tree</span>
        </div>
        <h3 class="text-lg font-semibold text-slate-900">Sin modelos dimensionales</h3>
        <p class="text-sm text-slate-500 max-w-md">Crea tu primer modelo dimensional para documentar la estructura de tus datos.</p>
        <button
          class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md"
          @click="showNewModal = true">
          <span class="material-symbols-outlined text-lg">add</span>
          Crear modelo
        </button>
      </div>
    </div>

    <!-- Models grid -->
    <div v-else class="max-w-[1600px] mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
          @design="openEditor(model.id)"
          @edit="openEditModal(model)"
          @export="exportModel(model.id)"
          @delete="confirmDelete(model)"
          @update:name="val => modelStore.updateModel(model.id, { name: val })"
          @update:description="val => modelStore.updateModel(model.id, { description: val })"
        />
        <!-- New model card -->
        <button
          class="group border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:border-blue-500 hover:bg-blue-50/30 transition-all min-h-[280px]"
          @click="showNewModal = true">
          <div class="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
            <span class="material-symbols-outlined text-2xl text-slate-400 group-hover:text-blue-600 transition-colors">add</span>
          </div>
          <div class="text-center">
            <span class="block text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">Nuevo modelo</span>
            <span class="block text-xs text-slate-500">Comienza un modelo desde cero</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Modal: Nuevo Modelo -->
    <div v-if="showNewModal" class="model-new-overlay" @click.self="cancelNew">
      <div class="model-new-container">
        <!-- Header -->
        <div class="model-new-header">
          <div class="model-new-header-content">
            <div>
              <h2 class="model-new-title">{{ isEditMode ? 'Editar Modelo Dimensional' : 'Nuevo Modelo Dimensional' }}</h2>
              <p class="model-new-subtitle">Defina los parámetros para su nuevo esquema de datos inteligente.</p>
            </div>
            <button class="model-new-close" @click="cancelNew">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
        
        <!-- Body -->
        <div class="model-new-body">
          <!-- Nombre -->
          <div class="model-new-field">
            <label class="model-new-label">Nombre</label>
            <input 
              v-model="newName" 
              type="text" 
              class="model-new-input" 
              placeholder="Ej: Analítica de Ventas Trimestral"
              autofocus />
          </div>
          
          <!-- Knowledge Space -->
          <div class="model-new-field" style="position: relative;">
            <label class="model-new-label">Knowledge Space</label>
            <div class="model-new-select" @click="showKnowledgeSpaceDropdown = !showKnowledgeSpaceDropdown">
              <span class="material-symbols-outlined" style="color: #2563eb; font-size: 20px;">hub</span>
              <span v-if="selectedKnowledgeSpace" style="color: #0f172a; font-size: 14px;">{{ selectedKnowledgeSpace }}</span>
              <span v-else style="color: #94a3b8; font-size: 14px;">Seleccionar Knowledge Space...</span>
              <span class="material-symbols-outlined" style="color: #94a3b8; margin-left: auto; font-size: 20px;">expand_more</span>
            </div>
            
            <!-- Dropdown -->
            <div v-if="showKnowledgeSpaceDropdown" class="model-new-dropdown">
              <div class="model-new-dropdown-search">
                <span class="material-symbols-outlined" style="color: #94a3b8; font-size: 16px;">search</span>
                <input 
                  v-model="knowledgeSpaceSearch" 
                  type="text" 
                  placeholder="Buscar space..." 
                  @click.stop />
              </div>
              <ul class="model-new-dropdown-list">
                <li 
                  v-for="space in filteredKnowledgeSpaces" 
                  :key="space.id"
                  class="model-new-dropdown-item"
                  :class="{ 'model-new-dropdown-item--selected': selectedKnowledgeSpace === space.name }"
                  @click.stop="selectKnowledgeSpace(space)">
                  <span class="material-symbols-outlined" style="color: #2563eb; font-size: 18px;">hub</span>
                  <span style="font-size: 14px; color: #0f172a;">{{ space.name }}</span>
                  <span v-if="selectedKnowledgeSpace === space.name" class="material-symbols-outlined" style="color: #2563eb; margin-left: auto; font-size: 16px;">check</span>
                </li>
              </ul>
            </div>
          </div>
          
          <!-- Descripción -->
          <div class="model-new-field">
            <label class="model-new-label">Descripción</label>
            <textarea 
              v-model="newDescription" 
              class="model-new-textarea" 
              rows="3" 
              placeholder="Proporcione contexto sobre el propósito de este modelo..."></textarea>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="model-new-footer">
          <button class="model-new-btn-cancel" @click="cancelNew">Cancelar</button>
          <button class="model-new-btn-create" :disabled="!newName.trim() || !selectedKnowledgeSpace" @click="saveModel">
            <span>{{ isEditMode ? 'Guardar' : 'Crear' }}</span>
            <span class="material-symbols-outlined" style="font-size: 16px;">{{ isEditMode ? 'save' : 'add_circle' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Confirmar eliminar -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar modelo</h3>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">¿Eliminar <strong>{{ deleteTarget.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50" @click="deleteTarget = null">Cancelar</button>
          <button class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700" @click="doDelete">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDimensionalModelStore } from '@/stores/dimensionalModel'
import { useUIStore } from '@/stores/ui'
import { useKnowledgeSpacesStore } from '@/stores/knowledgeSpaces'
import yaml from 'js-yaml'
import ModelCard from '@/components/dimensional-model/ModelCard.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const modelStore = useDimensionalModelStore()
const uiStore = useUIStore()
const knowledgeSpacesStore = useKnowledgeSpacesStore()

// Load data from backend on mount
onMounted(async () => {
  await Promise.all([
    modelStore.loadFromBackend(),
    knowledgeSpacesStore.loadFromBackend()
  ])
})

const showNewModal = ref(false)
const newName = ref('')
const newDescription = ref('')
const deleteTarget = ref(null)
const importInput = ref(null)

// Edit mode
const editModelId = ref(null)
const isEditMode = computed(() => !!editModelId.value)

// Knowledge Space Combobox
const showKnowledgeSpaceDropdown = ref(false)
const knowledgeSpaceSearch = ref('')
const selectedKnowledgeSpace = ref('')

const filteredKnowledgeSpaces = computed(() => {
  return knowledgeSpacesStore.filteredSpaces(knowledgeSpaceSearch.value)
})

function selectKnowledgeSpace(space) {
  selectedKnowledgeSpace.value = space.name
  knowledgeSpacesStore.setSelectedSpace(space)
  showKnowledgeSpaceDropdown.value = false
  knowledgeSpaceSearch.value = ''
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
  selectedKnowledgeSpace.value = ''
  showKnowledgeSpaceDropdown.value = false
  knowledgeSpaceSearch.value = ''
  editModelId.value = null
}

function openEditModal(model) {
  editModelId.value = model.id
  newName.value = model.name
  newDescription.value = model.description || ''
  // Try to find and set the knowledge space
  const spaceId = model.knowledgeSpaceId
  if (spaceId) {
    const space = knowledgeSpacesStore.getSpaceById(spaceId)
    if (space) {
      selectedKnowledgeSpace.value = space.name
    }
  }
  showNewModal.value = true
}

async function saveModel() {
  if (!newName.value.trim() || !selectedKnowledgeSpace.value) return
  
  // Find the selected knowledge space to get its ID
  const selectedSpace = knowledgeSpacesStore.getSpaceByName(selectedKnowledgeSpace.value)
  
  if (isEditMode.value) {
    // Update existing model
    try {
      await modelStore.updateModel(editModelId.value, {
        name: newName.value.trim(),
        description: newDescription.value.trim(),
        knowledgeSpaceId: selectedSpace?.id || null,
        knowledgeSpaceName: selectedKnowledgeSpace.value
      })
      cancelNew()
      uiStore.addAlert({
        type: 'success',
        message: 'Modelo actualizado correctamente'
      })
    } catch (err) {
      console.error('Failed to update model:', err)
      uiStore.addAlert({
        type: 'error',
        message: 'Error al actualizar el modelo: ' + (err.message || 'Error desconocido')
      })
    }
  } else {
    // Create new model
    try {
      const model = await modelStore.createModel({
        name: newName.value.trim(),
        description: newDescription.value.trim(),
        knowledgeSpaceId: selectedSpace?.id || null,
        knowledgeSpaceName: selectedKnowledgeSpace.value,
        createdBy: authStore.user?.id || ''
      })
      cancelNew()
      router.push(`/models/${model.id}`)
    } catch (err) {
      console.error('Failed to create model:', err)
      uiStore.addAlert({
        type: 'error',
        message: 'Error al crear el modelo: ' + (err.message || 'Error desconocido')
      })
    }
  }
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
/* Material Symbols font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

/* Custom font classes matching the design system */
.font-h1 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.font-body-md {
  font-family: 'Inter', system-ui, sans-serif;
}

.text-h1 {
  font-size: 36px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-weight: 700;
}

/* Nuevo Modelo Modal Styles */
.model-new-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6);
  padding: 16px;
}

.model-new-container {
  background: white;
  width: 100%;
  max-width: 512px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 32px);
  overflow: hidden;
}

.model-new-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: white;
  flex-shrink: 0;
}

.model-new-header-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.model-new-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.model-new-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.model-new-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
  flex-shrink: 0;
}

.model-new-close:hover {
  background: #f1f5f9;
  color: #334155;
}

.model-new-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.model-new-field {
  margin-bottom: 20px;
}

.model-new-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 6px;
}

.model-new-input,
.model-new-textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.model-new-input::placeholder,
.model-new-textarea::placeholder {
  color: #94a3b8;
}

.model-new-input:focus,
.model-new-textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.model-new-textarea {
  resize: none;
  min-height: 80px;
}

.model-new-select {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.model-new-select:hover {
  border-color: #94a3b8;
}

.model-new-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 1001;
  overflow: hidden;
}

.model-new-dropdown-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.model-new-dropdown-search input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  padding: 0;
}

.model-new-dropdown-list {
  max-height: 200px;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: 0;
}

.model-new-dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.model-new-dropdown-item:hover {
  background: #eff6ff;
}

.model-new-dropdown-item--selected {
  background: #eff6ff;
}

.model-new-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.model-new-btn-cancel {
  padding: 10px 20px;
  border: 1px solid #cbd5e1;
  background: white;
  color: #334155;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.model-new-btn-cancel:hover {
  background: #f1f5f9;
}

.model-new-btn-create {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
}

.model-new-btn-create:hover:not(:disabled) {
  background: #1d4ed8;
}

.model-new-btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
