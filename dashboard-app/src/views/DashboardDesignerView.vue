<template>
  <div class="designer-view">
    <!-- Dashboard list mode -->
    <div v-if="!activeDashboard">
      <div class="page-header">
        <div>
          <h2 class="page-title">Mis Dashboards</h2>
          <p class="page-subtitle">Diseña y gestiona tus dashboards</p>
        </div>
        <button class="btn btn-primary" @click="showNewModal = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Nuevo Dashboard
        </button>
      </div>

      <div v-if="dashboardStore.allDashboards.length === 0" class="empty-state card">
        <div class="empty-icon">🎨</div>
        <h3>Sin dashboards</h3>
        <p>Crea tu primer dashboard para comenzar a visualizar tus datos.</p>
        <button class="btn btn-primary" @click="showNewModal = true">Crear dashboard</button>
      </div>

      <div v-else class="dashboard-grid-list">
        <div
          v-for="db in dashboardStore.allDashboards"
          :key="db.id"
          class="db-card card"
        >
          <div class="db-card-header">
            <div class="db-icon-wrap">📊</div>
            <div class="db-card-actions">
              <button class="btn btn-secondary btn-sm" @click="openDesigner(db.id)">
                Diseñar
              </button>
              <button class="btn-icon" data-tooltip="Asignar usuarios" @click="openAssignModal(db)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </button>
              <button class="btn-icon" data-tooltip="Ver dashboard" @click="viewDashboard(db.id)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
              <button class="btn-icon" data-tooltip="Eliminar" @click="confirmDelete(db)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--error)">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                  <path d="M10 11v6M14 11v6"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="db-card-body">
            <h3 class="db-name">{{ db.name }}</h3>
            <p class="db-desc">{{ db.description || 'Sin descripción' }}</p>
            <div class="db-card-meta">
              <span class="badge badge-blue">{{ db.widgets.length }} widgets</span>
              <span v-if="db.isPublic" class="badge badge-green">Público</span>
              <span v-if="db.assignedUsers.length > 0" class="badge" style="background:#f9f0ff;color:#722ed1">
                {{ db.assignedUsers.length }} usuario(s)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Designer mode (dashboard open) -->
    <div v-else class="designer-editor">
      <!-- Editor toolbar -->
      <div class="editor-toolbar">
        <button class="btn btn-secondary btn-sm" @click="closeDesigner">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Volver
        </button>

        <div class="toolbar-title">
          <span v-if="!editingTitle" class="db-title-text" @dblclick="startEditTitle">
            {{ activeDashboard.name }}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="edit-hint">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </span>
          <input
            v-else
            ref="titleInput"
            v-model="editTitleValue"
            class="form-input title-edit-input"
            @blur="saveTitle"
            @keyup.enter="saveTitle"
            @keyup.escape="editingTitle = false"
          />
        </div>

        <div class="toolbar-spacer" />

        <!-- Public toggle -->
        <label class="toggle-label">
          <input type="checkbox" v-model="isPublic" @change="togglePublic" />
          <span class="toggle-text">Público</span>
        </label>

        <!-- Design / Preview toggle -->
        <div class="mode-toggle">
          <button
            class="mode-btn"
            :class="{ active: isDesignMode }"
            @click="isDesignMode = true"
          >🎨 Diseñar</button>
          <button
            class="mode-btn"
            :class="{ active: !isDesignMode }"
            @click="isDesignMode = false"
          >👁️ Vista previa</button>
        </div>

        <button
          v-if="isDesignMode"
          class="btn btn-primary btn-sm"
          @click="showAddWidget = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Añadir widget
        </button>
      </div>

      <!-- Description field (design mode) -->
      <div v-if="isDesignMode" class="description-bar">
        <input
          v-model="editDescription"
          type="text"
          class="form-input description-input"
          placeholder="Descripción del dashboard (opcional)..."
          @blur="saveDescription"
        />
      </div>

      <!-- Dashboard canvas -->
      <div class="editor-canvas">
        <DashboardGrid
          :widgets="activeDashboard.widgets"
          :is-design-mode="isDesignMode"
          :dashboard-id="activeDashboard.id"
          @configure-widget="openConfigModal"
          @remove-widget="removeWidget"
        />
      </div>
    </div>

    <!-- ======= MODALS ======= -->

    <!-- New Dashboard Modal -->
    <div v-if="showNewModal" class="modal-overlay" @click.self="showNewModal = false">
      <div class="modal-box" style="max-width: 460px;">
        <div class="modal-header">
          <h3>Nuevo Dashboard</h3>
          <button class="btn-icon" @click="showNewModal = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Nombre *</label>
            <input v-model="newName" class="form-input" placeholder="Ej: Dashboard de Ventas" autofocus />
          </div>
          <div class="form-group">
            <label class="form-label">Descripción</label>
            <input v-model="newDescription" class="form-input" placeholder="Descripción breve..." />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showNewModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="createDashboard" :disabled="!newName.trim()">Crear</button>
        </div>
      </div>
    </div>

    <!-- Assign Users Modal -->
    <div v-if="assigningDashboard" class="modal-overlay" @click.self="assigningDashboard = null">
      <div class="modal-box" style="max-width: 460px;">
        <div class="modal-header">
          <h3>Asignar usuarios — {{ assigningDashboard.name }}</h3>
          <button class="btn-icon" @click="assigningDashboard = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px">
            Selecciona los usuarios que tendrán acceso a este dashboard:
          </p>
          <div class="user-assign-list">
            <div
              v-for="user in authStore.viewers"
              :key="user.id"
              class="user-assign-item"
              :class="{ selected: selectedUsers.includes(user.id) }"
              @click="toggleUser(user.id)"
            >
              <div class="ua-avatar">{{ user.avatar }}</div>
              <div class="ua-info">
                <div class="ua-name">{{ user.name }}</div>
                <div class="ua-email">{{ user.email }}</div>
              </div>
              <div class="ua-check" v-if="selectedUsers.includes(user.id)">✓</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="assigningDashboard = null">Cancelar</button>
          <button class="btn btn-primary" @click="saveAssignment">Guardar asignación</button>
        </div>
      </div>
    </div>

    <!-- Add Widget Panel -->
    <div v-if="showAddWidget" class="modal-overlay" @click.self="showAddWidget = false">
      <div class="modal-box" style="max-width: 500px;">
        <div class="modal-header">
          <h3>Añadir Widget</h3>
          <button class="btn-icon" @click="showAddWidget = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group" style="margin-bottom:16px">
            <label class="form-label">Título del widget</label>
            <input v-model="newWidgetTitle" class="form-input" placeholder="Ej: Ventas Mensuales" />
          </div>
          <label class="form-label" style="margin-bottom:8px">Selecciona el tipo de gráfico</label>
          <div class="widget-type-grid">
            <div
              v-for="ct in chartTypes"
              :key="ct.value"
              class="widget-type-card"
              :class="{ selected: newWidgetType === ct.value }"
              @click="newWidgetType = ct.value"
            >
              <span class="wt-icon">{{ ct.icon }}</span>
              <span class="wt-label">{{ ct.label }}</span>
              <span class="wt-desc">{{ ct.desc }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddWidget = false">Cancelar</button>
          <button class="btn btn-primary" @click="addWidget">Añadir</button>
        </div>
      </div>
    </div>

    <!-- Chart Config Modal -->
    <ChartConfigModal
      v-if="configuringWidget"
      :widget="configuringWidget"
      @close="configuringWidget = null"
      @save="saveWidgetConfig"
    />

    <!-- Delete confirm -->
    <div v-if="deletingDashboard" class="modal-overlay" @click.self="deletingDashboard = null">
      <div class="modal-box" style="max-width: 380px;">
        <div class="modal-header">
          <h3>Eliminar Dashboard</h3>
          <button class="btn-icon" @click="deletingDashboard = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>¿Estás seguro de eliminar <strong>{{ deletingDashboard.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deletingDashboard = null">Cancelar</button>
          <button class="btn btn-danger btn-primary" @click="deleteDashboard" style="background:var(--error);color:#fff;border-color:var(--error)">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import DashboardGrid from '@/components/dashboard/DashboardGrid.vue'
import ChartConfigModal from '@/components/dashboard/ChartConfigModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

// State
const isDesignMode = ref(true)
const showNewModal = ref(false)
const showAddWidget = ref(false)
const configuringWidget = ref(null)
const assigningDashboard = ref(null)
const deletingDashboard = ref(null)
const selectedUsers = ref([])
const newName = ref('')
const newDescription = ref('')
const newWidgetTitle = ref('')
const newWidgetType = ref('bar')
const editingTitle = ref(false)
const editTitleValue = ref('')
const editDescription = ref('')
const titleInput = ref(null)
const isPublic = ref(false)

const chartTypes = [
  { value: 'bar', label: 'Barras', icon: '📊', desc: 'Comparar categorías' },
  { value: 'line', label: 'Líneas', icon: '📈', desc: 'Tendencias en el tiempo' },
  { value: 'pie', label: 'Pastel', icon: '🥧', desc: 'Distribución porcentual' },
  { value: 'gauge', label: 'Gauge', icon: '🎯', desc: 'Valor único / KPI' },
  { value: 'radar', label: 'Radar', icon: '🕸️', desc: 'Múltiples variables' },
  { value: 'combined', label: 'Combinado', icon: '📉', desc: 'Barras + Líneas' }
]

// Active dashboard from route
const activeDashboard = computed(() => {
  const id = route.params.id
  if (!id) return null
  return dashboardStore.allDashboards.find(d => d.id === id) || null
})

// Watch route changes
watch(() => route.params.id, (id) => {
  if (id) {
    const db = dashboardStore.allDashboards.find(d => d.id === id)
    if (db) {
      editDescription.value = db.description || ''
      isPublic.value = db.isPublic || false
      uiStore.setBreadcrumbs(['Diseño', db.name])
    }
  } else {
    uiStore.setBreadcrumbs(['Diseño', 'Mis Dashboards'])
  }
}, { immediate: true })

// Check for ?new=1 in query
watch(() => route.query.new, (v) => {
  if (v === '1') showNewModal.value = true
}, { immediate: true })

function openDesigner(id) {
  router.push(`/designer/${id}`)
}

function closeDesigner() {
  router.push('/designer')
}

function viewDashboard(id) {
  router.push(`/dashboard/${id}`)
}

function openAssignModal(db) {
  assigningDashboard.value = db
  selectedUsers.value = [...db.assignedUsers]
}

function toggleUser(userId) {
  const idx = selectedUsers.value.indexOf(userId)
  if (idx === -1) selectedUsers.value.push(userId)
  else selectedUsers.value.splice(idx, 1)
}

function saveAssignment() {
  if (!assigningDashboard.value) return
  dashboardStore.assignDashboardToUsers(assigningDashboard.value.id, selectedUsers.value)
  uiStore.addAlert({
    type: 'success',
    message: `Dashboard "${assigningDashboard.value.name}" asignado a ${selectedUsers.value.length} usuario(s)`
  })
  assigningDashboard.value = null
}

function confirmDelete(db) {
  deletingDashboard.value = db
}

function deleteDashboard() {
  if (!deletingDashboard.value) return
  const name = deletingDashboard.value.name
  dashboardStore.deleteDashboard(deletingDashboard.value.id)
  deletingDashboard.value = null
  if (activeDashboard.value?.id === deletingDashboard.value?.id) {
    router.push('/designer')
  }
  uiStore.addAlert({ type: 'success', message: `Dashboard "${name}" eliminado` })
}

function createDashboard() {
  if (!newName.value.trim()) return
  const db = dashboardStore.createDashboard(newName.value.trim(), newDescription.value.trim(), authStore.user.id)
  showNewModal.value = false
  newName.value = ''
  newDescription.value = ''
  // Remove ?new query param and navigate
  router.push(`/designer/${db.id}`)
}

function addWidget() {
  if (!activeDashboard.value) return
  const widget = dashboardStore.addWidget(activeDashboard.value.id, {
    title: newWidgetTitle.value || 'Nuevo Gráfico',
    chartType: newWidgetType.value,
    useMockData: true
  })
  showAddWidget.value = false
  newWidgetTitle.value = ''
  newWidgetType.value = 'bar'
  // Open config immediately
  configuringWidget.value = widget
}

function removeWidget(widgetId) {
  if (!activeDashboard.value) return
  dashboardStore.removeWidget(activeDashboard.value.id, widgetId)
}

function openConfigModal(widget) {
  configuringWidget.value = JSON.parse(JSON.stringify(widget))
}

function saveWidgetConfig(updatedWidget) {
  if (!activeDashboard.value) return
  dashboardStore.updateWidget(activeDashboard.value.id, updatedWidget.id, updatedWidget)
  configuringWidget.value = null
  uiStore.addAlert({ type: 'success', message: 'Widget actualizado correctamente' })
}

function startEditTitle() {
  editTitleValue.value = activeDashboard.value?.name || ''
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}

function saveTitle() {
  if (activeDashboard.value && editTitleValue.value.trim()) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { name: editTitleValue.value.trim() })
    uiStore.setBreadcrumbs(['Diseño', editTitleValue.value.trim()])
  }
  editingTitle.value = false
}

function saveDescription() {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { description: editDescription.value })
  }
}

function togglePublic() {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { isPublic: isPublic.value })
  }
}
</script>

<style scoped>
.designer-view { display: flex; flex-direction: column; height: 100%; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 20px; gap: 16px;
}
.page-title { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

/* Dashboard cards */
.dashboard-grid-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.db-card { overflow: hidden; }
.db-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px 0;
}
.db-icon-wrap { font-size: 24px; }
.db-card-actions { display: flex; align-items: center; gap: 4px; }
.db-card-body { padding: 10px 16px 16px; }
.db-name { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.db-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 12px; }
.db-card-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* Editor */
.designer-editor { display: flex; flex-direction: column; height: 100%; }

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.toolbar-title { flex: 1; min-width: 0; }
.db-title-text {
  font-size: 16px; font-weight: 600; color: var(--text);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
}
.db-title-text:hover { color: var(--primary); }
.edit-hint { opacity: 0.5; }
.title-edit-input { max-width: 300px; font-size: 15px; font-weight: 600; }
.toolbar-spacer { flex: 1; }

.toggle-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); cursor: pointer;
  flex-shrink: 0;
}
.toggle-text { white-space: nowrap; }

.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}
.mode-btn {
  padding: 6px 12px; border: none; background: transparent;
  font-size: 13px; cursor: pointer; color: var(--text-secondary);
  transition: all 0.15s; white-space: nowrap;
}
.mode-btn:hover { background: var(--bg); }
.mode-btn.active { background: var(--primary); color: #fff; }

.description-bar { margin-bottom: 10px; }
.description-input { font-size: 13px; }

.editor-canvas {
  flex: 1;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: auto;
  box-shadow: var(--shadow);
  padding: 8px;
  min-height: 400px;
}

/* Add widget types */
.widget-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.widget-type-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px; border: 2px solid var(--border);
  border-radius: 8px; cursor: pointer; transition: all 0.15s; text-align: center;
}
.widget-type-card:hover { border-color: var(--primary); background: var(--primary-light); }
.widget-type-card.selected { border-color: var(--primary); background: var(--primary-light); }
.wt-icon { font-size: 28px; margin-bottom: 6px; }
.wt-label { font-size: 13px; font-weight: 600; color: var(--text); }
.wt-desc { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

/* Assign users */
.user-assign-list { display: flex; flex-direction: column; gap: 8px; }
.user-assign-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border: 2px solid var(--border);
  border-radius: 8px; cursor: pointer; transition: all 0.15s;
}
.user-assign-item:hover { border-color: var(--primary); }
.user-assign-item.selected { border-color: var(--primary); background: var(--primary-light); }
.ua-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--primary); color: #fff;
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.ua-info { flex: 1; min-width: 0; }
.ua-name { font-size: 14px; font-weight: 500; color: var(--text); }
.ua-email { font-size: 12px; color: var(--text-secondary); }
.ua-check { color: var(--primary); font-weight: 700; font-size: 16px; }
</style>
