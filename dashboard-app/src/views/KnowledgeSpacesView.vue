<template>
  <div class="min-h-[calc(100vh-64px)] p-8">
    <!-- Page Header -->
    <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
      <div class="space-y-1">
        <span class="text-xs font-semibold tracking-wider text-blue-600 uppercase">Gestión de Datos</span>
        <h1 class="font-h1 text-h1 text-slate-900">Knowledge Spaces</h1>
        <p class="font-body-md text-slate-500 max-w-2xl">Gestiona tus espacios de conocimiento para organizar y documentar la estructura de tus datos.</p>
      </div>
      <button
        class="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 active:scale-95"
        @click="showNewModal = true">
        <span class="material-symbols-outlined text-lg">add</span>
        Nuevo Knowledge Space
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="spacesStore.allSpaces.length === 0" class="max-w-[1600px] mx-auto">
      <div class="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
          <span class="material-symbols-outlined text-3xl text-slate-400">hub</span>
        </div>
        <h3 class="text-lg font-semibold text-slate-900">Sin Knowledge Spaces</h3>
        <p class="text-sm text-slate-500 max-w-md">Crea tu primer Knowledge Space para comenzar a organizar tus datos.</p>
        <button
          class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-md"
          @click="showNewModal = true">
          <span class="material-symbols-outlined text-lg">add</span>
          Crear Knowledge Space
        </button>
      </div>
    </div>

    <!-- Knowledge Spaces grid -->
    <div v-else class="max-w-[1600px] mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <!-- Knowledge Space cards -->
        <div
          v-for="(space, idx) in spacesStore.allSpaces"
          :key="space.id"
          class="kspace-card"
          :style="{ animationDelay: `${idx * 50}ms` }">
          <!-- Card Header with ID badge -->
          <div class="kspace-card-header">
            <div class="kspace-id-badge">ID: {{ formatId(space.id) }}</div>
          </div>

          <!-- Card Body -->
          <div class="kspace-card-body">
            <!-- Icon and Title -->
            <div class="kspace-card-icon-wrapper">
              <div class="kspace-card-icon">
                <span class="material-symbols-outlined text-3xl text-blue-600">hub</span>
              </div>
            </div>

            <h3 class="kspace-card-title">{{ space.name }}</h3>
            <p class="kspace-card-description">{{ space.description || 'Sin descripción' }}</p>

            <!-- Database Type Badge -->
            <div class="kspace-card-db-type">
              <span class="material-symbols-outlined text-sm">database</span>
              {{ space.config?.dbType || 'PostgreSQL' }}
            </div>

            <!-- Stats Row -->
            <div class="kspace-card-stats">
              <div class="kspace-stat">
                <span class="material-symbols-outlined text-sm">schema</span>
                <span>{{ space.config?.schemaCount || 0 }} esquemas</span>
              </div>
              <div class="kspace-stat">
                <span class="material-symbols-outlined text-sm">table</span>
                <span>{{ space.config?.tableCount || 0 }} tablas</span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="kspace-card-progress">
              <div class="kspace-progress-header">
                <span class="kspace-progress-label">Documentación</span>
                <span class="kspace-progress-value">{{ space.config?.documentationProgress || 0 }}%</span>
              </div>
              <div class="kspace-progress-bar">
                <div 
                  class="kspace-progress-fill"
                  :style="{ width: `${space.config?.documentationProgress || 0}%` }">
                </div>
              </div>
            </div>
          </div>

          <!-- Card Footer with Actions -->
          <div class="kspace-card-footer">
            <div class="kspace-card-actions">
              <button class="kspace-action" title="Ver detalles" @click="openSpace(space.id)">
                <span class="material-symbols-outlined text-lg">visibility</span>
              </button>
              <button class="kspace-action" title="Editar" @click="openEditModal(space)">
                <span class="material-symbols-outlined text-lg">edit</span>
              </button>
              <button class="kspace-action kspace-action--danger" title="Eliminar" @click="confirmDelete(space)">
                <span class="material-symbols-outlined text-lg">delete</span>
              </button>
            </div>
          </div>
        </div>

        <!-- New Knowledge Space card -->
        <button
          class="group border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:border-blue-500 hover:bg-blue-50/30 transition-all min-h-[380px]"
          @click="showNewModal = true">
          <div class="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
            <span class="material-symbols-outlined text-2xl text-slate-400 group-hover:text-blue-600 transition-colors">add</span>
          </div>
          <div class="text-center">
            <span class="block text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">Nuevo Knowledge Space</span>
            <span class="block text-xs text-slate-500">Crea un espacio para tus datos</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Modal: Nuevo Knowledge Space -->
    <div v-if="showNewModal" class="kspace-modal-overlay" @click.self="cancelNew">
      <div class="kspace-modal-container">
        <!-- Header -->
        <div class="kspace-modal-header">
          <div class="kspace-modal-header-content">
            <div>
              <h2 class="kspace-modal-title">Nuevo Knowledge Space</h2>
              <p class="kspace-modal-subtitle">Crea un nuevo espacio para organizar y documentar tus datos.</p>
            </div>
            <button class="kspace-modal-close" @click="cancelNew">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
        
        <!-- Body -->
        <div class="kspace-modal-body">
          <!-- Nombre -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Nombre</label>
            <input 
              v-model="newName" 
              type="text" 
              class="kspace-modal-input" 
              placeholder="Ej: Ventas Corporativas"
              autofocus />
          </div>
          
          <!-- Tipo de base de datos -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Tipo de base de datos</label>
            <div class="kspace-modal-select-wrapper">
              <select v-model="newDbType" class="kspace-modal-select">
                <option value="PostgreSQL">PostgreSQL</option>
                <option value="MySQL">MySQL</option>
                <option value="MongoDB">MongoDB</option>
                <option value="SQL Server">SQL Server</option>
                <option value="Oracle">Oracle</option>
                <option value="SQLite">SQLite</option>
              </select>
              <span class="material-symbols-outlined kspace-select-icon">expand_more</span>
            </div>
          </div>
          
          <!-- Descripción -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Descripción</label>
            <textarea 
              v-model="newDescription" 
              class="kspace-modal-textarea" 
              rows="3" 
              placeholder="Describe el propósito de este Knowledge Space..."></textarea>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="kspace-modal-footer">
          <button class="kspace-modal-btn-cancel" @click="cancelNew">Cancelar</button>
          <button class="kspace-modal-btn-create" :disabled="!newName.trim()" @click="createSpace">
            <span>Crear</span>
            <span class="material-symbols-outlined" style="font-size: 16px;">add_circle</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Editar Knowledge Space -->
    <div v-if="editTarget" class="kspace-modal-overlay" @click.self="cancelEdit">
      <div class="kspace-modal-container">
        <!-- Header -->
        <div class="kspace-modal-header">
          <div class="kspace-modal-header-content">
            <div>
              <h2 class="kspace-modal-title">Editar Knowledge Space</h2>
              <p class="kspace-modal-subtitle">Modifica los datos de tu espacio de conocimiento.</p>
            </div>
            <button class="kspace-modal-close" @click="cancelEdit">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
        
        <!-- Body -->
        <div class="kspace-modal-body">
          <!-- Nombre -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Nombre</label>
            <input 
              v-model="editName" 
              type="text" 
              class="kspace-modal-input" 
              placeholder="Ej: Ventas Corporativas" />
          </div>
          
          <!-- Tipo de base de datos -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Tipo de base de datos</label>
            <div class="kspace-modal-select-wrapper">
              <select v-model="editDbType" class="kspace-modal-select">
                <option value="PostgreSQL">PostgreSQL</option>
                <option value="MySQL">MySQL</option>
                <option value="MongoDB">MongoDB</option>
                <option value="SQL Server">SQL Server</option>
                <option value="Oracle">Oracle</option>
                <option value="SQLite">SQLite</option>
              </select>
              <span class="material-symbols-outlined kspace-select-icon">expand_more</span>
            </div>
          </div>
          
          <!-- Descripción -->
          <div class="kspace-modal-field">
            <label class="kspace-modal-label">Descripción</label>
            <textarea 
              v-model="editDescription" 
              class="kspace-modal-textarea" 
              rows="3" 
              placeholder="Describe el propósito de este Knowledge Space..."></textarea>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="kspace-modal-footer">
          <button class="kspace-modal-btn-cancel" @click="cancelEdit">Cancelar</button>
          <button class="kspace-modal-btn-create" :disabled="!editName.trim()" @click="doUpdate">
            <span>Guardar</span>
            <span class="material-symbols-outlined" style="font-size: 16px;">save</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Confirmar eliminar -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="deleteTarget = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[420px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar Knowledge Space</h3>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useKnowledgeSpacesStore } from '@/stores/knowledgeSpaces'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const spacesStore = useKnowledgeSpacesStore()
const uiStore = useUIStore()

// Load data from backend on mount
onMounted(async () => {
  await spacesStore.loadFromBackend()
  uiStore.setBreadcrumbs(['Knowledge Spaces'])
})

// New modal state
const showNewModal = ref(false)
const newName = ref('')
const newDescription = ref('')
const newDbType = ref('PostgreSQL')

// Edit modal state
const editTarget = ref(null)
const editName = ref('')
const editDescription = ref('')
const editDbType = ref('PostgreSQL')

// Delete modal state
const deleteTarget = ref(null)

// Format ID for display
function formatId(id) {
  if (!id) return 'KS-000'
  // Extract last part of UUID or use full string
  const parts = id.toString().split('-')
  return `KS-${parts[parts.length - 1].substring(0, 4).toUpperCase()}`
}

// Cancel new modal
function cancelNew() {
  showNewModal.value = false
  newName.value = ''
  newDescription.value = ''
  newDbType.value = 'PostgreSQL'
}

// Create new Knowledge Space
async function createSpace() {
  if (!newName.value.trim()) return
  
  try {
    await spacesStore.createSpace({
      name: newName.value.trim(),
      description: newDescription.value.trim(),
      config: {
        dbType: newDbType.value,
        schemaCount: 0,
        tableCount: 0,
        documentationProgress: 0
      }
    })
    cancelNew()
    uiStore.addAlert({
      type: 'success',
      message: 'Knowledge Space creado exitosamente'
    })
  } catch (err) {
    console.error('Failed to create knowledge space:', err)
    uiStore.addAlert({
      type: 'error',
      message: 'Error al crear el Knowledge Space: ' + (err.message || 'Error desconocido')
    })
  }
}

// Open edit modal
function openEditModal(space) {
  editTarget.value = space
  editName.value = space.name
  editDescription.value = space.description || ''
  editDbType.value = space.config?.dbType || 'PostgreSQL'
}

// Cancel edit
function cancelEdit() {
  editTarget.value = null
  editName.value = ''
  editDescription.value = ''
  editDbType.value = 'PostgreSQL'
}

// Update Knowledge Space
async function doUpdate() {
  if (!editTarget.value || !editName.value.trim()) return
  
  try {
    await spacesStore.updateSpace(editTarget.value.id, {
      name: editName.value.trim(),
      description: editDescription.value.trim(),
      config: {
        ...editTarget.value.config,
        dbType: editDbType.value
      }
    })
    cancelEdit()
    uiStore.addAlert({
      type: 'success',
      message: 'Knowledge Space actualizado exitosamente'
    })
  } catch (err) {
    console.error('Failed to update knowledge space:', err)
    uiStore.addAlert({
      type: 'error',
      message: 'Error al actualizar el Knowledge Space: ' + (err.message || 'Error desconocido')
    })
  }
}

// Open Knowledge Space detail
function openSpace(id) {
  router.push(`/knowledge-spaces/${id}`)
}

// Confirm delete
function confirmDelete(space) {
  deleteTarget.value = space
}

// Delete Knowledge Space
async function doDelete() {
  if (!deleteTarget.value) return
  
  try {
    await spacesStore.deleteSpace(deleteTarget.value.id)
    deleteTarget.value = null
    uiStore.addAlert({
      type: 'success',
      message: 'Knowledge Space eliminado exitosamente'
    })
  } catch (err) {
    console.error('Failed to delete knowledge space:', err)
    uiStore.addAlert({
      type: 'error',
      message: 'Error al eliminar el Knowledge Space: ' + (err.message || 'Error desconocido')
    })
  }
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

/* Knowledge Space Card Styles */
.kspace-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.25s ease, transform 0.2s ease;
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
  min-height: 380px;
}

.kspace-card:hover {
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.1);
  transform: translateY(-2px);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Card Header */
.kspace-card-header {
  position: relative;
  height: 60px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 12px;
}

.kspace-id-badge {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.02em;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Card Body */
.kspace-card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.kspace-card-icon-wrapper {
  margin-bottom: 16px;
}

.kspace-card-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.kspace-card-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin-bottom: 8px;
}

.kspace-card-description {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 16px;
}

/* Database Type Badge */
.kspace-card-db-type {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 20px;
  margin-bottom: 16px;
}

/* Stats Row */
.kspace-card-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.kspace-stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

/* Progress Bar */
.kspace-card-progress {
  width: 100%;
  margin-top: auto;
}

.kspace-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kspace-progress-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.kspace-progress-value {
  font-size: 12px;
  color: #2563eb;
  font-weight: 600;
}

.kspace-progress-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.kspace-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
  border-radius: 3px;
  transition: width 0.4s ease;
}

/* Card Footer */
.kspace-card-footer {
  padding: 16px 20px;
  border-top: 1px solid #f1f5f9;
  background: #fafafa;
}

.kspace-card-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.kspace-action {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.kspace-action:hover {
  color: #2563eb;
  background: #eff6ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15);
}

.kspace-action--danger:hover {
  color: #dc2626;
  background: #fef2f2;
  box-shadow: 0 2px 4px rgba(220, 38, 38, 0.15);
}

/* Modal Styles */
.kspace-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6);
  padding: 16px;
}

.kspace-modal-container {
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

.kspace-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: white;
  flex-shrink: 0;
}

.kspace-modal-header-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.kspace-modal-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.kspace-modal-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.kspace-modal-close {
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

.kspace-modal-close:hover {
  background: #f1f5f9;
  color: #334155;
}

.kspace-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.kspace-modal-field {
  margin-bottom: 20px;
}

.kspace-modal-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 6px;
}

.kspace-modal-input,
.kspace-modal-textarea {
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

.kspace-modal-input::placeholder,
.kspace-modal-textarea::placeholder {
  color: #94a3b8;
}

.kspace-modal-input:focus,
.kspace-modal-textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.kspace-modal-textarea {
  resize: none;
  min-height: 80px;
}

.kspace-modal-select-wrapper {
  position: relative;
}

.kspace-modal-select {
  width: 100%;
  padding: 10px 14px;
  padding-right: 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
  appearance: none;
  cursor: pointer;
}

.kspace-modal-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.kspace-select-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  pointer-events: none;
  font-size: 20px;
}

.kspace-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.kspace-modal-btn-cancel {
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

.kspace-modal-btn-cancel:hover {
  background: #f1f5f9;
}

.kspace-modal-btn-create {
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

.kspace-modal-btn-create:hover:not(:disabled) {
  background: #1d4ed8;
}

.kspace-modal-btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
