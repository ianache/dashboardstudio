<template>
  <div class="settings-view">
    <div class="page-header">
      <h2 class="page-title">Configuración</h2>
      <p class="page-subtitle">Gestiona las conexiones y preferencias del sistema</p>
    </div>

    <div class="settings-grid">
      <!-- CubeJS Connection -->
      <div class="settings-card card">
        <div class="sc-header">
          <div class="sc-icon">🔌</div>
          <div>
            <h3 class="sc-title">Conexión CubeJS</h3>
            <p class="sc-desc">Configura el endpoint y el token de autenticación de tu instancia Cube</p>
          </div>
        </div>

        <div class="sc-body">
          <div v-if="cubeStore.connected" class="alert alert-success" style="margin-bottom: 16px;">
            ✅ Conectado a CubeJS — {{ cubeStore.cubes.length }} cubos disponibles
          </div>
          <div v-else-if="cubeStore.metaError" class="alert alert-error" style="margin-bottom: 16px;">
            ⚠️ Error de conexión: {{ cubeStore.metaError }}
          </div>

          <div class="form-group">
            <label class="form-label">API URL</label>
            <input
              v-model="apiUrl"
              type="url"
              class="form-input"
              placeholder="http://localhost:4000/cubejs-api/v1"
            />
            <span class="form-hint">URL base de la API CubeJS (incluye /cubejs-api/v1)</span>
          </div>

          <div class="form-group">
            <label class="form-label">API Token</label>
            <div style="position: relative;">
              <input
                v-model="apiToken"
                :type="showToken ? 'text' : 'password'"
                class="form-input"
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                style="padding-right: 40px;"
              />
              <button
                type="button"
                style="position:absolute;right:8px;top:50%;transform:translateY(-50%);border:none;background:none;cursor:pointer;color:var(--text-secondary)"
                @click="showToken = !showToken"
              >
                {{ showToken ? '🙈' : '👁️' }}
              </button>
            </div>
            <span class="form-hint">JWT token de autenticación generado con tu secret de Cube</span>
          </div>

          <div class="sc-actions">
            <button class="btn btn-secondary" @click="testConnection" :disabled="testing">
              <span v-if="testing" class="btn-spin"></span>
              <span v-else>🔍 Probar conexión</span>
            </button>
            <button class="btn btn-primary" @click="saveConnection">
              💾 Guardar
            </button>
          </div>

          <!-- Schema viewer -->
          <div v-if="cubeStore.cubes.length > 0" class="schema-viewer">
            <h4 class="schema-title">Cubos disponibles</h4>
            <div class="cube-list">
              <div v-for="cube in cubeStore.cubes" :key="cube.name" class="cube-item">
                <div class="cube-item-header" @click="toggleCube(cube.name)">
                  <span>📦 {{ cube.name }}</span>
                  <span style="font-size:11px;color:var(--text-secondary)">
                    {{ cube.measures.length }} medidas · {{ cube.dimensions.length }} dimensiones
                  </span>
                  <span style="margin-left:auto">{{ openCubes.includes(cube.name) ? '▲' : '▼' }}</span>
                </div>
                <div v-if="openCubes.includes(cube.name)" class="cube-item-body">
                  <div class="cube-member-group-sm">
                    <span class="cg-title">Medidas:</span>
                    <span v-for="m in cube.measures" :key="m.name" class="member-tag measure">
                      {{ cube.name }}.{{ m.name }} ({{ m.type }})
                    </span>
                  </div>
                  <div class="cube-member-group-sm">
                    <span class="cg-title">Dimensiones:</span>
                    <span v-for="d in cube.dimensions" :key="d.name" class="member-tag dimension">
                      {{ cube.name }}.{{ d.name }} ({{ d.type }})
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- User Info -->
      <div class="settings-card card">
        <div class="sc-header">
          <div class="sc-icon">👤</div>
          <div>
            <h3 class="sc-title">Mi perfil</h3>
            <p class="sc-desc">Información de tu cuenta</p>
          </div>
        </div>
        <div class="sc-body">
          <div class="profile-display">
            <div class="profile-avatar">{{ authStore.user?.avatar }}</div>
            <div class="profile-info">
              <div class="pi-name">{{ authStore.user?.name }}</div>
              <div class="pi-email">{{ authStore.user?.email }}</div>
              <span class="badge" :class="authStore.isDesigner ? 'badge-blue' : 'badge-green'" style="margin-top:8px">
                {{ authStore.isDesigner ? '🎨 Diseñador' : '👁️ Visualizador' }}
              </span>
            </div>
          </div>

          <div class="divider"></div>

          <h4 style="font-size:14px;font-weight:600;margin-bottom:12px">Dashboards disponibles</h4>
          <div v-if="myDashboards.length === 0" class="form-hint">Sin dashboards asignados</div>
          <div v-else class="db-list-small">
            <div v-for="db in myDashboards" :key="db.id" class="dbs-item">
              <span>📊 {{ db.name }}</span>
              <span class="badge badge-blue">{{ db.widgets.length }} w.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- User Management (Designer only) -->
      <div v-if="authStore.isDesigner" class="settings-card card">
        <div class="sc-header">
          <div class="sc-icon">👥</div>
          <div>
            <h3 class="sc-title">Usuarios del sistema</h3>
            <p class="sc-desc">Lista de usuarios y sus dashboards asignados</p>
          </div>
        </div>
        <div class="sc-body">
          <div class="users-table">
            <div class="ut-header">
              <span>Usuario</span>
              <span>Rol</span>
              <span>Dashboards asignados</span>
            </div>
            <div v-for="user in authStore.allUsers" :key="user.id" class="ut-row">
              <div class="ut-user">
                <div class="ut-avatar">{{ user.avatar }}</div>
                <div>
                  <div class="ut-name">{{ user.name }}</div>
                  <div class="ut-email">{{ user.email }}</div>
                </div>
              </div>
              <div>
                <span class="badge" :class="user.role === 'designer' ? 'badge-blue' : 'badge-green'">
                  {{ user.role === 'designer' ? 'Diseñador' : 'Visualizador' }}
                </span>
              </div>
              <div class="ut-dbs">
                <span v-if="!getDashboardsForUser(user.id).length" class="form-hint">Ninguno</span>
                <span
                  v-for="db in getDashboardsForUser(user.id)"
                  :key="db.id"
                  class="badge badge-blue"
                  style="margin-right:4px"
                >{{ db.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- App Info -->
      <div class="settings-card card">
        <div class="sc-header">
          <div class="sc-icon">ℹ️</div>
          <div>
            <h3 class="sc-title">Acerca de</h3>
            <p class="sc-desc">Información del sistema</p>
          </div>
        </div>
        <div class="sc-body">
          <table class="info-table">
            <tbody>
              <tr><td>Aplicación</td><td><strong>Dashboard Studio</strong></td></tr>
              <tr><td>Versión</td><td>1.0.0</td></tr>
              <tr><td>Framework</td><td>Vue 3 + Pinia</td></tr>
              <tr><td>Gráficos</td><td>Apache ECharts v5</td></tr>
              <tr><td>Modelo semántico</td><td>CubeJS</td></tr>
              <tr><td>Almacenamiento</td><td>LocalStorage (demo)</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCubeStore } from '@/stores/cubejs'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'

const authStore = useAuthStore()
const cubeStore = useCubeStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()

uiStore.setBreadcrumbs(['Configuración'])

const apiUrl = ref(cubeStore.apiUrl)
const apiToken = ref(cubeStore.token)
const showToken = ref(false)
const testing = ref(false)
const openCubes = ref([])

const myDashboards = computed(() => {
  if (authStore.isDesigner) return dashboardStore.allDashboards
  return dashboardStore.dashboardsForUser(authStore.user?.id || '')
})

function getDashboardsForUser(userId) {
  return dashboardStore.allDashboards.filter(d => d.assignedUsers.includes(userId))
}

async function testConnection() {
  testing.value = true
  cubeStore.setConfig(apiUrl.value, apiToken.value)
  const result = await cubeStore.testConnection()
  testing.value = false

  if (result.success) {
    uiStore.addAlert({ type: 'success', message: `Conexión exitosa — ${cubeStore.cubes.length} cubos encontrados` })
  } else {
    uiStore.addAlert({ type: 'error', message: `Error de conexión: ${result.error}` })
  }
}

function saveConnection() {
  cubeStore.setConfig(apiUrl.value, apiToken.value)
  uiStore.addAlert({ type: 'success', message: 'Configuración guardada correctamente' })
}

function toggleCube(name) {
  const idx = openCubes.value.indexOf(name)
  if (idx === -1) openCubes.value.push(name)
  else openCubes.value.splice(idx, 1)
}
</script>

<style scoped>
.settings-view { max-width: 1100px; }

.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.settings-card { padding: 0; overflow: hidden; }

.sc-header {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: #fafafa;
}
.sc-icon { font-size: 28px; flex-shrink: 0; }
.sc-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 2px; }
.sc-desc { font-size: 13px; color: var(--text-secondary); }

.sc-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

.sc-actions { display: flex; gap: 8px; }
.btn-spin {
  width: 14px; height: 14px;
  border: 2px solid rgba(0,0,0,0.15);
  border-top-color: var(--text);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

/* Schema viewer */
.schema-viewer { margin-top: 8px; }
.schema-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 10px; }
.cube-list { display: flex; flex-direction: column; gap: 6px; }
.cube-item { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.cube-item-header {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; background: var(--bg);
  cursor: pointer; font-size: 13px; font-weight: 500; color: var(--text);
}
.cube-item-header:hover { background: var(--primary-light); }
.cube-item-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.cube-member-group-sm { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }
.cg-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); white-space: nowrap; flex-shrink: 0; }
.member-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  font-family: monospace;
}
.member-tag.measure { background: var(--primary-light); color: var(--primary); }
.member-tag.dimension { background: #f6ffed; color: var(--success); }

/* Profile */
.profile-display { display: flex; gap: 16px; align-items: flex-start; }
.profile-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--primary); color: #fff;
  font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.pi-name { font-size: 16px; font-weight: 600; color: var(--text); }
.pi-email { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.db-list-small { display: flex; flex-direction: column; gap: 6px; }
.dbs-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: var(--bg); border-radius: 6px;
  font-size: 13px; color: var(--text);
}

/* Users table */
.users-table { display: flex; flex-direction: column; gap: 0; }
.ut-header {
  display: grid; grid-template-columns: 2fr 1fr 2fr;
  padding: 8px 12px; background: var(--bg);
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
  border-radius: 6px; margin-bottom: 4px;
}
.ut-row {
  display: grid; grid-template-columns: 2fr 1fr 2fr;
  padding: 10px 12px; align-items: center;
  border-bottom: 1px solid var(--border);
}
.ut-row:last-child { border-bottom: none; }
.ut-user { display: flex; align-items: center; gap: 10px; }
.ut-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--primary); color: #fff;
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.ut-name { font-size: 13px; font-weight: 500; color: var(--text); }
.ut-email { font-size: 11px; color: var(--text-secondary); }
.ut-dbs { display: flex; flex-wrap: wrap; gap: 4px; }

/* Info table */
.info-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.info-table td { padding: 8px 0; border-bottom: 1px solid var(--border); }
.info-table td:first-child { color: var(--text-secondary); width: 50%; }
.info-table tr:last-child td { border-bottom: none; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
