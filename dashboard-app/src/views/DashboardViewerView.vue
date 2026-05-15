<template>
  <div class="viewer-view">
    <div v-if="!dashboard" class="empty-state card">
      <div class="empty-icon">🔍</div>
      <h3>Dashboard no encontrado</h3>
      <p>El dashboard solicitado no existe o no tienes acceso a él.</p>
      <button class="btn btn-primary" @click="router.push('/')">Volver al inicio</button>
    </div>

    <template v-else>
      <div class="viewer-header">
        <div class="vh-info">
          <h2 class="vh-title">{{ dashboard.name }}</h2>
          <p v-if="dashboard.description" class="vh-desc">{{ dashboard.description }}</p>
        </div>
        <div class="vh-actions">
          <!-- Layout Toggle for Demo -->
          <div class="layout-toggle">
            <button 
              v-for="pos in ['top', 'left', 'right']" 
              :key="pos"
              class="btn btn-icon btn-sm"
              :class="{ 'btn-primary': filterPlacement === pos, 'btn-secondary': filterPlacement !== pos }"
              @click="filterPlacement = pos"
              :title="`Filtros a la ${pos}`"
            >
              <MIcon :icon="pos === 'top' ? 'vertical_align_top' : (pos === 'left' ? 'format_align_left' : 'format_align_right')" :size="18" />
            </button>
          </div>

          <button class="btn btn-secondary btn-icon btn-sm" @click="refreshAll" title="Actualizar datos">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
          <button v-if="authStore.isDesigner" class="btn btn-secondary btn-icon btn-sm" @click="router.push(`/designer/${dashboard.id}`)" title="Editar dashboard">
            <MIcon icon="edit" :size="16" />
          </button>
        </div>
      </div>

      <DashboardRuntime
        :dashboard-id="dashboard.id"
        :widgets="dashboard.widgets"
        :filters="dashboard.filters || []"
        :palette="dashboard.colorPalette"
        :filter-placement="filterPlacement"
        v-model:filter-values="activeFilterValues"
        :resolved-filters="resolvedDashboardFilters"
        @refresh="refreshAll"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import DashboardRuntime from '@/components/dashboard/DashboardRuntime.vue'
import MIcon from '@/components/common/MIcon.vue'
import { useDashboardFilters } from '@/composables/useDashboardFilters'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

const filterPlacement = ref('top')
const refreshKey = ref(0)

// Load data from backend on mount
onMounted(async () => {
  await dashboardStore.loadFromBackend()
})

const dashboard = computed(() => {
  const id = route.params.id
  if (!id) return null
  const db = dashboardStore.allDashboards.find(d => d.id === id)
  if (!db) return null

  // Check access
  if (authStore.isDesigner) return db
  if (db.isPublic || db.assignedUsers.includes(authStore.user?.id)) return db
  return null
})

const { activeFilterValues, resolvedDashboardFilters, resetFilters } = useDashboardFilters(dashboard)

watch(dashboard, (db) => {
  if (db) {
    uiStore.setBreadcrumbs([
      { label: 'Dashboards', path: '/' },
      { label: db.name, path: `/dashboard/${db.id}` }
    ])
  }
}, { immediate: true })

function refreshAll() {
  refreshKey.value++
}
</script>

<style scoped>
.viewer-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px; /* Consistent gap between header and runtime */
}

.viewer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 0; /* Remove internal padding */
  background: transparent; /* No card background */
  border: none; /* No border */
  box-shadow: none; /* No shadow */
  flex-shrink: 0;
}
.vh-info { flex: 1; min-width: 0; }
.vh-title { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.vh-desc { font-size: 14px; color: var(--text-secondary); margin: 0; }
.vh-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.layout-toggle {
  display: flex;
  gap: 4px;
  margin-right: 8px;
  padding-right: 12px;
  border-right: 1px solid var(--border);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  text-align: center;
  gap: 16px;
}
.empty-icon { font-size: 48px; }
</style>
