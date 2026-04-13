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
          <div v-else-if="cubeStore.error" class="alert alert-warning" style="margin-bottom: 16px;">
            ⚠️ No se pudo cargar la configuración del servidor
          </div>

          <div class="form-group">
            <label class="form-label">Nombre de configuración</label>
            <input
              v-model="configName"
              type="text"
              class="form-input"
              placeholder="Mi conexión CubeJS"
            />
            <span class="form-hint">Identificador para esta configuración</span>
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
            <span class="form-hint">JWT token de autenticación generado con tu secret de Cube (se almacena encriptado)</span>
          </div>

          <div class="sc-actions">
            <button class="btn btn-secondary" @click="testConnection" :disabled="testing">
              <span v-if="testing" class="btn-spin"></span>
              <span v-else>🔍 Probar conexión</span>
            </button>
            <button 
              class="btn btn-primary" 
              @click="saveConnection" 
              :disabled="saving || !authStore.isDesigner"
            >
              <span v-if="saving" class="btn-spin"></span>
              <span v-else>💾 Guardar en servidor</span>
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

      <!-- LLM / IA -->
      <div v-if="authStore.isDesigner" class="settings-card card">
        <div class="sc-header">
          <div class="sc-icon">✦</div>
          <div>
            <h3 class="sc-title">LLM / Inteligencia Artificial</h3>
            <p class="sc-desc">Claves API por proveedor y modelo asignado por operación</p>
          </div>
        </div>
        <div class="sc-body">
          <div v-if="llmStore.isConfigured" class="alert alert-success">
            ✅ Al menos un proveedor configurado
          </div>
          <div v-else class="alert alert-error">
            ⚠️ Sin clave API — las funciones de IA no estarán disponibles
          </div>

          <!-- One key field per provider -->
          <div v-for="prov in llmProviders" :key="prov.id" class="form-group">
            <label class="form-label">
              <span class="provider-icon">{{ prov.icon }}</span>
              {{ prov.apiKeyLabel }}
            </label>
            <div style="position:relative">
              <input
                v-model="llmKeys[prov.id]"
                :type="showLlmKey[prov.id] ? 'text' : 'password'"
                class="form-input"
                :placeholder="prov.apiKeyPlaceholder"
                autocomplete="off"
                style="padding-right:40px"
              />
              <button
                type="button"
                style="position:absolute;right:8px;top:50%;transform:translateY(-50%);border:none;background:none;cursor:pointer;color:var(--text-secondary)"
                @click="showLlmKey[prov.id] = !showLlmKey[prov.id]"
              >{{ showLlmKey[prov.id] ? '🙈' : '👁️' }}</button>
            </div>
            <span class="form-hint">
              Obtén tu clave en <a :href="prov.docsUrl" target="_blank" rel="noopener">{{ prov.docsUrl }} →</a>
              <span v-if="llmKeys[prov.id]" style="color:var(--success);"> • 🔒 Se almacenará encriptado</span>
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">Modelo por operación</label>
            <div class="llm-ops-table">
              <div class="llm-ops-header">
                <span>Operación</span>
                <span>Proveedor / Modelo</span>
              </div>
              <div v-for="op in llmOperations" :key="op.id" class="llm-ops-row">
                <div>
                  <div class="llm-op-label">{{ op.label }}</div>
                  <div class="llm-op-desc">{{ op.description }}</div>
                </div>
                <select
                  :value="llmStore.models[op.id]"
                  class="form-input form-select"
                  style="width:auto;min-width:210px;flex-shrink:0"
                  @change="llmStore.setModel(op.id, $event.target.value)"
                >
                  <optgroup v-for="prov in llmProviders" :key="prov.id" :label="prov.label">
                    <option v-for="m in prov.models" :key="m.id" :value="prov.id + ':' + m.id">
                      {{ m.label }}
                    </option>
                  </optgroup>
                </select>
              </div>
            </div>
          </div>

          <div class="sc-actions">
            <button 
              class="btn btn-primary" 
              @click="saveLlm" 
              :disabled="savingLlm || !authStore.isDesigner"
            >
              <span v-if="savingLlm" class="btn-spin"></span>
              <span v-else>💾 Guardar en servidor</span>
            </button>
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
      <!-- Color Palettes (designers only) -->
      <div v-if="authStore.isDesigner" class="settings-card card palette-mgr-card">
        <div class="sc-header">
          <div class="sc-icon">🎨</div>
          <div>
            <h3 class="sc-title">Paletas de colores</h3>
            <p class="sc-desc">Gestiona las paletas disponibles para dashboards y widgets. La paleta predeterminada se aplica automáticamente a los nuevos dashboards.</p>
          </div>
        </div>

        <div class="sc-body">

          <!-- Palette list -->
          <div class="pal-list">
            <div
              v-for="palette in paletteStore.allPalettes"
              :key="palette.id"
              class="pal-row"
              :class="{ 'pal-row--default': paletteStore.defaultPaletteId === palette.id }"
            >
              <div class="pal-row-swatches">
                <span
                  v-for="c in palette.colors.slice(0, 8)"
                  :key="c"
                  class="pal-swatch"
                  :style="{ background: c }"
                />
              </div>
              <span class="pal-row-name">{{ palette.label }}</span>
              <span v-if="paletteStore.defaultPaletteId === palette.id" class="pal-default-badge">
                Por defecto
              </span>
              <div class="pal-row-actions">
                <button
                  class="btn-icon"
                  :data-tooltip="paletteStore.defaultPaletteId === palette.id ? 'Quitar predeterminada' : 'Establecer como predeterminada'"
                  @click="paletteStore.setDefault(palette.id)"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon :fill="paletteStore.defaultPaletteId === palette.id ? 'currentColor' : 'none'" points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </button>
                <button
                  class="btn-icon"
                  data-tooltip="Editar"
                  @click="startEditPalette(palette)"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button
                  class="btn-icon"
                  data-tooltip="Eliminar"
                  :disabled="paletteStore.allPalettes.length <= 1"
                  @click="confirmDeletePalette(palette)"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--error)" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    <path d="M10 11v6M14 11v6"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Add / Edit form -->
          <div class="pal-form" v-if="palForm.open">
            <h4 class="pal-form-title">{{ palForm.editId ? 'Editar paleta' : 'Nueva paleta' }}</h4>
            <div class="form-group">
              <label class="form-label">Nombre</label>
              <input v-model="palForm.label" class="form-input" placeholder="Ej: Corporativa" maxlength="40" />
            </div>
            <div class="form-group">
              <label class="form-label">Colores (mínimo 6)</label>
              <div class="pal-color-inputs">
                <div v-for="(c, idx) in palForm.colors" :key="idx" class="pal-color-slot">
                  <input type="color" v-model="palForm.colors[idx]" class="pal-color-input" />
                  <button
                    v-if="palForm.colors.length > 6"
                    class="pal-color-remove"
                    @click="palForm.colors.splice(idx, 1)"
                    title="Quitar"
                  >×</button>
                </div>
                <button
                  v-if="palForm.colors.length < 12"
                  class="pal-color-add"
                  @click="palForm.colors.push('#cccccc')"
                >+</button>
              </div>
              <div class="pal-form-preview">
                <span
                  v-for="c in palForm.colors"
                  :key="c + Math.random()"
                  class="pal-swatch pal-swatch--lg"
                  :style="{ background: c }"
                />
              </div>
            </div>
            <div class="sc-actions">
              <button class="btn btn-secondary" @click="closePalForm">Cancelar</button>
              <button
                class="btn btn-primary"
                :disabled="!palForm.label.trim() || palForm.colors.length < 6"
                @click="savePalette"
              >
                {{ palForm.editId ? 'Guardar cambios' : 'Añadir paleta' }}
              </button>
            </div>
          </div>

          <div class="sc-actions" v-else>
            <button class="btn btn-secondary" @click="openNewPalForm">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Nueva paleta
            </button>
            <button class="btn btn-secondary" @click="paletteStore.resetToBuiltIn">
              Restaurar predefinidas
            </button>
          </div>

          <!-- Delete confirm -->
          <div v-if="deletingPalette" class="pal-delete-confirm">
            <span>¿Eliminar <strong>{{ deletingPalette.label }}</strong>?</span>
            <button class="btn btn-secondary btn-sm" @click="deletingPalette = null">Cancelar</button>
            <button class="btn btn-sm" style="background:var(--error);color:#fff;border-color:var(--error)" @click="doDeletePalette">Eliminar</button>
          </div>

        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCubeStore } from '@/stores/cubejs'
import { useDashboardStore } from '@/stores/dashboard'
import { useUIStore } from '@/stores/ui'
import { useLlmStore, PROVIDERS, LLM_OPERATIONS } from '@/stores/llm'
import { useColorPaletteStore } from '@/stores/colorPalettes'

const authStore = useAuthStore()
const cubeStore = useCubeStore()
const paletteStore = useColorPaletteStore()
const dashboardStore = useDashboardStore()
const uiStore = useUIStore()
const llmStore = useLlmStore()

uiStore.setBreadcrumbs(['Configuración'])

// CubeJS Config refs
const apiUrl = ref('')
const apiToken = ref('')
const configName = ref('Default')
const showToken = ref(false)
const testing = ref(false)
const saving = ref(false)
const openCubes = ref([])

// LLM refs
const llmKeys = ref({})
const showLlmKey = ref({})
const savingLlm = ref(false)

// Load config from backend on mount
onMounted(async () => {
  // Load CubeJS config
  await cubeStore.loadConfigFromBackend()
  apiUrl.value = cubeStore.apiUrl
  apiToken.value = cubeStore.token
  configName.value = cubeStore.configName

  // Load LLM config
  await llmStore.loadConfigFromBackend()
  // Check for legacy data and migrate if needed
  await llmStore.migrateFromLegacy()
  // Initialize LLM refs from store
  for (const prov of PROVIDERS) {
    llmKeys.value[prov.id] = llmStore.keys[prov.id] || ''
    showLlmKey.value[prov.id] = false
  }

  // Load palette config from backend
  await paletteStore.loadFromBackend()
})

// LLM providers and operations
const llmProviders = PROVIDERS
const llmOperations = LLM_OPERATIONS

async function saveLlm() {
  if (!authStore.isDesigner) {
    uiStore.addAlert({ type: 'error', message: 'No tienes permisos para guardar la configuración' })
    return
  }

  savingLlm.value = true

  // Update store with current values
  for (const prov of PROVIDERS) {
    llmStore.setKey(prov.id, llmKeys.value[prov.id] ?? '')
  }

  // Save to backend
  const result = await llmStore.saveConfigToBackend()
  savingLlm.value = false

  if (result.success) {
    uiStore.addAlert({ type: 'success', message: 'Configuración LLM guardada en el servidor' })
  } else {
    uiStore.addAlert({ type: 'error', message: `Error al guardar: ${result.error}` })
  }
}

const myDashboards = computed(() => {
  if (authStore.isDesigner) return dashboardStore.allDashboards
  return dashboardStore.dashboardsForUser(authStore.user?.id || '')
})

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

async function saveConnection() {
  if (!authStore.isDesigner) {
    uiStore.addAlert({ type: 'error', message: 'No tienes permisos para guardar la configuración' })
    return
  }

  saving.value = true
  const result = await cubeStore.saveConfigToBackend(
    configName.value,
    apiUrl.value,
    apiToken.value,
    true // isActive
  )
  saving.value = false

  if (result.success) {
    uiStore.addAlert({ type: 'success', message: 'Configuración guardada correctamente en el servidor' })
  } else {
    uiStore.addAlert({ type: 'error', message: `Error al guardar: ${result.error}` })
  }
}

function toggleCube(name) {
  const idx = openCubes.value.indexOf(name)
  if (idx === -1) openCubes.value.push(name)
  else openCubes.value.splice(idx, 1)
}

// ── Palette management ────────────────────────────────────────
const deletingPalette = ref(null)

const palForm = ref({ open: false, editId: null, label: '', colors: [] })

function openNewPalForm() {
  palForm.value = {
    open: true,
    editId: null,
    label: '',
    colors: ['#1890ff','#52c41a','#faad14','#f5222d','#722ed1','#13c2c2','#fa8c16','#eb2f96']
  }
}

function startEditPalette(palette) {
  palForm.value = {
    open: true,
    editId: palette.id,
    label: palette.label,
    colors: [...palette.colors]
  }
}

function closePalForm() {
  palForm.value.open = false
}

function savePalette() {
  const { editId, label, colors } = palForm.value
  if (editId) {
    paletteStore.updatePalette(editId, label.trim(), colors)
  } else {
    paletteStore.addPalette(label.trim(), colors)
  }
  palForm.value.open = false
  uiStore.addAlert({ type: 'success', message: editId ? 'Paleta actualizada' : 'Paleta añadida' })
}

function confirmDeletePalette(palette) {
  deletingPalette.value = palette
}

function doDeletePalette() {
  paletteStore.deletePalette(deletingPalette.value.id)
  deletingPalette.value = null
  uiStore.addAlert({ type: 'success', message: 'Paleta eliminada' })
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

/* Info table */
.info-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.info-table td { padding: 8px 0; border-bottom: 1px solid var(--border); }
.info-table td:first-child { color: var(--text-secondary); width: 50%; }
.info-table tr:last-child td { border-bottom: none; }

/* LLM */
.provider-icon { margin-right: 4px; }
.llm-ops-table { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.llm-ops-header {
  display: grid; grid-template-columns: 1fr auto;
  padding: 8px 14px; background: var(--bg);
  font-size: 11px; font-weight: 700; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
.llm-ops-row {
  display: grid; grid-template-columns: 1fr auto;
  align-items: center; gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
}
.llm-ops-row:last-child { border-bottom: none; }
.llm-op-label { font-size: 13px; font-weight: 600; color: var(--text); }
.llm-op-desc  { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

@keyframes spin { to { transform: rotate(360deg); } }

/* Palette manager */
.palette-mgr-card { grid-column: 1 / -1; }

.pal-list { display: flex; flex-direction: column; gap: 6px; }

.pal-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  transition: border-color 0.15s;
}
.pal-row--default { border-color: var(--primary); background: #e6f4ff; }

.pal-row-swatches { display: flex; gap: 3px; flex-shrink: 0; }
.pal-swatch {
  width: 16px; height: 16px;
  border-radius: 3px;
  display: inline-block;
  flex-shrink: 0;
}
.pal-swatch--lg { width: 22px; height: 22px; border-radius: 4px; }

.pal-row-name { font-size: 13px; font-weight: 500; color: var(--text); flex: 1; min-width: 0; }

.pal-default-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--primary);
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.pal-row-actions { display: flex; gap: 2px; flex-shrink: 0; }

.pal-form {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.pal-form-title { font-size: 14px; font-weight: 600; color: var(--text); margin: 0; }

.pal-color-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 6px;
}
.pal-color-slot { position: relative; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.pal-color-input {
  width: 36px; height: 36px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px;
  cursor: pointer;
  background: #fff;
}
.pal-color-remove {
  position: absolute; top: -6px; right: -6px;
  width: 16px; height: 16px;
  border-radius: 50%;
  border: none;
  background: var(--error);
  color: #fff;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pal-color-add {
  width: 36px; height: 36px;
  border: 2px dashed var(--border);
  border-radius: 6px;
  background: transparent;
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pal-color-add:hover { border-color: var(--primary); color: var(--primary); }

.pal-form-preview {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.pal-delete-confirm {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--error);
  border-radius: 8px;
  background: #fff2f0;
  font-size: 13px;
}
.pal-delete-confirm span { flex: 1; }
</style>
