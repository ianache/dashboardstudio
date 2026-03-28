<template>
  <aside class="side-menu" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <!-- Logo / Brand -->
    <div class="side-logo">
      <div class="logo-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="6" fill="#1890ff"/>
          <rect x="5" y="10" width="5" height="12" rx="1" fill="white"/>
          <rect x="11.5" y="6" width="5" height="16" rx="1" fill="white"/>
          <rect x="18" y="13" width="5" height="9" rx="1" fill="white"/>
        </svg>
      </div>
      <span class="logo-text">Dashboard<strong>Studio</strong></span>
    </div>

    <!-- Navigation -->
    <nav class="side-nav">
      <div class="nav-section">
        <router-link to="/" class="nav-item" :class="{ active: $route.name === 'Home' }">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </span>
          <span class="nav-label">Inicio</span>
        </router-link>
      </div>

      <!-- Designer section (only for designers) -->
      <div v-if="authStore.isDesigner" class="nav-section">
        <div class="nav-section-title">DISEÑO</div>
        <div class="nav-item" :class="{ active: isDesignerRoute }" @click="toggleSection('design')">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
          </span>
          <span class="nav-label">Mis Dashboards</span>
          <span class="nav-arrow" :class="{ open: openSections.design }">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
              <path d="M2 4l4 4 4-4"/>
            </svg>
          </span>
        </div>
        <transition name="expand">
          <div v-show="openSections.design" class="nav-sub">
            <router-link to="/designer" class="nav-sub-item" :class="{ active: $route.name === 'DesignerList' }">
              <span class="sub-dot">•</span> Ver todos
            </router-link>
            <div class="nav-sub-item nav-sub-action" @click="createNewDashboard">
              <span class="sub-dot">+</span> Nuevo dashboard
            </div>
          </div>
        </transition>

        <!-- Models subsection -->
        <div class="nav-item" :class="{ active: isModelRoute }" @click="toggleSection('models')">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="8" height="6" rx="1"/>
              <rect x="14" y="3" width="8" height="6" rx="1"/>
              <rect x="8" y="15" width="8" height="6" rx="1"/>
              <line x1="6" y1="9" x2="12" y2="15"/>
              <line x1="18" y1="9" x2="12" y2="15"/>
            </svg>
          </span>
          <span class="nav-label">Modelos</span>
          <span class="nav-arrow" :class="{ open: openSections.models }">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
              <path d="M2 4l4 4 4-4"/>
            </svg>
          </span>
        </div>
        <transition name="expand">
          <div v-show="openSections.models" class="nav-sub">
            <router-link to="/models" class="nav-sub-item" :class="{ active: $route.name === 'ModelList' }">
              <span class="sub-dot">•</span> Ver todos
            </router-link>
            <div class="nav-sub-item nav-sub-action" @click="createNewModel">
              <span class="sub-dot">+</span> Nuevo modelo
            </div>
          </div>
        </transition>
      </div>

      <!-- Dashboards section (for all users) -->
      <div class="nav-section">
        <div class="nav-section-title">DASHBOARDS</div>
        <div class="nav-item" :class="{ active: isDashboardRoute }" @click="toggleSection('dashboards')">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="3" width="15" height="13" rx="2"/>
              <path d="M16 8h4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5v-4"/>
              <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
            </svg>
          </span>
          <span class="nav-label">Dashboards</span>
          <span class="nav-badge" v-if="availableDashboards.length">{{ availableDashboards.length }}</span>
          <span class="nav-arrow" :class="{ open: openSections.dashboards }">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
              <path d="M2 4l4 4 4-4"/>
            </svg>
          </span>
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
              <span class="sub-dot">•</span>
              <span class="sub-label">{{ db.name }}</span>
            </router-link>
          </div>
        </transition>
      </div>
    </nav>

    <!-- Bottom section -->
    <div class="side-bottom">
      <router-link to="/settings" class="nav-item" :class="{ active: $route.name === 'Settings' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </span>
        <span class="nav-label">Configuración</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

const openSections = ref({
  design: true,
  models: true,
  dashboards: true
})

const isDesignerRoute = computed(() =>
  ['DesignerList', 'DesignerEdit'].includes(router.currentRoute.value.name)
)

const isModelRoute = computed(() =>
  ['ModelList', 'ModelEditor'].includes(router.currentRoute.value.name)
)

const isDashboardRoute = computed(() =>
  router.currentRoute.value.name === 'DashboardView'
)

const availableDashboards = computed(() => {
  if (authStore.isDesigner) return dashboardStore.allDashboards
  return dashboardStore.dashboardsForUser(authStore.user?.id || '')
})

function toggleSection(name) {
  openSections.value[name] = !openSections.value[name]
}

function createNewDashboard() {
  router.push('/designer?new=1')
}

function createNewModel() {
  router.push('/models?new=1')
}
</script>

<style scoped>
.side-menu {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.25s ease;
  overflow: hidden;
}

.side-menu.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* Logo */
.side-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: var(--topbar-height);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0;
  overflow: hidden;
}
.logo-text {
  color: #fff;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.2s;
}
.logo-text strong { font-weight: 700; }
.side-menu.collapsed .logo-text { opacity: 0; pointer-events: none; }

/* Nav */
.side-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0;
}
.side-nav::-webkit-scrollbar { width: 4px; }
.side-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); }

.nav-section { margin-bottom: 4px; }

.nav-section-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255,255,255,0.35);
  padding: 8px 20px 4px;
  letter-spacing: 0.8px;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .nav-section-title { opacity: 0; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: rgba(255,255,255,0.65);
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  white-space: nowrap;
  border-radius: 0;
  position: relative;
}
.nav-item:hover { color: #fff; background: rgba(255,255,255,0.06); }
.nav-item.active { color: #fff; background: var(--primary); }
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #fff;
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.nav-icon svg { width: 18px; height: 18px; }

.nav-label {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  transition: opacity 0.2s;
}
.side-menu.collapsed .nav-label { opacity: 0; pointer-events: none; }

.nav-arrow {
  color: rgba(255,255,255,0.4);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.nav-arrow.open { transform: rotate(180deg); }
.side-menu.collapsed .nav-arrow { opacity: 0; }

.nav-badge {
  background: var(--primary);
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
  background: rgba(0,0,0,0.15);
}
.side-menu.collapsed .nav-sub { display: none; }

.nav-sub-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px 8px 44px;
  color: rgba(255,255,255,0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
}
.nav-sub-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
.nav-sub-item.active { color: #fff; }

.nav-sub-action { color: rgba(24,144,255,0.8); }
.nav-sub-action:hover { color: var(--primary); }

.sub-dot { flex-shrink: 0; font-size: 16px; line-height: 1; }
.sub-label { overflow: hidden; text-overflow: ellipsis; }

.nav-sub-empty {
  padding: 8px 20px 8px 44px;
  color: rgba(255,255,255,0.25);
  font-size: 12px;
  font-style: italic;
}

/* Bottom */
.side-bottom {
  border-top: 1px solid rgba(255,255,255,0.08);
  padding: 8px 0;
  flex-shrink: 0;
}

/* Expand animation */
.expand-enter-active, .expand-leave-active { transition: max-height 0.25s ease, opacity 0.25s ease; max-height: 400px; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
</style>
