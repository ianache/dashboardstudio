<template>
  <header class="top-bar">
    <!-- Hamburger -->
    <button class="hamburger-btn" @click.stop="uiStore.toggleSidebar()" data-tooltip="Colapsar menú">
      <MIcon icon="menu" :size="22" />
    </button>

    <!-- Breadcrumb -->
    <nav class="breadcrumb" aria-label="breadcrumb">
      <router-link to="/" class="bread-home">
        <MIcon icon="home" :size="16" />
      </router-link>
      <template v-for="(crumb, i) in breadcrumbs" :key="i">
        <span class="bread-sep">/</span>
        <span class="bread-item" :class="{ last: i === breadcrumbs.length - 1 }">{{ crumb }}</span>
      </template>
    </nav>

    <div class="top-bar-spacer" />

    <!-- Right actions -->
    <div class="top-bar-actions">
      <!-- Alerts -->
      <div class="dropdown-wrapper" @click.stop>
        <button
          class="action-btn"
          :class="{ active: uiStore.alertsOpen }"
          @click.stop="uiStore.toggleAlerts()"
          data-tooltip="Alertas"
        >
          <MIcon icon="notifications" :size="20" />
          <span v-if="uiStore.unreadAlerts > 0" class="action-badge">{{ uiStore.unreadAlerts }}</span>
        </button>

        <transition name="dropdown">
          <div v-if="uiStore.alertsOpen" class="dropdown-panel alerts-panel">
            <div class="dp-header">
              <span>Alertas</span>
              <button v-if="uiStore.alerts.length" class="dp-action" @click="uiStore.markAllAlertsRead()">
                Marcar todas como leídas
              </button>
            </div>
            <div class="dp-body">
              <div v-if="uiStore.alerts.length === 0" class="dp-empty">
                Sin alertas
              </div>
              <div
                v-for="alert in uiStore.alerts"
                :key="alert.id"
                class="alert-item"
                :class="{ unread: !alert.read }"
                @click="uiStore.markAlertRead(alert.id)"
              >
                <span class="alert-dot" :class="`alert-dot-${alert.type || 'info'}`"></span>
                <div class="alert-content">
                  <div class="alert-msg">{{ alert.message }}</div>
                  <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- User menu -->
      <div class="dropdown-wrapper" @click.stop>
        <button
          class="user-btn"
          :class="{ active: uiStore.userMenuOpen }"
          @click.stop="uiStore.toggleUserMenu()"
        >
          <div class="user-avatar">{{ authStore.user?.avatar || '?' }}</div>
          <div class="user-info" v-if="!uiStore.sidebarCollapsed">
            <span class="user-name">{{ authStore.user?.name }}</span>
            <span class="user-role">{{ authStore.isDesigner ? 'Diseñador' : 'Visualizador' }}</span>
          </div>
          <MIcon icon="expand_more" :size="18" class="user-caret" />
        </button>

        <transition name="dropdown">
          <div v-if="uiStore.userMenuOpen" class="dropdown-panel user-panel">
            <div class="dp-user-header">
              <div class="dp-avatar">{{ authStore.user?.avatar || '?' }}</div>
              <div>
                <div class="dp-name">{{ authStore.user?.name }}</div>
                <div class="dp-email">{{ authStore.user?.email }}</div>
                <span class="badge badge-blue" style="margin-top:4px">
                  {{ authStore.isDesigner ? 'Diseñador' : 'Visualizador' }}
                </span>
              </div>
            </div>
            <div class="divider" style="margin: 0"></div>
            <router-link to="/settings" class="dp-item" @click="uiStore.closeDropdowns()">
              <MIcon icon="settings" :size="18" />
              Configuración
            </router-link>
            <div class="dp-item dp-danger" @click="handleLogout">
              <MIcon icon="logout" :size="18" />
              Cerrar sesión
            </div>
          </div>
        </transition>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import MIcon from '@/components/common/MIcon.vue'

const uiStore = useUIStore()
const authStore = useAuthStore()

const breadcrumbs = computed(() => uiStore.breadcrumbs)

function handleLogout() {
  uiStore.closeDropdowns()
  authStore.logout()
  // kc.logout() handles the browser redirect to Keycloak's logout endpoint
  // and back to the app — do NOT call router.push() here or it may abort that redirect
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return 'hace un momento'
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`
  return d.toLocaleDateString('es')
}
</script>

<style scoped>
.top-bar {
  height: var(--topbar-height);
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 90;
  box-shadow: 0 1px 4px rgba(0,21,41,0.06);
  flex-shrink: 0;
}

.hamburger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: 6px;
  transition: var(--transition);
  flex-shrink: 0;
}
.hamburger-btn:hover { background: var(--bg); color: var(--text); }

/* Breadcrumb */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.bread-home {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  text-decoration: none;
  flex-shrink: 0;
}
.bread-home:hover { color: var(--primary); }
.bread-sep { color: var(--text-secondary); font-size: 12px; flex-shrink: 0; }
.bread-item {
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bread-item.last { color: var(--text); font-weight: 500; }

.top-bar-spacer { flex: 1; }

/* Actions */
.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: var(--transition);
}
.action-btn:hover, .action-btn.active { background: var(--bg); color: var(--text); }

.action-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: var(--error);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* User button */
.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--transition);
}
.user-btn:hover, .user-btn.active { background: var(--bg); }

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}
.user-name { font-size: 13px; font-weight: 500; color: var(--text); }
.user-role { font-size: 11px; color: var(--text-secondary); }
.user-caret { color: var(--text-secondary); flex-shrink: 0; }

/* Dropdown panels */
.dropdown-wrapper { position: relative; }

.dropdown-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow-md);
  z-index: 200;
  min-width: 240px;
  overflow: hidden;
}

.alerts-panel { width: 300px; }

.dp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.dp-action { font-size: 12px; font-weight: 400; color: var(--primary); cursor: pointer; border: none; background: none; }
.dp-action:hover { text-decoration: underline; }

.dp-body { max-height: 320px; overflow-y: auto; }
.dp-empty { padding: 24px; text-align: center; color: var(--text-secondary); font-size: 13px; }

.alert-item {
  display: flex;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border);
}
.alert-item:last-child { border-bottom: none; }
.alert-item:hover { background: var(--bg); }
.alert-item.unread { background: var(--primary-light); }
.alert-item.unread:hover { background: #d0e9ff; }

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.alert-dot-info { background: var(--primary); }
.alert-dot-success { background: var(--success); }
.alert-dot-warning { background: var(--warning); }
.alert-dot-error { background: var(--error); }

.alert-content { flex: 1; min-width: 0; }
.alert-msg { font-size: 13px; color: var(--text); line-height: 1.4; }
.alert-time { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

/* User dropdown */
.user-panel { width: 260px; }

.dp-user-header {
  display: flex;
  gap: 12px;
  padding: 16px;
  align-items: flex-start;
}
.dp-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.dp-name { font-size: 14px; font-weight: 600; color: var(--text); }
.dp-email { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.dp-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--text);
  cursor: pointer;
  transition: background 0.15s;
  text-decoration: none;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
}
.dp-item:hover { background: var(--bg); }
.dp-danger { color: var(--error); }
.dp-danger:hover { background: #fff2f0; }

/* Dropdown animation */
.dropdown-enter-active, .dropdown-leave-active { transition: opacity 0.15s, transform 0.15s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
