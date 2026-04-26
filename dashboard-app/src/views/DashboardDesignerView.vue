<template>
  <div class="designer-view">
    <!-- Dashboard list mode -->
    <div v-if="!activeDashboard">
      <!-- Page header -->
      <div class="ds-page-header">
        <div>
          <h2 class="ds-page-title">Mis Dashboards</h2>
          <p class="ds-page-subtitle">Diseña y gestiona tus dashboards para obtener insights en tiempo real.</p>
        </div>
        <div class="ds-header-actions">
          <input ref="importFileInput" type="file" accept=".json" style="display:none" @change="handleImportFile" />
          <button class="ds-btn-secondary" @click="importFileInput.click()">
            <MIcon icon="upload" :size="18" /> Importar
          </button>
          <button class="ds-btn-primary" @click="showNewModal = true">
            <MIcon icon="add" :size="18" /> Nuevo
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="dashboardStore.allDashboards.length === 0" class="empty-state card">
        <div class="empty-icon">🎨</div>
        <h3>Sin dashboards</h3>
        <p>Crea tu primer dashboard para comenzar a visualizar tus datos.</p>
        <button class="btn btn-primary" @click="showNewModal = true">Crear dashboard</button>
      </div>

      <!-- Designer grid -->
      <div v-else class="designer-grid">
        <DesignerCard
          v-for="(db, idx) in dashboardStore.allDashboards"
          :key="db.id"
          :name="db.name"
          :description="db.description"
          :widget-count="db.widgets.length"
          :is-public="db.isPublic"
          :assigned-users-count="db.assignedUsers.length"
          :color-index="idx"
          :category-icon="categoryIcons[idx % categoryIcons.length]"
          @design="openDesigner(db.id)"
          @assign="openAssignModal(db)"
          @view="viewDashboard(db.id)"
          @export="handleExportDashboard(db)"
          @delete="confirmDelete(db)"
        />

        <!-- Create new card -->
        <button class="designer-new-card" @click="showNewModal = true">
          <div class="new-card-icon-wrap">
            <MIcon icon="add" :size="28" />
          </div>
          <span class="new-card-title">Nuevo Dashboard</span>
          <span class="new-card-sub">Comienza un diseño desde cero</span>
        </button>
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

        <!-- Palette picker (design mode only) -->
        <div v-if="isDesignMode" class="palette-picker" v-click-outside="() => paletteOpen = false">
          <button class="palette-trigger" @click="paletteOpen = !paletteOpen" :title="'Paleta del dashboard'">
            <div class="palette-trigger-swatches" v-if="activeDashboardPalette">
              <span
                v-for="c in activeDashboardPalette.colors.slice(0, 5)"
                :key="c"
                class="palette-trigger-swatch"
                :style="{ background: c }"
              />
            </div>
            <div class="palette-trigger-swatches palette-trigger-swatches--default" v-else>
              <span class="palette-trigger-swatch" style="background:#1890ff"/>
              <span class="palette-trigger-swatch" style="background:#52c41a"/>
              <span class="palette-trigger-swatch" style="background:#faad14"/>
              <span class="palette-trigger-swatch" style="background:#f5222d"/>
              <span class="palette-trigger-swatch" style="background:#722ed1"/>
            </div>
            <span class="palette-trigger-label">{{ activeDashboardPalette?.label ?? 'Por defecto' }}</span>
            <svg class="palette-trigger-arrow" :class="{ open: paletteOpen }" width="12" height="12" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="palette-dropdown" v-if="paletteOpen">
            <div
              class="palette-option"
              :class="{ selected: !activeDashboard?.colorPalette }"
              @click="selectDashboardPalette(null)"
            >
              <span class="palette-option-label">Por defecto</span>
              <div class="palette-option-swatches">
                <span class="palette-option-swatch" style="background:#1890ff"/>
                <span class="palette-option-swatch" style="background:#52c41a"/>
                <span class="palette-option-swatch" style="background:#faad14"/>
                <span class="palette-option-swatch" style="background:#f5222d"/>
                <span class="palette-option-swatch" style="background:#722ed1"/>
                <span class="palette-option-swatch" style="background:#13c2c2"/>
              </div>
            </div>
            <div
              v-for="palette in paletteStore.allPalettes"
              :key="palette.id"
              class="palette-option"
              :class="{ selected: activeDashboard?.colorPalette === palette.id }"
              @click="selectDashboardPalette(palette.id)"
            >
              <span class="palette-option-label">{{ palette.label }}</span>
              <div class="palette-option-swatches">
                <span
                  v-for="c in palette.colors.slice(0, 6)"
                  :key="c"
                  class="palette-option-swatch"
                  :style="{ background: c }"
                />
              </div>
            </div>
          </div>
        </div>

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
          @click="addWidget"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Añadir widget
        </button>
        <button
          v-if="isDesignMode"
          class="btn-ai-assist"
          style="margin-left:8px"
          @click="aiAssistOpen = true"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
          </svg>
          IA Assist
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

      <!-- Filter bar -->
      <DashboardFilterBar
        v-if="activeDashboard.filters?.length > 0 || isDesignMode"
        :dashboard-id="activeDashboard.id"
        :filters="activeDashboard.filters || []"
        :is-design-mode="isDesignMode"
        v-model="activeFilterValues"
        @refresh="refreshDesign"
      />

      <!-- Dashboard canvas -->
      <div class="editor-canvas">
        <DashboardGrid
          :widgets="activeDashboard.widgets"
          :is-design-mode="isDesignMode"
          :dashboard-id="activeDashboard.id"
          :dashboard-filters="resolvedDashboardFilters"
          :dashboard-palette="activeDashboard.colorPalette || null"
          :key="designRefreshKey"
          @configure-widget="openConfigModal"
          @layout-widget="openLayoutModal"
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
      <div class="am-box">
        <!-- Header -->
        <div class="am-header">
          <div>
            <h2 class="am-title">Asignar usuarios</h2>
            <p class="am-subtitle">{{ assigningDashboard.name }}</p>
          </div>
          <button class="am-close" @click="assigningDashboard = null">
            <MIcon icon="close" :size="22" />
          </button>
        </div>

        <!-- Body -->
        <div class="am-body">
          <!-- Instruction -->
          <p class="am-instruction">Busca y selecciona los usuarios que tendrán acceso a este dashboard.</p>

          <!-- Search row -->
          <div class="am-search-row">
            <div class="am-search-wrap">
              <MIcon icon="search" :size="20" class="am-search-icon" />
              <input
                v-model="userSearchQuery"
                class="am-search-input"
                placeholder="Buscar por nombre o correo..."
                @keyup.enter="searchUsers"
              />
            </div>
            <button class="am-kc-btn" @click="searchUsers" :disabled="isSearchingUsers">
              <MIcon icon="hub" :size="20" />
              <span>{{ isSearchingUsers ? 'Buscando...' : 'Buscar en Keycloak' }}</span>
            </button>
          </div>

          <!-- Search error -->
          <div v-if="searchError" class="am-error">
            <MIcon icon="error" :size="16" />
            {{ searchError }}
          </div>

          <!-- Search results -->
          <div v-if="userSearchResults.length > 0" class="am-section">
            <div class="am-section-header">
              <span class="am-section-label">Resultados</span>
              <span class="am-section-count">{{ userSearchResults.length }}</span>
            </div>
            <div class="am-user-list">
              <div
                v-for="user in userSearchResults"
                :key="'s-'+user.id"
                class="am-user-item"
                :class="{ 'am-user-item--selected': selectedUsers.includes(user.id) }"
                @click="toggleUserFromSearch(user)"
              >
                <div class="am-avatar">{{ user.avatar }}</div>
                <div class="am-user-info">
                  <div class="am-user-name">{{ user.name }}</div>
                  <div class="am-user-email">{{ user.email || user.username }}</div>
                </div>
                <div class="am-user-action">
                  <MIcon v-if="selectedUsers.includes(user.id)" icon="check_circle" :size="20" :fill="1" style="color: var(--primary)" />
                  <MIcon v-else icon="add_circle" :size="20" style="color: var(--outline)" />
                </div>
              </div>
            </div>
          </div>

          <!-- Assigned users -->
          <div class="am-section">
            <div class="am-section-header">
              <span class="am-section-label">Usuarios asignados</span>
              <span class="am-section-count" v-if="assignedUsersFull.length">{{ assignedUsersFull.length }} asignado{{ assignedUsersFull.length !== 1 ? 's' : '' }}</span>
            </div>

            <!-- Empty assigned state -->
            <div v-if="assignedUsersFull.length === 0" class="am-empty">
              <MIcon icon="person_search" :size="36" style="color: var(--outline-variant)" />
              <p>No hay usuarios asignados</p>
              <span>Comienza buscando un usuario arriba.</span>
            </div>

            <div v-else class="am-user-list">
              <div
                v-for="user in assignedUsersFull"
                :key="'a-'+user.id"
                class="am-user-item"
              >
                <div class="am-avatar">{{ user.avatar }}</div>
                <div class="am-user-info">
                  <div class="am-user-name">{{ user.name }}</div>
                  <div class="am-user-email">{{ user.email || user.username }}</div>
                </div>
                <button class="am-remove-btn" @click.stop="toggleUserFromSearch(user)" data-tooltip="Quitar acceso">
                  <MIcon icon="delete" :size="20" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="am-footer">
          <button class="am-btn-cancel" @click="assigningDashboard = null">Cancelar</button>
          <button class="am-btn-save" @click="saveAssignment">Guardar asignación</button>
        </div>
      </div>
    </div>

    <!-- Import Dashboard Modal -->
    <div v-if="importPreview" class="modal-overlay" @click.self="importPreview = null">
      <div class="modal-box" style="max-width: 440px;">
        <div class="modal-header">
          <h3>Importar Dashboard</h3>
          <button class="btn-icon" @click="importPreview = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px">
            Se creará una copia nueva del siguiente dashboard:
          </p>
          <div class="import-preview-card">
            <div class="import-preview-name">{{ importPreview.name }}</div>
            <p v-if="importPreview.description" class="import-preview-desc">{{ importPreview.description }}</p>
            <div class="import-preview-meta">
              <span class="badge badge-blue">{{ importPreview.widgets.length }} widgets</span>
              <span v-if="importPreview.filters?.length" class="badge" style="background:#f6ffed;color:#52c41a">
                {{ importPreview.filters.length }} filtros
              </span>
            </div>
          </div>
          <p class="form-hint" style="margin-top:12px">Los identificadores internos serán regenerados.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="importPreview = null">Cancelar</button>
          <button class="btn btn-primary" @click="confirmImport">Importar</button>
        </div>
      </div>
    </div>

    <!-- Chart Config Modal -->
    <ChartConfigModal
      v-if="configuringWidget && !layoutWidget"
      :widget="configuringWidget"
      @close="configuringWidget = null"
      @save="saveWidgetConfig"
      @open-layout="openLayoutModal(configuringWidget)"
    />

    <!-- Chart Layout Modal -->
    <ChartLayoutModal
      v-if="layoutWidget"
      :widget="layoutWidget"
      @close="layoutWidget = null"
      @save="saveLayoutConfig"
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

    <!-- Modal: AI Assist -->
    <div v-if="aiAssistOpen" class="modal-overlay" @click.self="aiAssistOpen = false">
      <div class="modal card ai-assist-modal">
        <div class="modal-header ai-assist-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
          </svg>
          <span>IA Assist — Generador de Widgets</span>
          <span v-if="llmStore.isConfigured" class="ai-model-label">
            {{ llmStore.configFor('modelAssist').providerLabel }} · {{ llmStore.configFor('modelAssist').modelLabel }}
          </span>
          <button class="btn-icon" style="margin-left:auto" @click="aiAssistOpen = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body ai-assist-body">
          <div v-if="!llmStore.isConfigured" class="alert alert-error">
            Sin clave API configurada.
            <router-link to="/settings" @click="aiAssistOpen = false" style="color:inherit;font-weight:600;margin-left:4px">
              Ir a Configuración →
            </router-link>
          </div>
          
          <div class="ai-context-row">
            <span class="ai-ctx-label">Contexto del Cubo:</span>
            <span class="badge badge-blue">{{ cubeStore.allMeasures.length }} métricas</span>
            <span class="badge badge-purple">{{ cubeStore.allDimensions.length }} dimensiones</span>
          </div>

          <textarea
            v-model="aiAssistPrompt"
            class="form-input ai-prompt-input"
            rows="5"
            placeholder="Ej: Muéstrame un gráfico de barras comparando el total de ventas por región..."
            :disabled="aiAssistLoading || !llmStore.isConfigured"
            @keydown.enter.prevent="runAIAssist"
          ></textarea>
        </div>

        <div class="modal-footer ai-assist-footer">
          <span class="ai-hint">Usa Enter para enviar</span>
          <button class="btn btn-secondary" @click="aiAssistOpen = false" :disabled="aiAssistLoading">Cancelar</button>
          <button
            class="btn-ai-assist"
            style="margin-left:auto"
            :disabled="!aiAssistPrompt.trim() || aiAssistLoading || !llmStore.isConfigured"
            @click="runAIAssist"
          >
            <svg v-if="aiAssistLoading" class="spinner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32" />
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
            {{ aiAssistLoading ? 'Generando...' : 'Generar Widget' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import DashboardGrid from '@/components/dashboard/DashboardGrid.vue'
import DesignerCard from '@/components/dashboard/DesignerCard.vue'
import MIcon from '@/components/common/MIcon.vue'
import ChartConfigModal from '@/components/dashboard/ChartConfigModal.vue'
import ChartLayoutModal from '@/components/dashboard/ChartLayoutModal.vue'
import DashboardFilterBar from '@/components/dashboard/DashboardFilterBar.vue'
import { useDashboardFilters } from '@/composables/useDashboardFilters'
import { useColorPaletteStore } from '@/stores/colorPalettes'
import keycloak from '@/services/keycloak'
import { useCubeStore } from '@/stores/cubejs'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'

const categoryIcons = ['dashboard', 'directions_car', 'account_tree', 'campaign', 'security', 'monitoring', 'bar_chart', 'pie_chart']
const kcUrl = ''
const kcRealm = import.meta.env.VITE_KEYCLOAK_REALM || 'dashboard'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()
const paletteStore = useColorPaletteStore()
const cubeStore = useCubeStore()
const llmStore = useLlmStore()

// Load data from backend on mount
onMounted(async () => {
  await Promise.all([
    dashboardStore.loadFromBackend(),
    paletteStore.loadFromBackend()
  ])
})

// State
const isDesignMode = ref(true)
const designRefreshKey = ref(0)
function refreshDesign() { designRefreshKey.value++ }
const showNewModal = ref(false)
const configuringWidget = ref(null)
const layoutWidget = ref(null)
const assigningDashboard = ref(null)
const deletingDashboard = ref(null)
const selectedUsers = ref([])
const userSearchQuery = ref('')
const userSearchResults = ref([])
const isSearchingUsers = ref(false)
const searchError = ref(null)
const assignedUsersFull = ref([])

const newName = ref('')
const newDescription = ref('')
const editingTitle = ref(false)
const editTitleValue = ref('')
const editDescription = ref('')
const titleInput = ref(null)
const isPublic = ref(false)
const paletteOpen = ref(false)
const importFileInput = ref(null)
const importPreview = ref(null)

const vClickOutside = {
  mounted(el, binding) {
    el._clickOutsideHandler = (e) => { if (!el.contains(e.target)) binding.value(e) }
    document.addEventListener('mousedown', el._clickOutsideHandler)
  },
  unmounted(el) {
    document.removeEventListener('mousedown', el._clickOutsideHandler)
  }
}

// Active dashboard from route
const activeDashboard = computed(() => {
  const id = route.params.id
  if (!id) return null
  return dashboardStore.allDashboards.find(d => d.id === id) || null
})

const { activeFilterValues, resolvedDashboardFilters, resetFilters } = useDashboardFilters(activeDashboard)

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

// ── AI Assist ─────────────────────────────────────────────────
const aiAssistOpen = ref(false)
const aiAssistPrompt = ref('')
const aiAssistLoading = ref(false)

function buildWidgetAssistPrompt() {
  const measures = cubeStore.allMeasures.map(m => `- ${m.fullName} (${m.type}) - ${m.title}`).join('\n')
  const dims = cubeStore.allDimensions.map(d => `- ${d.fullName} (${d.type}) - ${d.title}`).join('\n')
  
  return `Eres un experto analista de datos. Tu tarea es generar la configuración de un widget para un dashboard partiendo de un modelo en estrella.

MÉTRICAS DISPONIBLES (Usa el valor 'fullName' para 'measures'):
${measures}

DIMENSIONES DISPONIBLES (Usa el valor 'fullName' para 'dimensions'. Si es de tiempo, úsalo en 'timeDimension'):
${dims}

PETICIÓN DEL USUARIO:
${aiAssistPrompt.value}

INSTRUCCIONES:
1. Responde SOLO con un bloque JSON válido (\`\`\`json ... \`\`\`).
2. El JSON debe referenciar EXCLUSIVAMENTE nombres detallados en los listados anteriores y tener este formato EXACTO:
{
  "title": "Un título corto para el gráfico generado de tu comprensión de la petición temporal o temática",
  "widgetType": "bar", // escoge: bar, line, pie, gauge, radar, table, combined
  "cubeQuery": {
    "measures": ["CubeName.measureName"],
    "dimensions": ["CubeName.dimensionName"],
    "timeDimension": {
      "dimension": "CubeName.timeDimensionName",
      "granularity": "month" // opcional, puede ser: day, week, month, year
    }
  }
}
3. No incluyas texto fuera del bloque JSON.
4. "timeDimension" es opcional. Solo inclúyela si la consulta tiene un enfoque explícito en fechas/tiempo y la petición o métrica pide graficar en el tiempo. NO la incluyas al azar si analizas campos normales de nombre/status.`
}

async function runAIAssist() {
  if (!aiAssistPrompt.value.trim() || !llmStore.isConfigured) return
  aiAssistLoading.value = true

  try {
    const cfg = llmStore.configFor('modelAssist')
    const text = await callLlm({ provider: cfg.provider, modelId: cfg.modelId, apiKey: cfg.apiKey, prompt: buildWidgetAssistPrompt(), maxTokens: 16384 })
    
    let widgetDef = null
    const extractedText = text.trim()

    try {
      widgetDef = JSON.parse(extractedText)
    } catch {
      const match = extractedText.match(/```(?:json)?\s*([\s\S]*?)(?:```|$)/i)
      const block = match ? match[1].trim() : extractedText
      try {
        widgetDef = JSON.parse(block)
      } catch (e2) {
        throw new Error('No se pudo encontrar un objeto JSON válido en la respuesta.')
      }
    }

    if (!widgetDef || !widgetDef.cubeQuery || !widgetDef.widgetType) {
      throw new Error('La respuesta de la IA carece de los campos requeridos.')
    }

    const { cubeQuery } = widgetDef;
    if (cubeQuery.timeDimension && !cubeQuery.timeDimension.dimension) {
        delete cubeQuery.timeDimension
    }
    
    // Map LLM string arrays to {key, label} objects expected by the store
    const normalizedQuery = {
      measures: (cubeQuery.measures || []).map(m => typeof m === 'string' ? { key: m, label: m.split('.').pop(), color: '#1890ff' } : m),
      dimensions: (cubeQuery.dimensions || []).map(d => typeof d === 'string' ? { key: d, label: d.split('.').pop() } : d),
      timeDimension: cubeQuery.timeDimension || null,
      filters: [],
      limit: 100
    }

    dashboardStore.addWidget(activeDashboard.value.id, {
        title: widgetDef.title || 'Gráfico generado por IA',
        chartType: widgetDef.widgetType,
        cubeQuery: normalizedQuery,
        useMockData: false
    })

    aiAssistOpen.value = false
    aiAssistPrompt.value = ''
  } catch (err) {
    alert('Error al generar widget: ' + err.message)
  } finally {
    aiAssistLoading.value = false
  }
}

function viewDashboard(id) {
  router.push(`/dashboard/${id}`)
}

async function openAssignModal(db) {
  assigningDashboard.value = db
  selectedUsers.value = [...db.assignedUsers]
  
  assignedUsersFull.value = []
  userSearchQuery.value = ''
  userSearchResults.value = []
  searchError.value = null

  if (selectedUsers.value.length > 0) {
    try {
        const userPromises = selectedUsers.value.map(id => 
          fetch(`/keycloak/admin/realms/${kcRealm}/users/${id}`, {
           headers: { Authorization: `Bearer ${keycloak.token}` }
         }).then(r => r.ok ? r.json() : null)
       )
       const results = await Promise.all(userPromises)
       assignedUsersFull.value = results.filter(u => u).map(u => ({
          id: u.id,
          name: (u.firstName && u.lastName) ? `${u.firstName} ${u.lastName}` : (u.firstName || u.lastName || u.username),
          email: u.email || '',
          username: u.username || '',
          avatar: (u.firstName ? u.firstName[0] : (u.username?.[0] || '?')).toUpperCase()
       }))
    } catch(err) {
       console.error("No se pudieron cargar perfiles de los usuarios asignados", err)
    }
  }
}

async function searchUsers() {
  if (!userSearchQuery.value || userSearchQuery.value.trim().length < 2) {
    userSearchResults.value = []
    searchError.value = null
    return
  }
  isSearchingUsers.value = true
  searchError.value = null
  try {
    const url = `/keycloak/admin/realms/${kcRealm}/users?search=${encodeURIComponent(userSearchQuery.value.trim())}`
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${keycloak.token}` }
    })
    if (!response.ok) {
      if (response.status === 403) throw new Error('Sin permiso (requiere rol view-users o realm-management en Keycloak)')
      throw new Error(`Error al conectar con el servidor (HTTP ${response.status})`)
    }
    const json = await response.json()
    userSearchResults.value = json.map(u => ({
      id: u.id,
      name: (u.firstName && u.lastName) ? `${u.firstName} ${u.lastName}` : (u.firstName || u.lastName || u.username),
      email: u.email || '',
      username: u.username || '',
      avatar: (u.firstName ? u.firstName[0] : (u.username?.[0] || '?')).toUpperCase()
    }))
  } catch (err) {
    searchError.value = err.message
    userSearchResults.value = []
  } finally {
    isSearchingUsers.value = false
  }
}

function toggleUserFromSearch(user) {
  const isSelected = selectedUsers.value.includes(user.id)
  if (!isSelected) {
    selectedUsers.value.push(user.id)
    if (!assignedUsersFull.value.find(u => u.id === user.id)) {
      assignedUsersFull.value.push(user)
    }
  } else {
    selectedUsers.value = selectedUsers.value.filter(id => id !== user.id)
    assignedUsersFull.value = assignedUsersFull.value.filter(u => u.id !== user.id)
  }
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

async function createDashboard() {
  if (!newName.value.trim()) return
  const db = await dashboardStore.createDashboard(newName.value.trim(), newDescription.value.trim(), authStore.user.id)
  showNewModal.value = false
  newName.value = ''
  newDescription.value = ''
  // Remove ?new query param and navigate
  router.push(`/designer/${db.id}`)
}

function addWidget() {
  if (!activeDashboard.value) return
  router.push(`/designer/${activeDashboard.value.id}/configure`)
}

function removeWidget(widgetId) {
  if (!activeDashboard.value) return
  dashboardStore.removeWidget(activeDashboard.value.id, widgetId)
}

function openConfigModal(widget) {
  router.push(`/designer/${activeDashboard.value.id}/configure/${widget.id}`)
}

function openLayoutModal(widget) {
  configuringWidget.value = null
  layoutWidget.value = activeDashboard.value?.widgets.find(w => w.id === widget.id) || widget
}

function saveLayoutConfig(patch) {
  if (!activeDashboard.value || !layoutWidget.value) return
  dashboardStore.updateWidget(activeDashboard.value.id, layoutWidget.value.id, patch)
  layoutWidget.value = null
  uiStore.addAlert({ type: 'success', message: 'Formato del widget actualizado' })
}

function saveWidgetConfig(updatedWidget) {
  if (!activeDashboard.value || !updatedWidget.id) {
    console.error('Cannot save widget config: missing dashboard or widget id', { dashboardId: activeDashboard.value?.id, widgetId: updatedWidget?.id })
    configuringWidget.value = null
    return
  }
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

function selectDashboardPalette(paletteId) {
  if (activeDashboard.value) {
    dashboardStore.updateDashboard(activeDashboard.value.id, { colorPalette: paletteId })
  }
  paletteOpen.value = false
}

const activeDashboardPalette = computed(() =>
  paletteStore.getPaletteById(activeDashboard.value?.colorPalette) || null
)

// ── Export / Import ───────────────────────────────────────────

function handleExportDashboard(db) {
  const payload = {
    __dashboardStudio: true,
    version: '1.0',
    exportedAt: new Date().toISOString(),
    dashboard: {
      name: db.name,
      description: db.description || '',
      isPublic: db.isPublic || false,
      filters: db.filters || [],
      colorPalette: db.colorPalette || null,
      widgets: db.widgets
    }
  }
  const slug = db.name.replace(/[^a-zA-Z0-9_\-. ]/g, '').trim().replace(/\s+/g, '_') || 'dashboard'
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${slug}.dashboard.json`
  a.click()
  URL.revokeObjectURL(url)
  uiStore.addAlert({ type: 'success', message: `Dashboard "${db.name}" exportado` })
}

function handleImportFile(e) {
  const file = e.target.files[0]
  if (!file) return
  e.target.value = ''
  const reader = new FileReader()
  reader.onload = (evt) => {
    try {
      const data = JSON.parse(evt.target.result)
      if (!data.__dashboardStudio || !data.dashboard?.name) {
        uiStore.addAlert({ type: 'error', message: 'Archivo inválido: no es un dashboard exportado de Dashboard Studio' })
        return
      }
      importPreview.value = data.dashboard
    } catch {
      uiStore.addAlert({ type: 'error', message: 'Error al leer el archivo: JSON inválido' })
    }
  }
  reader.readAsText(file)
}

function confirmImport() {
  if (!importPreview.value) return
  const d = importPreview.value
  const db = dashboardStore.createDashboard(d.name, d.description, authStore.user.id)
  dashboardStore.updateDashboard(db.id, {
    isPublic: d.isPublic || false,
    filters: d.filters || [],
    colorPalette: d.colorPalette || null,
    widgets: d.widgets.map(w => ({
      ...w,
      id: Math.random().toString(36).substr(2, 9)
    }))
  })
  uiStore.addAlert({ type: 'success', message: `Dashboard "${d.name}" importado correctamente` })
  importPreview.value = null
  router.push(`/designer/${db.id}`)
}
</script>

<style scoped>
.designer-view { display: flex; flex-direction: column; height: 100%; }

/* ── Page header ── */
.ds-page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 32px; gap: 16px; flex-wrap: wrap;
}
.ds-page-title {
  font-size: 32px; font-weight: 700; color: var(--on-surface);
  letter-spacing: -0.02em; line-height: 1.2;
  font-family: 'Plus Jakarta Sans', sans-serif; margin-bottom: 6px;
}
.ds-page-subtitle { font-size: 16px; color: var(--secondary); line-height: 1.5; }
.ds-header-actions { display: flex; align-items: center; gap: 10px; }
.ds-btn-secondary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant); color: var(--on-surface);
  font-size: 13px; font-weight: 600; border-radius: 10px; cursor: pointer;
  transition: background 0.2s;
}
.ds-btn-secondary:hover { background: var(--surface-container-low); }
.ds-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; background: var(--primary); color: #fff;
  border: none; font-size: 13px; font-weight: 600; border-radius: 10px;
  cursor: pointer; transition: background 0.2s, box-shadow 0.2s;
}
.ds-btn-primary:hover { background: var(--primary-container); box-shadow: var(--shadow-md); }
.ds-btn-primary:active { transform: scale(0.98); }

/* ── Designer grid ── */
.designer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* Create new card */
.designer-new-card {
  border: 2px dashed var(--outline-variant);
  border-radius: 12px;
  padding: 32px 24px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; cursor: pointer; background: transparent;
  transition: border-color 0.2s, background 0.2s;
  min-height: 300px;
}
.designer-new-card:hover {
  border-color: var(--primary);
  background: rgba(0, 88, 190, 0.04);
}
.designer-new-card:hover .new-card-icon-wrap { background: rgba(0, 88, 190, 0.1); color: var(--primary); }
.designer-new-card:hover .new-card-title { color: var(--primary); }
.new-card-icon-wrap {
  width: 52px; height: 52px; border-radius: 50%;
  background: var(--surface-container); color: var(--on-surface-variant);
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.new-card-title {
  font-size: 14px; font-weight: 600; color: var(--on-surface);
  transition: color 0.2s;
}
.new-card-sub { font-size: 13px; color: var(--secondary); }

/* Import preview */
.import-preview-card {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}
.import-preview-name { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.import-preview-desc { font-size: 13px; color: var(--text-secondary); margin: 0 0 10px; }
.import-preview-meta { display: flex; gap: 6px; flex-wrap: wrap; }

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

/* Palette picker */
.palette-picker {
  position: relative;
  flex-shrink: 0;
}
.palette-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
  transition: border-color 0.15s;
  white-space: nowrap;
}
.palette-trigger:hover { border-color: var(--primary); }
.palette-trigger-swatches {
  display: flex;
  gap: 2px;
}
.palette-trigger-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  display: inline-block;
}
.palette-trigger-label {
  font-size: 12px;
  color: var(--text-secondary);
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.palette-trigger-arrow {
  color: var(--text-secondary);
  transition: transform 0.15s;
  flex-shrink: 0;
}
.palette-trigger-arrow.open { transform: rotate(180deg); }

.palette-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  min-width: 220px;
  z-index: 200;
  overflow: hidden;
}
.palette-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.1s;
  gap: 12px;
}
.palette-option:hover { background: var(--bg); }
.palette-option.selected { background: #e6f4ff; }
.palette-option-label {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  flex-shrink: 0;
}
.palette-option.selected .palette-option-label { color: var(--primary); font-weight: 600; }
.palette-option-swatches {
  display: flex;
  gap: 3px;
}
.palette-option-swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  display: inline-block;
}

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
/* ── Assign Users Modal ── */
.am-box {
  background: #fff;
  width: 100%;
  max-width: 640px;
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.am-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 18px;
  border-bottom: 1px solid var(--outline-variant);
  flex-shrink: 0;
}
.am-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--on-surface);
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin: 0 0 2px;
  line-height: 1.3;
}
.am-subtitle {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin: 0;
}
.am-close {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: var(--on-surface-variant);
  transition: background 0.15s;
  flex-shrink: 0;
}
.am-close:hover { background: var(--surface-container-high); }

.am-body {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

.am-instruction {
  font-size: 14px;
  color: var(--on-surface-variant);
  margin: 0;
  line-height: 1.5;
}

/* Search */
.am-search-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.am-search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.am-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--outline);
  pointer-events: none;
}
.am-search-input {
  width: 100%;
  padding: 10px 14px 10px 40px;
  border: 1px solid var(--outline-variant);
  border-radius: 8px;
  font-size: 14px;
  color: var(--on-surface);
  background: var(--surface-container-lowest);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.am-search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 88, 190, 0.12);
}
.am-kc-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(0, 88, 190, 0.05);
  color: var(--primary);
  border: 1px solid rgba(0, 88, 190, 0.2);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}
.am-kc-btn:hover:not(:disabled) { background: rgba(0, 88, 190, 0.1); }
.am-kc-btn:disabled { opacity: 0.55; cursor: not-allowed; }

/* Error */
.am-error {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--error);
  background: var(--error-container);
  padding: 8px 14px;
  border-radius: 8px;
}

/* Section */
.am-section { display: flex; flex-direction: column; gap: 10px; }
.am-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2px;
}
.am-section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}
.am-section-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--secondary);
  background: var(--secondary-container);
  padding: 2px 8px;
  border-radius: 4px;
}

/* User list */
.am-user-list { display: flex; flex-direction: column; gap: 8px; }
.am-user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid rgba(194, 198, 214, 0.4);
  border-radius: 12px;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.am-user-item:hover { box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08); }
.am-user-item--selected { border-color: rgba(0, 88, 190, 0.3); background: rgba(0, 88, 190, 0.03); }

.am-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-container);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.am-user-info { flex: 1; min-width: 0; }
.am-user-name { font-size: 14px; font-weight: 500; color: var(--on-surface); }
.am-user-email { font-size: 12px; color: var(--outline); margin-top: 1px; }
.am-user-action { flex-shrink: 0; }

.am-remove-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: var(--outline);
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}
.am-remove-btn:hover { color: var(--error); background: rgba(186, 26, 26, 0.1); }

/* Empty assigned */
.am-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 32px 20px;
  border: 2px dashed var(--outline-variant);
  border-radius: 16px;
  background: var(--surface-container-low);
  text-align: center;
}
.am-empty p { font-size: 14px; font-weight: 500; color: var(--on-surface-variant); margin: 4px 0 0; }
.am-empty span { font-size: 13px; color: var(--outline); }

/* Footer */
.am-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--outline-variant);
  background: var(--surface-container-low);
  flex-shrink: 0;
}
.am-btn-cancel {
  padding: 10px 24px;
  background: transparent;
  color: var(--on-surface-variant);
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.am-btn-cancel:hover { background: var(--surface-container-high); }
.am-btn-save {
  padding: 10px 24px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 88, 190, 0.25);
  transition: background 0.15s, transform 0.1s;
}
.am-btn-save:hover { background: var(--primary-dark); }
.am-btn-save:active { transform: scale(0.98); }

/* AI Assist Modal */
.ai-assist-modal { width: 90%; max-width: 600px; display: flex; flex-direction: column; }
.ai-assist-header { background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(168,85,247,0.1)); border-bottom: 1px solid rgba(168,85,247,0.2); color: var(--text); }
.ai-model-label { margin-left:12px; font-size:11px; font-family:var(--font-mono); background:#fff; padding:2px 6px; border-radius:4px; border:1px solid #e0e0e0; color:#666; }
.ai-context-row { display: flex; align-items: center; gap:8px; margin-bottom: 16px; font-size: 13px; }
.ai-ctx-label { font-weight: 600; color: var(--text-secondary); }
.ai-prompt-input { font-size: 14px; font-family: inherit; resize: vertical; min-height: 80px; }
.ai-prompt-input:focus { border-color: #a855f7; box-shadow: 0 0 0 3px rgba(168,85,247,0.15); }
.ai-hint { margin-right:auto; font-size:12px; color:#aaa; font-style:italic; }

.btn-ai-assist {
  display: flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: white; border: none; padding: 6px 14px;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; box-shadow: 0 4px 12px rgba(168, 247, 0.25);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.btn-ai-assist:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(168, 85, 247, 0.35); }
.btn-ai-assist:active:not(:disabled) { transform: translateY(0); }
.btn-ai-assist:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; filter: grayscale(50%); }

.spinner-icon { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
</style>
