<template>
  <div class="home-view">
    <!-- Welcome header -->
    <div class="welcome-card card">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>Bienvenido, {{ authStore.user?.name }} 👋</h2>
          <p>
            <span v-if="authStore.isDesigner">
              Tienes acceso como <strong>Diseñador</strong>. Puedes crear y editar dashboards.
            </span>
            <span v-else>
              Tienes acceso como <strong>Visualizador</strong>. Puedes ver los dashboards asignados.
            </span>
          </p>
        </div>
        <div class="welcome-role-badge" :class="authStore.isDesigner ? 'designer' : 'viewer'">
          <span v-if="authStore.isDesigner">🎨 Diseñador</span>
          <span v-else>👁️ Visualizador</span>
        </div>
      </div>
    </div>

    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat-card card" v-for="stat in stats" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
          <span>{{ stat.icon }}</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Quick access -->
    <div class="section-title">Acceso rápido</div>
    <div class="quick-access">
      <div v-if="authStore.isDesigner" class="quick-card card" @click="router.push('/designer?new=1')">
        <div class="qc-icon">➕</div>
        <div class="qc-title">Nuevo Dashboard</div>
        <div class="qc-desc">Crea un dashboard desde cero</div>
      </div>
      <div v-if="authStore.isDesigner" class="quick-card card" @click="router.push('/designer')">
        <div class="qc-icon">📋</div>
        <div class="qc-title">Mis Dashboards</div>
        <div class="qc-desc">Ver y gestionar todos los dashboards</div>
      </div>
      <div class="quick-card card" @click="router.push('/settings')">
        <div class="qc-icon">⚙️</div>
        <div class="qc-title">Configuración</div>
        <div class="qc-desc">Configura la conexión a CubeJS</div>
      </div>
    </div>

    <!-- Recent dashboards -->
    <div class="section-title" style="margin-top: 24px">Dashboards disponibles</div>
    <div v-if="myDashboards.length === 0" class="empty-state card">
      <div class="empty-icon">📊</div>
      <h3>Sin dashboards</h3>
      <p v-if="authStore.isDesigner">Crea tu primer dashboard desde el menú lateral.</p>
      <p v-else>No tienes dashboards asignados aún. Contacta con tu administrador.</p>
    </div>
    <div v-else class="dashboard-list">
      <div
        v-for="db in myDashboards"
        :key="db.id"
        class="db-card card"
        @click="openDashboard(db)"
      >
        <div class="db-card-top">
          <div class="db-icon">📊</div>
          <div class="db-actions" v-if="authStore.isDesigner">
            <button
              class="btn-icon"
              data-tooltip="Editar"
              @click.stop="router.push(`/designer/${db.id}`)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="db-name">{{ db.name }}</div>
        <div class="db-desc">{{ db.description || 'Sin descripción' }}</div>
        <div class="db-meta">
          <span class="badge badge-blue">{{ db.widgets.length }} widgets</span>
          <span v-if="db.isPublic" class="badge badge-green">Público</span>
          <span class="db-date">{{ formatDate(db.updatedAt) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

uiStore.setBreadcrumbs(['Inicio'])

const myDashboards = computed(() => {
  if (authStore.isDesigner) return dashboardStore.allDashboards
  return dashboardStore.dashboardsForUser(authStore.user?.id || '')
})

const stats = computed(() => {
  const dashboards = myDashboards.value
  const totalWidgets = dashboards.reduce((sum, d) => sum + d.widgets.length, 0)

  if (authStore.isDesigner) {
    return [
      { label: 'Total Dashboards', value: dashboards.length, icon: '📊', color: '#1890ff' },
      { label: 'Total Widgets', value: totalWidgets, icon: '📦', color: '#52c41a' },
      { label: 'Públicos', value: dashboards.filter(d => d.isPublic).length, icon: '🌐', color: '#faad14' },
      { label: 'Con asignación', value: dashboards.filter(d => d.assignedUsers.length > 0).length, icon: '👥', color: '#722ed1' }
    ]
  }
  return [
    { label: 'Mis Dashboards', value: dashboards.length, icon: '📊', color: '#1890ff' },
    { label: 'Gráficos totales', value: totalWidgets, icon: '📈', color: '#52c41a' }
  ]
})

function openDashboard(db) {
  if (authStore.isDesigner) {
    router.push(`/designer/${db.id}`)
  } else {
    router.push(`/dashboard/${db.id}`)
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.home-view { display: flex; flex-direction: column; gap: 16px; max-width: 1200px; }

/* Welcome */
.welcome-card { padding: 24px; }
.welcome-content { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.welcome-text h2 { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.welcome-text p { font-size: 14px; color: var(--text-secondary); margin: 0; }
.welcome-role-badge {
  padding: 10px 20px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}
.welcome-role-badge.designer { background: var(--primary-light); color: var(--primary); }
.welcome-role-badge.viewer { background: #f6ffed; color: var(--success); }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
.stat-card { padding: 16px; display: flex; align-items: center; gap: 14px; }
.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text); line-height: 1; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Section title */
.section-title { font-size: 15px; font-weight: 600; color: var(--text); margin-top: 8px; }

/* Quick access */
.quick-access { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.quick-card {
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.quick-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--primary); }
.qc-icon { font-size: 28px; }
.qc-title { font-size: 14px; font-weight: 600; color: var(--text); }
.qc-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.4; }

/* Dashboard list */
.dashboard-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.db-card { padding: 16px; cursor: pointer; transition: all 0.2s; }
.db-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--primary); }
.db-card-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
.db-icon { font-size: 24px; }
.db-name { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.db-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 12px; }
.db-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.db-date { font-size: 12px; color: var(--text-secondary); margin-left: auto; }
</style>
