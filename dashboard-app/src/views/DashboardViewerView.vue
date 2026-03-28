<template>
  <div class="viewer-view">
    <div v-if="!dashboard" class="empty-state card">
      <div class="empty-icon">🔍</div>
      <h3>Dashboard no encontrado</h3>
      <p>El dashboard solicitado no existe o no tienes acceso a él.</p>
      <button class="btn btn-primary" @click="router.push('/')">Volver al inicio</button>
    </div>

    <template v-else>
      <!-- Dashboard header -->
      <div class="viewer-header card">
        <div class="vh-info">
          <h2 class="vh-title">{{ dashboard.name }}</h2>
          <p v-if="dashboard.description" class="vh-desc">{{ dashboard.description }}</p>
        </div>
        <div class="vh-actions">
          <span class="badge badge-blue">{{ dashboard.widgets.length }} gráficos</span>
          <span v-if="dashboard.isPublic" class="badge badge-green">Público</span>
          <button class="btn btn-secondary btn-sm" @click="refreshAll">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualizar todo
          </button>
          <button v-if="authStore.isDesigner" class="btn btn-secondary btn-sm" @click="router.push(`/designer/${dashboard.id}`)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Editar
          </button>
        </div>
      </div>

      <!-- Filter bar -->
      <DashboardFilterBar
        v-if="dashboard.filters?.length > 0"
        :dashboard-id="dashboard.id"
        :filters="dashboard.filters || []"
        :is-design-mode="false"
        v-model="activeFilterValues"
      />

      <!-- Dashboard grid -->
      <div class="viewer-canvas">
        <DashboardGrid
          :widgets="dashboard.widgets"
          :is-design-mode="false"
          :dashboard-id="dashboard.id"
          :dashboard-filters="resolvedDashboardFilters"
          :key="refreshKey"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import DashboardGrid from '@/components/dashboard/DashboardGrid.vue'
import DashboardFilterBar from '@/components/dashboard/DashboardFilterBar.vue'
import { useDashboardFilters } from '@/composables/useDashboardFilters'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

const refreshKey = ref(0)

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
  resetFilters()
  if (db) {
    uiStore.setBreadcrumbs(['Dashboards', db.name])
  }
}, { immediate: true })

function refreshAll() {
  refreshKey.value++
}
</script>

<style scoped>
.viewer-view { display: flex; flex-direction: column; gap: 16px; height: 100%; }

.viewer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  flex-shrink: 0;
}
.vh-info { flex: 1; min-width: 0; }
.vh-title { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.vh-desc { font-size: 14px; color: var(--text-secondary); margin: 0; }
.vh-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }

.viewer-canvas {
  flex: 1;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: auto;
  box-shadow: var(--shadow);
  padding: 8px;
  min-height: 400px;
}
</style>
