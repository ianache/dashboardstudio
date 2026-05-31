<template>
  <div class="designer-view">
    <!-- Dashboard list mode -->
    <div v-if="!activeDashboard" class="min-h-[calc(100vh-64px)] p-8">
      <!-- Page Header -->
      <div class="max-w-[1600px] mx-auto mb-8 flex items-end justify-between">
        <div class="space-y-1">
          <h1 class="font-h1 text-h1 text-slate-900">Mis Dashboards</h1>
          <p class="font-body-md text-slate-500 max-w-2xl">Diseña y gestiona tus dashboards para obtener insights en tiempo real.</p>
        </div>
        <div class="flex items-center gap-3">
          <input ref="importFileInput" type="file" accept=".json" style="display:none" @change="handleImportFile" />
          <button class="btn btn-secondary" @click="importFileInput.click()">
            <span class="material-symbols-outlined text-lg">download</span>
            Importar
          </button>
          <button class="btn btn-primary" @click="showNewModal = true">
            <span class="material-symbols-outlined text-lg">add</span>
            Nuevo
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="dashboardStore.allDashboards.length === 0" class="max-w-[1600px] mx-auto">
        <div class="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center">
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
            <span class="material-symbols-outlined text-3xl text-slate-400">dashboard</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-900">Sin dashboards</h3>
          <p class="text-sm text-slate-500 max-w-md">Crea tu primer dashboard para comenzar a visualizar tus datos.</p>
          <button class="btn btn-primary" @click="showNewModal = true">
            <span class="material-symbols-outlined text-lg">add</span>
            Crear dashboard
          </button>
        </div>
      </div>

      <!-- Designer grid -->
      <div v-else class="max-w-[1600px] mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
          <button
            class="group border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:border-blue-500 hover:bg-blue-50/30 transition-all min-h-[280px]"
            @click="showNewModal = true">
            <div class="w-12 h-12 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
              <span class="material-symbols-outlined text-2xl text-slate-400 group-hover:text-blue-600 transition-colors">add</span>
            </div>
            <div class="text-center">
              <span class="block text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">Nuevo Dashboard</span>
              <span class="block text-xs text-slate-500">Comienza un diseño desde cero</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Designer mode (dashboard open) -->
    <template v-else>
      <PageHeader
        :title="activeDashboard.name"
        :description="activeDashboard.description"
      >
        <template #actions>
          <div class="vh-controls-row">
            <!-- Settings button -->
            <button class="btn btn-secondary btn-icon btn-sm" @click="openPropsDrawer" title="Configuración del dashboard">
              <MIcon icon="settings" :size="20" />
            </button>

            <div class="divider-v"></div>

            <!-- Design / Preview toggle -->
            <div class="mode-toggle">
              <button
                class="mode-btn"
                :class="{ active: isDesignMode }"
                @click="isDesignMode = true"
                title="Modo diseño"
              >
                <MIcon icon="brush" :size="18" />
              </button>
              <button
                class="mode-btn"
                :class="{ active: !isDesignMode }"
                @click="isDesignMode = false"
                title="Vista previa"
              >
                <MIcon icon="visibility" :size="18" />
              </button>
            </div>

            <template v-if="isDesignMode">
              <button class="btn btn-primary btn-icon btn-sm" @click="addWidget" title="Añadir Widget">
                <MIcon icon="add" :size="20" />
              </button>
              <button class="btn-ai-assist btn-icon btn-sm" @click="aiAssistOpen = true" title="IA Assist">
                <MIcon icon="auto_awesome" :size="20" />
              </button>
            </template>
          </div>
        </template>
      </PageHeader>

      <DashboardRuntime
        v-if="activeDashboard"
        :dashboard-id="activeDashboard.id"
        :widgets="activeDashboard.widgets"
        :filters="activeDashboard.filters || []"
        :palette="activeDashboard.colorPalette"
        :filter-placement="filterPlacement"
        :is-design-mode="isDesignMode"
        v-model:filter-values="activeFilterValues"
        :resolved-filters="resolvedDashboardFilters"
        @refresh="refreshDesign"
        @configure-widget="openConfigModal"
        @layout-widget="openLayoutModal"
        @remove-widget="removeWidget"
      />

      <!-- Properties Side Drawer -->
      <transition name="slide-right">
        <div v-if="showPropsDrawer" class="props-drawer-overlay" @click.self="showPropsDrawer = false">
          <div class="props-drawer">
            <div class="props-drawer-header">
              <h3>Edit Dashboard</h3>
              <div class="props-drawer-actions">
                <button class="action-btn-save" @click="saveAndCloseProps" title="Guardar cambios">
                  <MIcon icon="save" :size="20" />
                </button>
                <button class="action-btn-close" @click="showPropsDrawer = false" title="Cerrar">
                  <MIcon icon="close" :size="20" />
                </button>
              </div>
            </div>

            <div class="props-drawer-body">
              <div class="form-group">
                <label class="form-label">Nombre del Dashboard</label>
                <input v-model="editTitleValue" class="form-input" placeholder="Nombre..." />
              </div>

              <div class="form-group">
                <label class="form-label">Descripción</label>
                <textarea v-model="editDescription" class="form-textarea" rows="3" placeholder="Descripción opcional..."></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">Paleta de colores</label>
                <div class="palette-picker-grid">
                  <div
                    class="palette-option-card"
                    :class="{ selected: !activeDashboard?.colorPalette }"
                    @click="selectDashboardPalette(null)"
                  >
                    <div class="palette-swatches-row">
                      <span class="p-swatch" style="background:#1890ff"/><span class="p-swatch" style="background:#52c41a"/><span class="p-swatch" style="background:#faad14"/>
                    </div>
                    <span class="p-label">Defecto</span>
                  </div>
                  <div
                    v-for="palette in paletteStore.allPalettes"
                    :key="palette.id"
                    class="palette-option-card"
                    :class="{ selected: activeDashboard?.colorPalette === palette.id }"
                    @click="selectDashboardPalette(palette.id)"
                  >
                    <div class="palette-swatches-row">
                      <span v-for="c in palette.colors.slice(0, 3)" :key="c" class="p-swatch" :style="{ background: c }"/>
                    </div>
                    <span class="p-label">{{ palette.label }}</span>
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Posición de filtros</label>
                <div class="placement-selector">
                  <button 
                    v-for="pos in [
                      { id: 'top', icon: 'vertical_align_top', label: 'Arriba' },
                      { id: 'left', icon: 'format_align_left', label: 'Izquierda' },
                      { id: 'right', icon: 'format_align_right', label: 'Derecha' }
                    ]" 
                    :key="pos.id"
                    class="placement-btn"
                    :class="{ active: filterPlacement === pos.id }"
                    @click="filterPlacement = pos.id"
                  >
                    <MIcon :icon="pos.icon" :size="20" />
                    <span>{{ pos.label }}</span>
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label class="toggle-row">
                  <span class="form-label">Acceso público</span>
                  <input type="checkbox" v-model="isPublic" @change="togglePublic" />
                </label>
                <p class="form-hint">Si está activo, cualquier usuario podrá ver este dashboard sin asignación previa.</p>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </template>

    <!-- ======= MODALS ======= -->

    <!-- New Dashboard Modal -->
    <div v-if="showNewModal" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="showNewModal = false">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[460px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Nuevo Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="showNewModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5 flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-slate-700">Nombre *</label>
            <input 
              v-model="newName" 
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              placeholder="Ej: Dashboard de Ventas" 
              autofocus />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-slate-700">Descripción</label>
            <input 
              v-model="newDescription" 
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              placeholder="Descripción breve..." />
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="btn btn-ghost" @click="showNewModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="createDashboard" :disabled="!newName.trim()">Crear</button>
        </div>
      </div>
    </div>

    <!-- Assign Users Modal -->
    <div v-if="assigningDashboard" class="modal-overlay-assign" @click.self="assigningDashboard = null">
      <div class="assign-modal-box">
        <!-- Header -->
        <div class="assign-modal-header">
          <h2>Asignar usuarios — {{ assigningDashboard.name }}</h2>
          <button @click="assigningDashboard = null">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <!-- Content Area -->
        <div class="assign-modal-body">
          <!-- Instruction & Search -->
          <div class="assign-search-section">
            <p class="assign-instruction">Busca usuarios en Keycloak por nombre parcial o correo para asignarlos al dashboard.</p>
            <div class="assign-search-row">
              <div class="assign-input-wrapper">
                <span class="material-symbols-outlined assign-search-icon">search</span>
                <input
                  v-model="userSearchQuery"
                  type="text"
                  placeholder="Ingrese más de 3 caracteres y espere 2 segundos..."
                  @input="onSearchInput"
                  @keyup.enter="searchUsers"
                />
              </div>
              <button 
                class="assign-search-btn"
                @click="searchUsers"
                :disabled="isSearchingUsers">
                <span class="material-symbols-outlined">hub</span>
                <span>{{ isSearchingUsers ? 'Buscando...' : 'Buscar en Keycloak' }}</span>
              </button>
            </div>
          </div>

          <!-- Search error -->
          <div v-if="searchError" class="assign-error">
            <span class="material-symbols-outlined">error</span>
            {{ searchError }}
          </div>

          <!-- Search results -->
          <div v-if="userSearchResults.length > 0" class="assign-results-section">
            <div class="assign-section-header">
              <h3>RESULTADOS</h3>
              <span class="assign-count-badge">{{ userSearchResults.length }}</span>
            </div>
            <div class="assign-users-list">
              <div 
                v-for="user in userSearchResults" 
                :key="'s'+user.id"
                class="assign-user-item"
                @click="toggleUserFromSearch(user)">
                <div class="assign-user-info">
                  <div class="assign-avatar">{{ user.avatar }}</div>
                  <div class="assign-user-details">
                    <p class="assign-user-name">{{ user.name }}</p>
                    <p class="assign-user-email">{{ user.email || user.username }}</p>
                  </div>
                </div>
                <button 
                  class="assign-add-btn"
                  @click.stop="toggleUserFromSearch(user)">
                  <span class="material-symbols-outlined">add</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Assigned Users -->
          <div class="assign-assigned-section">
            <div class="assign-section-header">
              <h3>USUARIOS ASIGNADOS</h3>
              <span v-if="assignedUsersFull.length" class="assign-count-badge">
                {{ assignedUsersFull.length }} ASIGNADO{{ assignedUsersFull.length !== 1 ? 'S' : '' }}
              </span>
            </div>
            
            <div v-if="assignedUsersFull.length > 0" class="assign-users-list">
              <div 
                v-for="user in assignedUsersFull" 
                :key="'a'+user.id"
                class="assign-user-item">
                <div class="assign-user-info">
                  <div class="assign-avatar">{{ user.avatar }}</div>
                  <div class="assign-user-details">
                    <p class="assign-user-name">{{ user.name }}</p>
                    <p class="assign-user-email">{{ user.email || user.username }}</p>
                  </div>
                </div>
                <button 
                  class="assign-delete-btn"
                  @click.stop="toggleUserFromSearch(user)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else class="assign-empty-state">
              <span class="material-symbols-outlined">person_search</span>
              <p>No hay usuarios asignados</p>
              <span>Comienza buscando un usuario arriba.</span>
            </div>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="assign-modal-footer">
          <button class="btn btn-ghost" @click="assigningDashboard = null">Cancelar</button>
          <button class="btn btn-primary" @click="saveAssignment">Guardar asignación</button>
        </div>
      </div>
    </div>

    <!-- Import Dashboard Modal -->
    <div v-if="importPreview" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="importPreview = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[440px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Importar Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="importPreview = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-500 mb-4">Se creará una copia nueva del siguiente dashboard:</p>
          <div class="p-4 border border-slate-200 rounded-lg bg-slate-50">
            <div class="text-base font-semibold text-slate-900 mb-1">{{ importPreview.name }}</div>
            <p v-if="importPreview.description" class="text-sm text-slate-500 mb-3">{{ importPreview.description }}</p>
            <div class="flex gap-2 flex-wrap">
              <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded">{{ importPreview.widgets.length }} widgets</span>
              <span v-if="importPreview.filters?.length" class="inline-flex items-center px-2 py-1 text-xs font-medium bg-emerald-50 text-emerald-600 rounded">
                {{ importPreview.filters.length }} filtros
              </span>
            </div>
          </div>
          <p class="text-xs text-slate-400 mt-3">Los identificadores internos serán regenerados.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="btn btn-ghost" @click="importPreview = null">Cancelar</button>
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
    <div v-if="deletingDashboard" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="deletingDashboard = null">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[380px] max-w-[95vw] overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 class="text-base font-semibold text-slate-900">Eliminar Dashboard</h3>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="deletingDashboard = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5">
          <p class="text-sm text-slate-700">¿Estás seguro de eliminar <strong>{{ deletingDashboard.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
          <button class="btn btn-ghost" @click="deletingDashboard = null">Cancelar</button>
          <button class="btn btn-danger" @click="deleteDashboard">Eliminar</button>
        </div>
      </div>
    </div>

    <!-- Modal: AI Assist -->
    <div v-if="aiAssistOpen" class="fixed inset-0 bg-black/45 flex items-center justify-center z-50" @click.self="aiAssistOpen = false">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl w-[600px] max-w-[95vw] overflow-hidden flex flex-col">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <span class="material-symbols-outlined text-indigo-600">auto_awesome</span>
          <span class="text-base font-semibold text-slate-900">IA Assist — Generador de Widgets</span>
          <span v-if="llmStore.isConfigured" class="ml-auto text-xs font-mono bg-white px-2 py-1 rounded border border-slate-200 text-slate-600">
            {{ llmStore.configFor('modelAssist').providerLabel }} · {{ llmStore.configFor('modelAssist').modelLabel }}
          </span>
          <button class="p-1 text-slate-400 hover:text-slate-600 rounded" @click="aiAssistOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="px-6 py-5 flex flex-col gap-4">
          <div v-if="!llmStore.isConfigured" class="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">
            Sin clave API configurada.
            <router-link to="/settings" @click="aiAssistOpen = false" class="font-semibold underline">
              Ir a Configuración →
            </router-link>
          </div>
          
          <div class="flex items-center gap-2 text-sm">
            <span class="font-semibold text-slate-600">Contexto del Cubo:</span>
            <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded">{{ cubeStore.allMeasures.length }} métricas</span>
            <span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-purple-50 text-purple-600 rounded">{{ cubeStore.allDimensions.length }} dimensiones</span>
          </div>

          <textarea
            v-model="aiAssistPrompt"
            rows="5"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
            placeholder="Ej: Muéstrame un gráfico de barras comparando el total de ventas por región..."
            :disabled="aiAssistLoading || !llmStore.isConfigured"
            @keydown.enter.prevent="runAIAssist"
          ></textarea>
        </div>

        <div class="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
          <span class="text-xs text-slate-400 italic">Usa Enter para enviar</span>
          <div class="flex items-center gap-3">
            <button class="btn btn-ghost" @click="aiAssistOpen = false" :disabled="aiAssistLoading">Cancelar</button>
            <button
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg shadow-md transition-all"
              :class="[!aiAssistPrompt.trim() || aiAssistLoading || !llmStore.isConfigured ? 'opacity-60 cursor-not-allowed grayscale' : 'hover:opacity-90 hover:-translate-y-0.5']"
              :disabled="!aiAssistPrompt.trim() || aiAssistLoading || !llmStore.isConfigured"
              @click="runAIAssist"
              style="background: linear-gradient(135deg, #6366f1, #a855f7);"
            >
              <svg v-if="aiAssistLoading" class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32" />
              </svg>
              <span v-else class="material-symbols-outlined text-sm">send</span>
              {{ aiAssistLoading ? 'Generando...' : 'Generar Widget' }}
            </button>
          </div>
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
import DashboardRuntime from '@/components/dashboard/DashboardRuntime.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DesignerCard from '@/components/dashboard/DesignerCard.vue'
import ChartConfigModal from '@/components/dashboard/ChartConfigModal.vue'
import ChartLayoutModal from '@/components/dashboard/ChartLayoutModal.vue'
import DashboardFilterBar from '@/components/dashboard/DashboardFilterBar.vue'
import MIcon from '@/components/common/MIcon.vue'
import { useDashboardFilters } from '@/composables/useDashboardFilters'
import { useColorPaletteStore } from '@/stores/colorPalettes'
import { usersApi } from '@/services/api'
import { useCubeStore } from '@/stores/cubejs'
import { useLlmStore } from '@/stores/llm'
import { callLlm } from '@/composables/useLlmCall'

const categoryIcons = ['dashboard', 'directions_car', 'account_tree', 'campaign', 'security', 'monitoring', 'bar_chart', 'pie_chart']
// All registered backend users (loaded once per modal open)
const allBackendUsers = ref([])
const kcRealm = import.meta.env.VITE_KEYCLOAK_REALM || 'Apps'

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
const filterPlacement = ref('top')
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
const searchDebounceTimer = ref(null)

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
const showPropsDrawer = ref(false)

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

// Watch active dashboard to sync UI and breadcrumbs
watch(activeDashboard, (db) => {
  if (db) {
    // Sync local edit state with active dashboard
    editTitleValue.value = db.name || ''
    editDescription.value = db.description || ''
    isPublic.value = db.isPublic || false
    
    uiStore.setBreadcrumbs([
      { label: 'Diseño', path: '/designer' },
      { label: db.name, path: `/designer/${db.id}` }
    ])
  } else if (!route.params.id) {
    uiStore.setBreadcrumbs([
      { label: 'Diseño', path: '/designer' },
      { label: 'Mis Dashboards', path: '/designer' }
    ])
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

function openPropsDrawer() {
  if (activeDashboard.value) {
    editTitleValue.value = activeDashboard.value.name || ''
    editDescription.value = activeDashboard.value.description || ''
    isPublic.value = activeDashboard.value.isPublic || false
  }
  showPropsDrawer.value = true
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

function _mapKcUser(u) {
  return {
    id: u.id,
    name: (u.firstName && u.lastName) ? `${u.firstName} ${u.lastName}` : (u.firstName || u.lastName || u.username || u.email || u.id),
    email: u.email || '',
    username: u.username || '',
    first_name: u.firstName || null,
    last_name: u.lastName || null,
    avatar: (u.firstName ? u.firstName[0] : (u.username?.[0] || '?')).toUpperCase()
  }
}

function _mapBackendUser(u) {
  return {
    id: u.id,
    name: u.full_name || u.username || u.email || u.id,
    email: u.email || '',
    username: u.username || '',
    first_name: u.first_name || null,
    last_name: u.last_name || null,
    avatar: u.avatar || (u.full_name ? u.full_name[0] : (u.username?.[0] || '?')).toUpperCase()
  }
}

async function openAssignModal(db) {
  assigningDashboard.value = db
  selectedUsers.value = [...db.assignedUsers]

  assignedUsersFull.value = []
  userSearchQuery.value = ''
  userSearchResults.value = []
  searchError.value = null
  allBackendUsers.value = []

  // Feature temporarily disabled during BFF migration
  console.warn('User search and assignment is being migrated to BFF.')
}

function _applyUserFilter(q) {
  const query = (q || '').trim().toLowerCase()
  // Show all unassigned users if no query, otherwise filter
  userSearchResults.value = allBackendUsers.value.filter(u =>
    !selectedUsers.value.includes(u.id) && (
      !query ||
      u.name.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      u.username.toLowerCase().includes(query)
    )
  )
  searchError.value = null
}

/** Debounce handler: waits 2s after last keystroke and requires >3 chars */
function onSearchInput() {
  clearTimeout(searchDebounceTimer.value)
  userSearchResults.value = []
  searchError.value = null

  const q = userSearchQuery.value.trim()
  if (q.length <= 3) return  // need more than 3 chars

  searchDebounceTimer.value = setTimeout(() => {
    searchUsers()
  }, 2000)
}

async function searchUsers() {
  if (!userSearchQuery.value || userSearchQuery.value.trim().length <= 3) {
    userSearchResults.value = []
    searchError.value = null
    return
  }
  isSearchingUsers.value = true
  searchError.value = null
  try {
    const results = await usersApi.search(userSearchQuery.value.trim())
    userSearchResults.value = results.filter(u => !selectedUsers.value.includes(u.id))
  } catch (err) {
    searchError.value = err?.message || 'Error al buscar usuarios'
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
  // Keep search results in sync after selection change
  _applyUserFilter(userSearchQuery.value)
}

async function saveAssignment() {
  if (!assigningDashboard.value) return

  // Provision any selected users who may not yet exist in the DB
  if (assignedUsersFull.value.length > 0) {
    try {
      await usersApi.provisionBatch(assignedUsersFull.value.map(u => ({
        id: u.id,
        email: u.email || null,
        full_name: u.name || null,
        first_name: u.first_name || null,
        last_name: u.last_name || null,
        username: u.username || null
      })))
    } catch (err) {
      console.error('Error provisionando usuarios:', err)
      uiStore.addAlert({ type: 'error', message: 'Error al registrar usuarios antes de asignar.' })
      return
    }
  }

  await dashboardStore.assignDashboardToUsers(assigningDashboard.value.id, selectedUsers.value)
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
    uiStore.setBreadcrumbs([
      { label: 'Diseño', path: '/designer' },
      { label: editTitleValue.value.trim(), path: `/designer/${activeDashboard.value.id}` }
    ])
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
}

function saveAndCloseProps() {
  saveTitle()
  saveDescription()
  showPropsDrawer.value = false
  uiStore.addAlert({ type: 'success', message: 'Configuración del dashboard guardada' })
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

async function confirmImport() {
  if (!importPreview.value) return
  const d = importPreview.value
  try {
    const db = await dashboardStore.createDashboard(d.name, d.description, authStore.user.id)
    await dashboardStore.updateDashboard(db.id, {
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
  } catch (err) {
    uiStore.addAlert({ type: 'error', message: 'Error al importar dashboard' })
  }
}
</script>

<style scoped>
.designer-view { display: flex; flex-direction: column; height: 100%; }

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

.text-sm { font-size: 14px; }

/* Editor */
.viewer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 0;
  background: transparent;
  flex-shrink: 0;
}

.vh-info { flex: 1; min-width: 0; }
.vh-title { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px; line-height: 1.2; }
.vh-desc { font-size: 14px; color: var(--text-secondary); margin: 0; }

.vh-actions-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.vh-controls-row {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px; /* Aligns with vh-title height approximate */
}

.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.mode-btn:hover { background: var(--bg); }
.mode-btn.active { background: var(--primary); color: #fff; }

/* Custom AI Assist Icon Button */
.btn-ai-assist.btn-icon {
  width: 34px;
  height: 34px;
  padding: 0;
  justify-content: center;
  border-radius: 8px;
}


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
  display: inline-flex; align-items: center;
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

/* AI Assist */
.btn-ai-assist {
  display: inline-flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: white; border: none; padding: 6px 14px;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; box-shadow: 0 4px 12px rgba(168, 85, 247, 0.25);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.btn-ai-assist:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(168, 85, 247, 0.35); }
.btn-ai-assist:active:not(:disabled) { transform: translateY(0); }
.btn-ai-assist:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; filter: grayscale(50%); }

.animate-spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Custom font classes */
.font-h1 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* Assign Users Modal Styles */
.modal-overlay-assign {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  padding: 16px;
}

.assign-modal-box {
  background: white;
  width: 100%;
  max-width: 672px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.assign-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.assign-modal-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}

.assign-modal-header button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.assign-modal-header button:hover {
  background: #f1f5f9;
  color: #334155;
}

.assign-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.assign-search-section {
  margin-bottom: 24px;
}

.assign-instruction {
  font-size: 14px;
  color: #475569;
  margin: 0 0 16px 0;
}

.assign-search-row {
  display: flex;
  gap: 12px;
}

.assign-input-wrapper {
  position: relative;
  flex: 1;
}

.assign-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 20px;
  pointer-events: none;
}

.assign-input-wrapper input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s;
}

.assign-input-wrapper input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.assign-search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.assign-search-btn:hover:not(:disabled) {
  background: #2563eb;
}

.assign-search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.assign-search-btn .material-symbols-outlined {
  font-size: 18px;
}

.assign-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 24px;
}

.assign-results-section,
.assign-assigned-section {
  margin-bottom: 24px;
}

.assign-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 4px;
}

.assign-section-header h3 {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.assign-count-badge {
  padding: 2px 8px;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}

.assign-users-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assign-user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.2s;
}

.assign-user-item:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.assign-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assign-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.assign-user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.assign-user-name {
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
  margin: 0;
}

.assign-user-email {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.assign-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s;
}

.assign-delete-btn:hover {
  color: #dc2626;
  background: #fef2f2;
}

.assign-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #3b82f6;
  transition: all 0.2s;
}

.assign-add-btn:hover {
  color: #2563eb;
  background: #eff6ff;
}

.assign-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  background: #f8fafc;
  text-align: center;
}

.assign-empty-state .material-symbols-outlined {
  font-size: 48px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.assign-empty-state p {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin: 0 0 4px 0;
}

.assign-empty-state span {
  font-size: 13px;
  color: #94a3b8;
}

.assign-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* Properties Drawer */
.props-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  justify-content: flex-end;
}

.props-drawer {
  width: 400px;
  max-width: 90vw;
  background: #fff;
  height: 100%;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.props-drawer-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.props-drawer-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.props-drawer-actions {
  display: flex;
  gap: 8px;
}

.props-drawer-actions button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn-save { background: var(--primary); color: #fff; }
.action-btn-save:hover { background: var(--primary-dark); }
.action-btn-close { background: #f1f5f9; color: #64748b; }
.action-btn-close:hover { background: #e2e8f0; color: #0f172a; }

.props-drawer-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.palette-picker-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 8px;
}

.palette-option-card {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}

.palette-option-card:hover { border-color: var(--primary); background: #fff; }
.palette-option-card.selected { border-color: var(--primary); background: #eff6ff; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1); }

.palette-swatches-row { display: flex; gap: 4px; margin-bottom: 6px; }
.p-swatch { width: 20px; height: 20px; border-radius: 4px; }
.p-label { font-size: 12px; font-weight: 500; color: #475569; display: block; }

.placement-selector {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.placement-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.placement-btn span { font-size: 11px; font-weight: 500; }
.placement-btn:hover { background: #f8fafc; }
.placement-btn.active { border-color: var(--primary); color: var(--primary); background: #eff6ff; }

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.divider-v { width: 1px; height: 24px; background: #e2e8f0; margin: 0 8px; }

.slide-right-enter-active, .slide-right-leave-active { transition: opacity 0.3s; }
.slide-right-enter-from, .slide-right-leave-to { opacity: 0; }
.slide-right-enter-active .props-drawer, .slide-right-leave-active .props-drawer { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); transform: translateX(0); }
.slide-right-enter-from .props-drawer, .slide-right-leave-to .props-drawer { transform: translateX(100%); }

</style>
