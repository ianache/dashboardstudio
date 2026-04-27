<template>
  <aside class="side-menu" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <!-- Logo / Brand -->
    <div class="side-logo">
      <div class="logo-icon-wrap">
        <MIcon icon="analytics" :size="22" :fill="1" style="color:#fff" />
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
            <div class="nav-sub-item nav-sub-action" @click="createNewModel">
              <span class="sub-plus">+</span>Nuevo modelo
            </div>
            <router-link to="/models/data-types" class="nav-sub-item" :class="{ active: $route.name === 'DataTypes' }">
              <span class="sub-dot" />Tipos de datos
            </router-link>
            <router-link to="/models/knowledge-spaces" class="nav-sub-item" :class="{ active: $route.name === 'KnowledgeSpaces' }">
              <span class="sub-dot" />Knowledge Spaces
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
      <router-link to="/settings" class="nav-item" :class="{ active: $route.name === 'Settings' }">
        <MIcon icon="settings" :size="20" class="nav-icon" />
        <span class="nav-label">Configuración</span>
      </router-link>

      <div class="workspace-info">
        <div class="workspace-avatar">
          <MIcon icon="person" :size="18" style="color:#64748b" />
        </div>
        <div class="workspace-text">
          <p class="workspace-name">{{ authStore.user?.name || 'Usuario' }}</p>
          <p class="workspace-role">{{ authStore.isDesigner ? 'Diseñador' : 'Visualizador' }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import MIcon from '@/components/common/MIcon.vue'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

const openSections = ref({ design: true, models: true, dashboards: true })

const isDesignerRoute = computed(() =>
  ['DesignerList', 'DesignerEdit'].includes(router.currentRoute.value.name)
)
const isModelRoute = computed(() =>
  ['ModelList', 'ModelEditor', 'DataTypes', 'KnowledgeSpaces'].includes(router.currentRoute.value.name)
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
function createNewModel() { router.push('/models?new=1') }
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
  z-index: 100;
  transition: width 0.25s ease;
  overflow: hidden;
  box-shadow: 4px 0 20px rgba(0,0,0,0.3);
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
  background: #2563eb;
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
  color: #fff;
  font-size: 15px;
  white-space: nowrap;
  line-height: 1.2;
}
.logo-title strong { font-weight: 700; }
.logo-subtitle {
  color: #475569;
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
.side-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.nav-section { margin-bottom: 4px; }

.nav-section-title {
  font-size: 10px;
  font-weight: 700;
  color: rgba(255,255,255,0.25);
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
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
  border-radius: 8px;
  border-left: 3px solid transparent;
}
.nav-item:hover { color: #f1f5f9; background: rgba(15,23,42,0.6); }
.nav-item.active {
  color: #fff;
  background: rgba(37,99,235,0.12);
  border-left-color: #3b82f6;
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
  color: rgba(255,255,255,0.25);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.nav-arrow.open { transform: rotate(180deg); }
.side-menu.collapsed .nav-arrow { opacity: 0; }

.nav-badge {
  background: #2563eb;
  color: #fff;
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
  background: rgba(0,0,0,0.2);
  margin: 0 8px;
  border-radius: 6px;
}
.side-menu.collapsed .nav-sub { display: none; }

.nav-sub-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 38px;
  color: rgba(255,255,255,0.4);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  border-radius: 6px;
}
.nav-sub-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
.nav-sub-item.active { color: #93c5fd; }
.nav-sub-action { color: rgba(96,165,250,0.8); }
.nav-sub-action:hover { color: #60a5fa; }

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
  color: rgba(255,255,255,0.2);
  font-size: 12px;
  font-style: italic;
}

/* Bottom */
.side-bottom {
  border-top: 1px solid var(--sidebar-border);
  padding: 8px 0 0;
  flex-shrink: 0;
}

.workspace-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px 16px;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .workspace-info { opacity: 0; }

.workspace-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #1e293b;
  border: 1px solid #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.workspace-text { overflow: hidden; }
.workspace-name {
  color: #fff;
  font-size: 12px; font-weight: 700;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.workspace-role { color: #475569; font-size: 10px; white-space: nowrap; }

/* Expand animation */
.expand-enter-active, .expand-leave-active {
  transition: max-height 0.25s ease, opacity 0.25s ease;
  max-height: 400px;
}
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
</style>
