<template>
  <div class="configurator-view">
    <!-- Header -->
    <header class="configurator-header">
      <div class="header-left">
        <button class="btn btn-secondary btn-sm" @click="handleCancel" :disabled="saving">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Volver
        </button>
        <div class="header-title">
          <input 
            type="text" 
            :value="store.title" 
            @input="store.setTitle($event.target.value)"
            placeholder="Título del gráfico"
            class="title-input"
          />
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleCancel" :disabled="saving">Cancelar</button>
        <button class="btn btn-primary" @click="handleSave" :disabled="saving || store.measures.length === 0">
          <span v-if="saving" class="spinner-xs"></span>
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
    </header>

    <!-- Main Content Grid -->
    <main class="configurator-content" :class="{ 'is-loading': saving || cubeStore.metaLoading }">
      <!-- Loading Overlay -->
      <div v-if="saving || cubeStore.metaLoading" class="panel-overlay">
        <div class="spinner"></div>
        <span>{{ saving ? 'Guardando configuración...' : 'Cargando metadatos...' }}</span>
      </div>
      <!-- Left Panel: Data Source -->
      <aside class="panel panel-source">
        <header class="panel-header">
          <h3>Origen de Datos</h3>
        </header>
        <div class="panel-body">
          <div class="cube-selector">
            <label>Cubo Principal</label>
            <select :value="store.selectedCube" @change="store.setCube($event.target.value)" class="form-select">
              <option v-for="cube in availableCubes" :key="cube.name" :value="cube.name">
                {{ cube.title || cube.name }}
              </option>
            </select>
          </div>

          <div v-if="store.selectedCube" class="source-lists">
            <!-- Measures -->
            <div class="source-section">
              <div class="section-header">
                <h4>Métricas</h4>
                <div class="search-box">
                  <input type="text" v-model="measureSearch" placeholder="Buscar métrica..." />
                </div>
              </div>
              <draggable
                class="field-list"
                :list="currentMeasures"
                :group="{ name: 'measures', pull: 'clone', put: false }"
                :sort="false"
                item-key="fullName"
                :clone="m => ({ ...m })"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: m }">
                  <div class="field-item">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon measure">#</span>
                      <span class="field-label" :title="m.fullName">{{ m.title }}</span>
                    </div>
                  </div>
                </template>
              </draggable>
              <div v-if="currentMeasures.length === 0" class="no-results">
                No se encontraron métricas
              </div>
            </div>

            <!-- Dimensions -->
            <div class="source-section">
              <div class="section-header">
                <h4>Análisis</h4>
                <div class="search-box">
                  <input type="text" v-model="dimensionSearch" placeholder="Buscar dimensión..." />
                </div>
              </div>
              <draggable
                class="field-list"
                :list="currentDimensions"
                :group="{ name: 'dimensions', pull: 'clone', put: false }"
                :sort="false"
                item-key="fullName"
                :clone="d => ({ ...d })"
              >
                <template #item="{ element: d }">
                  <div class="field-item">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon dimension">A</span>
                      <span class="field-label" :title="d.fullName">{{ d.title }}</span>
                    </div>
                  </div>
                </template>
              </draggable>
              <div v-if="currentDimensions.length === 0" class="no-results">
                No se encontraron dimensiones
              </div>
            </div>
          </div>

          <div v-else-if="cubeStore.metaLoading" class="loading-state">
            <div class="spinner-sm"></div>
            <span>Cargando metadatos...</span>
          </div>

          <div v-else class="empty-state">
            <p>Seleccione un cubo para ver los campos disponibles.</p>
          </div>
        </div>
      </aside>

      <!-- Center Panel: Configuration -->
      <section class="panel panel-config" :class="{ 'collapsed': configCollapsed }">
        <header class="panel-header">
          <div class="header-left-group">
            <button class="toggle-btn" @click="toggleConfig">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"/><polyline v-if="!configCollapsed" points="12 19 5 12 12 5"/><polyline v-else points="12 5 19 12 12 19"/>
              </svg>
            </button>
            <h3 v-if="!configCollapsed">Configuración</h3>
          </div>
          <div v-if="!configCollapsed" class="chart-type-selector">
            <select :value="store.chartType" @change="store.setChartType($event.target.value)" class="form-select select-sm">
              <option value="bar">Barras</option>
              <option value="line">Líneas</option>
              <option value="pie">Circular</option>
              <option value="gauge">Indicador</option>
              <option value="radar">Radar</option>
            </select>
          </div>
        </header>
        <div v-if="!configCollapsed" class="panel-body">
          <div class="config-sections">
            <!-- Measures (Series) -->
            <div class="config-section">
              <div class="section-label">
                <span>Series</span>
                <small>(Métricas)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.measures"
                :group="{ name: 'measures', put: (to, from, element) => !store.measures.some(m => m.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: m }">
                  <div class="field-item active-field">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon measure">#</span>
                      <span class="field-label">{{ m.alias || m.title }}</span>
                    </div>
                    <div class="field-actions">
                      <button class="action-btn" @click="openConfig('measures', m)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                        </svg>
                      </button>
                      <button class="remove-btn" @click="store.removeMeasure(m.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.measures.length === 0" class="drop-placeholder">
                    Arrastre métricas aquí
                  </div>
                </template>
              </draggable>
            </div>

            <!-- Dimensions (Análisis) -->
            <div class="config-section">
              <div class="section-label">
                <span>Análisis</span>
                <small>(Dimensiones)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.dimensions"
                :group="{ name: 'dimensions', put: (to, from, element) => !store.dimensions.some(d => d.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: d }">
                  <div class="field-item active-field">
                    <div class="field-content">
                      <div class="drag-handle">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                          <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                        </svg>
                      </div>
                      <span class="field-icon dimension">A</span>
                      <span class="field-label">{{ d.alias || d.title }}</span>
                    </div>
                    <div class="field-actions">
                      <button class="action-btn" @click="openConfig('dimensions', d)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                        </svg>
                      </button>
                      <button class="remove-btn" @click="store.removeDimension(d.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.dimensions.length === 0" class="drop-placeholder">
                    Arrastre dimensiones aquí
                  </div>
                </template>
              </draggable>
            </div>

            <!-- Quick Filters -->
            <div class="config-section">
              <div class="section-label">
                <span>Filtros Rápidos</span>
                <small>(Dimensiones)</small>
              </div>
              <draggable
                class="drop-zone"
                v-model="store.filters"
                :group="{ name: 'dimensions', pull: false, put: (to, from, element) => !store.filters.some(f => f.fullName === element.fullName) }"
                item-key="fullName"
                :animation="200"
                :component-data="{ name: 'list', tag: 'div' }"
              >
                <template #item="{ element: f }">
                  <div class="field-item active-field filter-field-config">
                    <div class="filter-main">
                      <div class="field-content">
                        <span class="field-icon dimension">F</span>
                        <span class="field-label">{{ f.alias || f.title }}</span>
                      </div>
                      <button class="remove-btn" @click="store.removeFilter(f.fullName)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                    <div class="filter-settings">
                      <select 
                        :value="f.operator || 'equals'" 
                        @change="store.updateFilter(f.fullName, { operator: $event.target.value })"
                        class="form-select select-xs"
                      >
                        <option value="equals">Es igual a</option>
                        <option value="notEquals">No es igual a</option>
                        <option value="contains">Contiene</option>
                        <option value="set">Está definido</option>
                      </select>
                      <input 
                        type="text" 
                        :value="(f.values || []).join(', ')"
                        @change="store.updateFilter(f.fullName, { values: $event.target.value.split(',').map(v => v.trim()) })"
                        placeholder="Valores..."
                        class="form-control input-xs"
                      />
                    </div>
                  </div>
                </template>
                <template #footer>
                  <div v-if="store.filters.length === 0" class="drop-placeholder">
                    Arrastre dimensiones para filtrar
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </div>
      </section>

      <!-- Right Panel: Preview -->
      <section class="panel panel-preview">
        <header class="panel-header">
          <h3>Vista Previa</h3>
        </header>
        <div class="panel-body">
          <div class="preview-container card">
            <template v-if="store.measures.length > 0">
              <EChartWrapper
                :chartType="store.chartType"
                :data="data"
                :loading="loading"
                :error="error"
                :widget="currentWidget"
              />
            </template>
            <div v-else class="empty-state">
              <div class="empty-icon">📊</div>
              <h3>Sin vista previa</h3>
              <p>Configure métricas y dimensiones para generar el gráfico.</p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Field Config Modal -->
    <div v-if="activeConfigField" class="modal-backdrop" @click.self="closeConfig">
      <div class="modal-content field-config-modal">
        <header class="modal-header">
          <h3>Configurar {{ activeConfigField.type === 'measures' ? 'Métrica' : 'Dimensión' }}</h3>
          <button class="close-btn" @click="closeConfig">&times;</button>
        </header>
        <div class="modal-body">
          <div class="form-group">
            <label>Nombre Visible (Alias)</label>
            <input 
              type="text" 
              v-model="activeConfigField.field.alias" 
              :placeholder="activeConfigField.field.title"
              class="form-control"
            />
          </div>
          
          <div v-if="activeConfigField.type === 'measures'" class="form-group">
            <label>Formato</label>
            <select v-model="activeConfigField.field.format" class="form-select">
              <option :value="undefined">Predeterminado</option>
              <option value="number">Número</option>
              <option value="currency">Moneda</option>
              <option value="percent">Porcentaje</option>
            </select>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" @click="closeConfig">Cancelar</button>
          <button class="btn btn-primary" @click="updateFieldConfig">Aplicar</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import draggable from 'vuedraggable'
import { useVisualizationConfiguratorStore } from '@/stores/visualizationConfigurator'
import { useUIStore } from '@/stores/ui'
import { useDashboardStore } from '@/stores/dashboard'
import { useCubeStore } from '@/stores/cubejs'
import { useCubeQuery } from '@/composables/useCubeQuery'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const router = useRouter()
const route = useRoute()
const store = useVisualizationConfiguratorStore()
const uiStore = useUIStore()
const dashboardStore = useDashboardStore()
const cubeStore = useCubeStore()

// Search states
const measureSearch = ref('')
const dimensionSearch = ref('')
const saving = ref(false)
const configCollapsed = ref(false)
const activeConfigField = ref(null) // { type: 'measure'|'dimension', field: Object }

const toggleConfig = () => {
  configCollapsed.value = !configCollapsed.value
}

// Computed widget for useCubeQuery and persistence
const currentWidget = computed(() => ({
  id: store.widgetId,
  title: store.title,
  chartType: store.chartType,
  cubeQuery: {
    measures: store.measures.map(m => ({ 
      key: m.fullName, 
      label: m.alias || m.title,
      format: m.format
    })),
    dimensions: store.dimensions.map(d => ({ 
      key: d.fullName, 
      label: d.alias || d.title 
    })),
    filters: store.filters.map(f => ({
      member: f.fullName,
      operator: f.operator || 'equals',
      values: f.values || []
    })),
    limit: 100
  },
  chartOptions: store.chartOptions,
  useMockData: false
}))

// ... (fetchData and watchers)

const openConfig = (type, field) => {
  activeConfigField.value = { type, field: { ...field } }
}

const closeConfig = () => {
  activeConfigField.value = null
}

const updateFieldConfig = () => {
  if (!activeConfigField.value) return
  
  const { type, field } = activeConfigField.value
  if (type === 'measure') {
    store.updateMeasure(field.fullName, { alias: field.alias, format: field.format })
  } else {
    store.updateDimension(field.fullName, { alias: field.alias })
  }
  closeConfig()
}

const { data, loading, error, fetchData } = useCubeQuery(currentWidget)

// Re-fetch data when query configuration changes
watch([() => store.measures, () => store.dimensions, () => store.selectedCube], () => {
  if (store.measures.length > 0) {
    fetchData()
  }
}, { deep: true })

// Data source computed properties
const availableCubes = computed(() => cubeStore.cubes)

const currentMeasures = computed(() => {
  if (!store.selectedCube) return []
  const measures = cubeStore.getMeasuresForCube(store.selectedCube)
  return measures
    .map(m => ({
      ...m,
      fullName: m.name.includes('.') ? m.name : `${store.selectedCube}.${m.name}`,
      cubeName: store.selectedCube
    }))
    .filter(m => 
      m.title.toLowerCase().includes(measureSearch.value.toLowerCase()) ||
      m.fullName.toLowerCase().includes(measureSearch.value.toLowerCase())
    )
})

const currentDimensions = computed(() => {
  if (!store.selectedCube) return []
  const dimensions = cubeStore.getDimensionsForCube(store.selectedCube)
  return dimensions
    .map(d => ({
      ...d,
      fullName: d.name.includes('.') ? d.name : `${store.selectedCube}.${d.name}`,
      cubeName: store.selectedCube
    }))
    .filter(d => 
      d.title.toLowerCase().includes(dimensionSearch.value.toLowerCase()) ||
      d.fullName.toLowerCase().includes(dimensionSearch.value.toLowerCase())
    )
})

onMounted(async () => {
  const dashboardId = route.params.dashboardId
  const widgetId = route.params.widgetId
  
  // Ensure metadata is loaded
  if (!cubeStore.meta) {
    await cubeStore.loadConfigFromBackend()
    await cubeStore.loadMeta()
  }

  if (dashboardId) {
    store.setDashboardId(dashboardId)
    
    // Load dashboards if they aren't loaded yet
    if (dashboardStore.allDashboards.length === 0) {
      await dashboardStore.loadFromBackend()
    }
    
    const db = dashboardStore.allDashboards.find(d => d.id === dashboardId)
    if (db) {
      if (widgetId) {
        const widget = db.widgets.find(w => w.id === widgetId)
        if (widget) {
          store.setWidget(widget)
          uiStore.setBreadcrumbs(['Diseño', db.name, 'Configurar: ' + widget.title])
        } else {
          uiStore.setBreadcrumbs(['Diseño', db.name, 'Nuevo Gráfico'])
        }
      } else {
        uiStore.setBreadcrumbs(['Diseño', db.name, 'Nuevo Gráfico'])
      }
    } else {
      uiStore.setBreadcrumbs(['Diseño', 'Configurador'])
    }
  }

  // Set default cube if none selected
  if (!store.selectedCube && cubeStore.cubes.length > 0) {
    store.setCube(cubeStore.cubes[0].name)
  }
})

onUnmounted(() => {
  store.reset()
})

const handleSave = async () => {
  if (!store.dashboardId) return
  
  saving.value = true
  try {
    if (store.widgetId) {
      await dashboardStore.updateWidget(store.dashboardId, store.widgetId, currentWidget.value)
    } else {
      await dashboardStore.addWidget(store.dashboardId, currentWidget.value)
    }
    router.push(`/designer/${store.dashboardId}`)
  } catch (err) {
    console.error('Failed to save widget:', err)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  if (store.dashboardId) {
    router.push(`/designer/${store.dashboardId}`)
  } else {
    router.push('/designer')
  }
}
</script>

<style scoped>
.configurator-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--topbar-height) - 48px); /* Adjust based on layout */
  gap: 16px;
}

.configurator-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
  max-width: 400px;
}

.title-input {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.title-input:hover {
  background: #f0f0f0;
}

.title-input:focus {
  outline: none;
  background: white;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.configurator-content {
  display: grid;
  grid-template-columns: 280px 320px 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns 0.3s ease;
}

.configurator-content.is-collapsed {
  grid-template-columns: 280px 48px 1fr;
}

.panel-config.collapsed {
  width: 48px;
  padding: 0;
}

.header-left-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-btn {
  background: transparent;
  border: none;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #f0f0f0;
  color: var(--primary);
}

.filter-field {
  border-style: dotted !important;
  border-color: #94a3b8 !important;
}

.panel {
  display: flex;
  flex-direction: column;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.panel-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-preview {
  background: var(--bg); /* Subtle contrast for preview area */
  border: none;
  box-shadow: none;
}

.panel-preview .panel-header {
  background: transparent;
  border-bottom: none;
  padding-bottom: 8px;
}

.panel-preview .panel-body {
  padding: 0 0 16px 0;
  display: flex;
  flex-direction: column;
}

.preview-container {
  flex: 1;
  background: var(--card-bg);
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
  height: 100%;
  gap: 12px;
}

.empty-icon {
  font-size: 40px;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.empty-state p {
  font-size: 14px;
  max-width: 240px;
  line-height: 1.5;
}

/* Source Panel Styles */
.cube-selector {
  margin-bottom: 20px;
}

.cube-selector label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.source-lists {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.source-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.search-box input {
  width: 100%;
  padding: 6px 10px;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.1);
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
  user-select: none;
}

.field-item:hover {
  border-color: var(--primary);
  background: #f0f7ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.field-content {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  opacity: 0.3;
  cursor: grab;
  flex-shrink: 0;
}

.field-item:hover .drag-handle {
  opacity: 0.7;
}

.field-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.field-icon.measure {
  background: #e1f5fe;
  color: #0288d1;
}

.field-icon.dimension {
  background: #e8f5e9;
  color: #2e7d32;
}

.field-label {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-results {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  padding: 12px;
  font-style: italic;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 12px;
  color: var(--text-secondary);
}
.spinner-sm {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(0,0,0,0.1);
  border-left-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-xs {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-left-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
  margin-right: 8px;
  vertical-align: middle;
}

.panel-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 100;
  backdrop-filter: blur(2px);
  color: var(--text);
  font-weight: 500;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0,0,0,0.1);
  border-left-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Transitions */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.list-move {
  transition: transform 0.3s ease;
}

@keyframes spin {
/* Config Panel Styles */
.config-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.section-label span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.section-label small {
  font-size: 11px;
  color: var(--text-secondary);
}

.drop-zone {
  min-height: 50px;
  background: #fcfcfc;
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s;
}

.drop-zone:empty {
  display: none; /* Hide if truly empty to let footer show */
}

.drop-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.6;
}

.active-field {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  cursor: default !important;
}

.active-field .drag-handle {
  cursor: grab;
}

.remove-btn {
  background: transparent;
  border: none;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.4;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
  opacity: 1;
}

/* Field Actions & Modal */
.field-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: none;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.4;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f0f0f0;
  color: var(--primary);
  opacity: 1;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.field-config-modal {
  width: 100%;
  max-width: 400px;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 24px;
  line-height: 1;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fafafa;
}

.filter-field-config {
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 8px !important;
  padding: 10px !important;
}

.filter-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-settings {
  display: flex;
  gap: 6px;
}

.select-xs {
  padding: 2px 4px !important;
  font-size: 11px !important;
  height: 24px !important;
  width: 100px !important;
}

.input-xs {
  padding: 2px 8px !important;
  font-size: 11px !important;
  height: 24px !important;
  flex: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
