<template>
  <div class="home-view">

    <!-- Greeting -->
    <section class="greeting">
      <h2 class="greeting-title">Bienvenido, {{ authStore.user?.name }}</h2>
      <p class="greeting-sub">Aquí tienes un resumen del rendimiento de tu workspace hoy.</p>
    </section>

    <!-- KPI Row -->
    <section class="kpi-row">
      <KpiCard
        v-for="stat in stats"
        :key="stat.label"
        :icon="stat.icon"
        :icon-fill="stat.iconFill ?? 0"
        :label="stat.label"
        :value="stat.value"
        :trend="stat.trend"
        :icon-color="stat.iconColor"
        :icon-bg="stat.iconBg"
      />
    </section>

    <!-- Quick Actions -->
    <section class="home-section">
      <h3 class="section-heading">Acceso rápido</h3>
      <div class="quick-actions-grid">
        <QuickActionCard
          v-if="authStore.isDesigner"
          icon="add_circle"
          title="Nuevo Dashboard"
          description="Crea un dashboard desde cero"
          variant="primary"
          @click="router.push('/designer?new=1')"
        />

        <QuickActionCard
          v-if="authStore.isDesigner"
          icon="grid_view"
          title="Mis Dashboards"
          description="Ver y gestionar todos los dashboards"
          variant="default"
          @click="router.push('/designer')"
        />

        <QuickActionCard
          icon="settings"
          title="Configuración"
          description="Configura la conexión a CubeJS"
          variant="secondary"
          @click="router.push('/settings')"
        />
      </div>
    </section>

    <!-- Dashboards -->
    <section class="home-section">
      <div class="section-header">
        <h3 class="section-heading">Dashboards disponibles</h3>
        <button v-if="authStore.isDesigner" class="view-all-btn" @click="router.push('/designer')">
          Ver todos
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="14" height="14">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>

      <div v-if="myDashboards.length === 0" class="empty-state card">
        <div class="empty-icon">📊</div>
        <h3>Sin dashboards</h3>
        <p v-if="authStore.isDesigner">Crea tu primer dashboard desde el menú lateral.</p>
        <p v-else>No tienes dashboards asignados aún. Contacta con tu administrador.</p>
      </div>

      <div v-else class="db-grid">
        <DashboardCard
          v-for="(db, idx) in myDashboards"
          :key="db.id"
          :name="db.name"
          :description="db.description"
          :widget-count="db.widgets.length"
          :updated-label="formatDate(db.updatedAt)"
          :color-index="idx"
          :badge="getBadge(db)"
          @open="openDashboard(db)"
          @share="() => {}"
          @menu="authStore.isDesigner ? router.push(`/designer/${db.id}`) : undefined"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import KpiCard from '@/components/common/KpiCard.vue'
import QuickActionCard from '@/components/common/QuickActionCard.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

onMounted(async () => {
  await dashboardStore.loadFromBackend()
})

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
      {
        label: 'Total Dashboards',
        value: dashboards.length,
        trend: '+5% vs mes anterior',
        icon: 'dashboard',
        iconFill: 0,
        iconColor: 'var(--primary)',
        iconBg: 'rgba(0, 88, 190, 0.1)',
      },
      {
        label: 'Widgets activos',
        value: totalWidgets,
        trend: 'Activos ahora',
        icon: 'widgets',
        iconFill: 0,
        iconColor: 'var(--tertiary)',
        iconBg: 'rgba(70, 72, 212, 0.1)',
      },
      {
        label: 'Reportes públicos',
        value: dashboards.filter(d => d.isPublic).length,
        trend: dashboards.filter(d => d.isPublic).length === 0 ? 'Estado: Privado' : 'Públicos',
        icon: 'public',
        iconFill: 0,
        iconColor: 'var(--secondary)',
        iconBg: 'rgba(86, 94, 116, 0.1)',
      },
      {
        label: 'Con asignación',
        value: dashboards.filter(d => d.assignedUsers?.length > 0).length,
        trend: dashboards.filter(d => d.assignedUsers?.length > 0).length === 0 ? 'Sin asignaciones' : 'Asignados',
        icon: 'assignment_ind',
        iconFill: 0,
        iconColor: 'var(--error)',
        iconBg: 'rgba(186, 26, 26, 0.1)',
      },
    ]
  }
  return [
    {
      label: 'Mis Dashboards',
      value: dashboards.length,
      trend: 'Asignados a mí',
      icon: 'dashboard',
      iconFill: 0,
      iconColor: 'var(--primary)',
      iconBg: 'rgba(0, 88, 190, 0.1)',
    },
    {
      label: 'Gráficos totales',
      value: totalWidgets,
      trend: 'En todos mis dashboards',
      icon: 'monitoring',
      iconFill: 0,
      iconColor: 'var(--tertiary)',
      iconBg: 'rgba(70, 72, 212, 0.1)',
    },
  ]
})

function getBadge(db) {
  if (db.isPublic) return { text: 'Público', variant: 'public' }
  if (db.assignedUsers?.length > 0) return { text: 'Activo', variant: 'active' }
  return null
}

function openDashboard(db) {
  if (authStore.isDesigner) {
    router.push(`/designer/${db.id}`)
  } else {
    router.push(`/dashboard/${db.id}`)
  }
}

function formatDate(iso) {
  if (!iso) return 'Sin fecha'
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now - d
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return 'Actualizado hoy'
  if (diffDays === 1) return 'Actualizado ayer'
  if (diffDays < 7) return `Hace ${diffDays} días`
  return d.toLocaleDateString('es', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: var(--section-gap);
  max-width: 1400px;
}

/* Greeting */
.greeting { display: flex; flex-direction: column; gap: 6px; }
.greeting-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--on-surface);
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.greeting-sub {
  font-size: 16px;
  color: var(--on-surface-variant);
  line-height: 1.6;
}

/* KPI row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--gutter);
}

/* Sections */
.home-section { display: flex; flex-direction: column; gap: var(--stack-md); }
.section-heading {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  padding: 4px 0;
  transition: opacity 0.2s;
}
.view-all-btn:hover { opacity: 0.75; }

/* Quick actions */
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--gutter);
}

/* Dashboard grid */
.db-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--stack-lg);
}
</style>
