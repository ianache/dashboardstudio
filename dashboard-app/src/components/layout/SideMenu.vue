<template>
  <aside class="side-menu" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <!-- Logo / Brand -->
    <div class="side-logo">
      <div class="logo-icon-wrap">
        <MIcon icon="analytics" :size="22" :fill="1" class="icon-on-primary" />
      </div>
      <div class="logo-text-block">
        <span class="logo-title">Dashboard<strong>Studio</strong></span>
        <span class="logo-subtitle">Enterprise Control</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="side-nav">
      <div class="nav-section">
        <router-link to="/" class="nav-item" :class="{ active: $route.name === 'Home' }">
          <MIcon icon="home" :size="20" class="nav-icon" />
          <span class="nav-label">Inicio</span>
        </router-link>
      </div>

      <!-- Designer section -->
      <div v-if="authStore.isDesigner" class="nav-section">
        <div class="nav-section-title">DISEÑO</div>

        <div class="nav-item" :class="{ active: isDesignerRoute }" @click="toggleSection('design')">
          <MIcon icon="grid_view" :size="20" class="nav-icon" />
          <span class="nav-label">Mis Dashboards</span>
          <MIcon icon="expand_more" :size="18" class="nav-arrow" :class="{ open: openSections.design }" />
        </div>
        <transition name="expand">
          <div v-show="openSections.design" class="nav-sub">
            <router-link to="/designer" class="nav-sub-item" :class="{ active: $route.name === 'DesignerList' }">
              <span class="sub-dot" />Ver todos
            </router-link>
            <div class="nav-sub-item nav-sub-action" @click="createNewDashboard">
              <span class="sub-plus">+</span>Nuevo dashboard
            </div>
          </div>
        </transition>

        <div class="nav-item" :class="{ active: isModelRoute }" @click="toggleSection('models')">
          <MIcon icon="account_tree" :size="20" class="nav-icon" />
          <span class="nav-label">Modelos</span>
          <MIcon icon="expand_more" :size="18" class="nav-arrow" :class="{ open: openSections.models }" />
        </div>
        <transition name="expand">
          <div v-show="openSections.models" class="nav-sub">
            <router-link to="/models" class="nav-sub-item" :class="{ active: $route.name === 'ModelList' }">
              <span class="sub-dot" />Ver todos
            </router-link>
            <router-link to="/models/data-types" class="nav-sub-item" :class="{ active: $route.name === 'DataTypes' }">
              <span class="sub-dot" />Tipos de datos
            </router-link>
            <router-link to="/models/knowledge-spaces" class="nav-sub-item" :class="{ active: $route.name === 'KnowledgeSpaces' }">
              <span class="sub-dot" />Knowledge Spaces
            </router-link>
          </div>
        </transition>
      </div>

      <!-- Data Integration section -->
      <div v-if="authStore.isDesigner" class="nav-section">
        <div class="nav-section-title">DATA INTEGRATION</div>

        <div class="nav-item" :class="{ active: isIntegrationRoute }" @click="toggleSection('integration')">
          <MIcon icon="sync_alt" :size="20" class="nav-icon" />
          <span class="nav-label">Data Integration</span>
          <MIcon icon="expand_more" :size="18" class="nav-arrow" :class="{ open: openSections.integration }" />
        </div>
        <transition name="expand">
          <div v-show="openSections.integration" class="nav-sub">
            <router-link to="/integrations" class="nav-sub-item" :class="{ active: $route.name === 'Integrations' }">
              <span class="sub-dot" />Integrations
            </router-link>
            <router-link to="/integrations/diagram-types" class="nav-sub-item" :class="{ active: $route.name === 'DiagramTypes' }">
              <span class="sub-dot" />Tipos de Diagrama
            </router-link>
            <router-link to="/integrations/tool-catalog" class="nav-sub-item" :class="{ active: $route.name === 'ToolCatalog' }">
              <span class="sub-dot" />Catálogo de Herramientas
            </router-link>
            <router-link to="/integrations/connections" class="nav-sub-item" :class="{ active: $route.name === 'Connections' }">
              <span class="sub-dot" />Conexiones
            </router-link>
            </div>
            </transition>

      </div>

      <!-- Dashboards section -->
      <div class="nav-section">
        <div class="nav-section-title">DASHBOARDS</div>
        <div class="nav-item" :class="{ active: isDashboardRoute }" @click="toggleSection('dashboards')">
          <MIcon icon="bar_chart" :size="20" class="nav-icon" />
          <span class="nav-label">Dashboards</span>
          <span class="nav-badge" v-if="availableDashboards.length">{{ availableDashboards.length }}</span>
          <MIcon icon="expand_more" :size="18" class="nav-arrow" :class="{ open: openSections.dashboards }" />
        </div>
        <transition name="expand">
          <div v-show="openSections.dashboards" class="nav-sub">
            <div v-if="availableDashboards.length === 0" class="nav-sub-empty">
              Sin dashboards asignados
            </div>
            <router-link
              v-for="db in availableDashboards"
              :key="db.id"
              :to="`/dashboard/${db.id}`"
              class="nav-sub-item"
              :class="{ active: $route.params.id === db.id }"
            >
              <span class="sub-dot" />
              <span class="sub-label">{{ db.name }}</span>
            </router-link>
          </div>
        </transition>
      </div>
    </nav>

    <!-- Bottom section -->
    <div class="side-bottom">
      <div class="platform-status-container">
        <div class="platform-version-info">
          <span class="platform-version-label">Versión de la Plataforma</span>
          <span class="platform-version-val">v1.0.0</span>
        </div>
        
        <div class="status-indicator-wrapper">
          <button 
            class="status-indicator-btn" 
            :class="overallStatus" 
            @click.stop="toggleStatusPopup"
            data-tooltip="Estado de los servicios"
          >
            <MIcon :icon="statusIcon" :size="18" color="currentColor" />
          </button>

          <!-- Status Popup -->
          <transition name="fade">
            <div v-if="showStatusPopup" class="status-popup" @click.stop>
              <div class="status-popup-header">
                <span class="status-popup-title">Servicios</span>
                <button class="status-popup-refresh-btn" @click="checkAllHealth" title="Recargar">
                  <MIcon icon="sync_alt" :size="12" color="currentColor" />
                </button>
              </div>
              <div class="status-popup-body">
                <div v-for="(status, service) in services" :key="service" class="service-status-row">
                  <div class="service-name-group">
                    <span class="service-dot" :class="status" />
                    <span class="service-name">{{ service.toUpperCase() }}</span>
                  </div>
                  <span class="service-status-label" :class="status">
                    {{ status === 'green' ? 'OK' : (status === 'amber' ? 'WARN' : 'DOWN') }}
                  </span>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import MIcon from '@/components/common/MIcon.vue'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

const openSections = ref({ design: true, models: true, integration: true, dashboards: true })

const isDesignerRoute = computed(() =>
  ['DesignerList', 'DesignerEdit'].includes(router.currentRoute.value.name)
)
const isModelRoute = computed(() =>
  ['ModelList', 'ModelEditor', 'DataTypes', 'KnowledgeSpaces'].includes(router.currentRoute.value.name)
)
const isIntegrationRoute = computed(() =>
  ['Integrations', 'DiagramTypes', 'ToolCatalog'].includes(router.currentRoute.value.name)
)
const isDashboardRoute = computed(() =>
  router.currentRoute.value.name === 'DashboardView'
)
const availableDashboards = computed(() => {
  if (authStore.isDesigner) return dashboardStore.allDashboards
  return dashboardStore.dashboardsForUser(authStore.user?.id || '')
})

function toggleSection(name) { openSections.value[name] = !openSections.value[name] }
function createNewDashboard() { router.push('/designer?new=1') }

// Service Health Monitoring via BFF health report
const showStatusPopup = ref(false)
const services = ref({
  bff: 'green',
  backend: 'green',
  ai: 'green',
  cubejs: 'green'
})

function toggleStatusPopup() {
  showStatusPopup.value = !showStatusPopup.value
}

async function checkAllHealth() {
  try {
    const res = await fetch('/bff/health', { credentials: 'include' })
    if (res.ok) {
      const data = await res.json()
      if (data.services) {
        services.value = data.services
      }
    } else {
      services.value = { bff: 'red', backend: 'red', ai: 'red', cubejs: 'red' }
    }
  } catch (err) {
    services.value = { bff: 'red', backend: 'red', ai: 'red', cubejs: 'red' }
  }
}

const overallStatus = computed(() => {
  const failedCount = Object.values(services.value).filter(status => status === 'red').length
  const ratio = failedCount / 4
  if (ratio > 0.8) {
    return 'red' // More than 80% (4 out of 4) is critical non-operational
  } else if (failedCount > 0) {
    return 'amber' // 1, 2, or 3 failed is amber warning
  } else {
    return 'green' // All 4 running is green OK
  }
})

const statusIcon = computed(() => {
  const status = overallStatus.value
  if (status === 'green') return 'check_circle'
  if (status === 'amber') return 'alert_circle'
  return 'x_circle'
})

let healthInterval = null
onMounted(() => {
  checkAllHealth()
  healthInterval = setInterval(checkAllHealth, 30000)
  window.addEventListener('click', closePopup)
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
  window.removeEventListener('click', closePopup)
})

function closePopup() {
  showStatusPopup.value = false
}
</script>

<style scoped>
.side-menu {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  z-index: 1100;
  transition: width 0.25s ease;
  overflow: visible;
  box-shadow: var(--shadow-md);
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}
.side-menu.collapsed { width: var(--sidebar-collapsed-width); }

/* Logo */
.side-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
  overflow: hidden;
  height: var(--topbar-height);
}
.logo-icon-wrap {
  width: 38px;
  height: 38px;
  background: var(--primary-container);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-text-block {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .logo-text-block { opacity: 0; pointer-events: none; }
.logo-title {
  color: var(--on-surface);
  font-size: 15px;
  white-space: nowrap;
  line-height: 1.2;
}
.logo-title strong { font-weight: 700; }
.logo-subtitle {
  color: var(--on-surface-variant);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  white-space: nowrap;
}

/* Nav */
.side-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 0 8px;
}
.side-nav::-webkit-scrollbar { width: 4px; }
.side-nav::-webkit-scrollbar-thumb { background: var(--sidebar-border); border-radius: 2px; }

.nav-section { margin-bottom: 4px; }

.nav-section-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--on-surface-variant);
  opacity: 0.5;
  padding: 8px 20px 4px;
  letter-spacing: 0.1em;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .nav-section-title { opacity: 0; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin: 2px 8px;
  color: var(--on-surface-variant);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
  border-radius: 8px;
  border-left: 3px solid transparent;
}
.nav-item:hover { 
  color: var(--on-surface); 
  background: var(--surface-container-low); 
}
.nav-item.active {
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 10%, transparent);
  border-left-color: var(--primary);
}

.nav-icon {
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.nav-label {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .nav-label { opacity: 0; pointer-events: none; }

.nav-arrow {
  color: var(--on-surface-variant);
  opacity: 0.6;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.nav-arrow.open { transform: rotate(180deg); }
.side-menu.collapsed .nav-arrow { opacity: 0; }

.nav-badge {
  background: var(--primary);
  color: var(--on-primary);
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  flex-shrink: 0;
  transition: opacity 0.2s;
}
.side-menu.collapsed .nav-badge { opacity: 0; }

/* Sub nav */
.nav-sub {
  overflow: hidden;
  background: color-mix(in srgb, var(--surface) 95%, var(--on-surface));
  margin: 0 8px;
  border-radius: 6px;
}
.side-menu.collapsed .nav-sub { display: none; }

.nav-sub-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 38px;
  color: var(--on-surface-variant);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  border-radius: 6px;
}
.nav-sub-item:hover { color: var(--on-surface); background: var(--surface-container-low); }
.nav-sub-item.active { color: var(--primary); font-weight: 600; }
.nav-sub-action { color: var(--primary); }
.nav-sub-action:hover { opacity: 0.9; }

.sub-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
  opacity: 0.6;
}
.sub-plus {
  font-size: 14px; font-weight: 700;
  flex-shrink: 0; line-height: 1;
}
.sub-label { overflow: hidden; text-overflow: ellipsis; }
.nav-sub-empty {
  padding: 8px 12px 8px 38px;
  color: var(--on-surface-variant);
  opacity: 0.5;
  font-size: 12px;
  font-style: italic;
}

/* Bottom */
.side-bottom {
  border-top: 1px solid var(--sidebar-border);
  padding: 8px 0 0;
  flex-shrink: 0;
}

.platform-status-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px 16px;
  position: relative;
  transition: all 0.25s ease;
}

.side-menu.collapsed .platform-status-container {
  padding: 12px 0;
  justify-content: center;
}

.platform-version-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  overflow: hidden;
  transition: opacity 0.2s ease, width 0.2s ease;
  width: 100%;
}

.side-menu.collapsed .platform-version-info {
  width: 0;
  opacity: 0;
  pointer-events: none;
  display: none;
}

.platform-version-label {
  font-size: 11px;
  color: var(--on-surface-variant);
  font-weight: 500;
  white-space: nowrap;
}

.platform-version-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--on-surface);
  white-space: nowrap;
}

.status-indicator-wrapper {
  position: relative;
  flex-shrink: 0;
}

.status-indicator-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  transition: var(--transition);
}

.status-indicator-btn:hover {
  background: var(--surface-container-high);
}

.status-indicator-btn.green {
  color: var(--success);
  border-color: color-mix(in srgb, var(--success) 30%, var(--border));
  background: color-mix(in srgb, var(--success) 8%, transparent);
}
.status-indicator-btn.amber {
  color: var(--warning);
  border-color: color-mix(in srgb, var(--warning) 30%, var(--border));
  background: color-mix(in srgb, var(--warning) 8%, transparent);
}
.status-indicator-btn.red {
  color: var(--error);
  border-color: color-mix(in srgb, var(--error) 30%, var(--border));
  background: color-mix(in srgb, var(--error) 8%, transparent);
}

.status-popup {
  position: absolute;
  bottom: 0;
  left: 100%;
  margin-left: 12px;
  width: 180px;
  background: var(--surface-container);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: 10px 12px;
  z-index: 1000;
  animation: slide-in 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slide-in {
  from { transform: translateX(-10px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.status-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

.status-popup-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-popup-refresh-btn {
  background: transparent;
  border: none;
  color: var(--on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.status-popup-refresh-btn:hover {
  color: var(--on-surface);
  background: var(--surface-container-high);
}

.status-popup-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.service-name-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.service-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.service-dot.green { background-color: var(--success); box-shadow: 0 0 6px var(--success); }
.service-dot.amber { background-color: var(--warning); box-shadow: 0 0 6px var(--warning); }
.service-dot.red { background-color: var(--error); box-shadow: 0 0 6px var(--error); }

.service-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--on-surface);
}

.service-status-label {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
}
.service-status-label.green {
  color: var(--success);
  background: color-mix(in srgb, var(--success) 12%, transparent);
}
.service-status-label.amber {
  color: var(--warning);
  background: color-mix(in srgb, var(--warning) 12%, transparent);
}
.service-status-label.red {
  color: var(--error);
  background: color-mix(in srgb, var(--error) 12%, transparent);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}



/* Expand animation */
.expand-enter-active, .expand-leave-active {
  transition: max-height 0.25s ease, opacity 0.25s ease;
  max-height: 400px;
}
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }

/* Icon semantic classes */
.icon-on-primary { color: var(--on-primary-container); }
.icon-muted      { color: var(--on-surface-variant); }
</style>
