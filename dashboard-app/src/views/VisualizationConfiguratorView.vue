<template>
  <div class="configurator-view">
    <!-- Header -->
    <header class="configurator-header">
      <div class="header-left">
        <button class="btn btn-secondary btn-sm" @click="handleCancel">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Volver
        </button>
        <div class="header-title">
          <span class="db-title-text">{{ store.title }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleCancel">Cancelar</button>
        <button class="btn btn-primary" @click="handleSave">Guardar</button>
      </div>
    </header>

    <!-- Main Content Grid -->
    <main class="configurator-content">
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
      <section class="panel panel-config">
        <header class="panel-header">
          <h3>Configuración</h3>
        </header>
        <div class="panel-body">
          <div class="empty-state">
            <p>Arrastre campos aquí para configurar el gráfico.</p>
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
            <div class="empty-state">
              <div class="empty-icon">📊</div>
              <h3>Sin vista previa</h3>
              <p>Configure métricas y dimensiones para generar el gráfico.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import draggable from 'vuedraggable'
import { useVisualizationConfiguratorStore } from '@/stores/visualizationConfigurator'
import { useUIStore } from '@/stores/ui'
import { useDashboardStore } from '@/stores/dashboard'
import { useCubeStore } from '@/stores/cubejs'

const router = useRouter()
const route = useRoute()
const store = useVisualizationConfiguratorStore()
const uiStore = useUIStore()
const dashboardStore = useDashboardStore()
const cubeStore = useCubeStore()

// Search states
const measureSearch = ref('')
const dimensionSearch = ref('')

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

const handleSave = () => {
  // Logic will be implemented in future plans
  router.push(`/designer/${store.dashboardId}`)
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
  min-height: 0; /* Important for grid item scrolling */
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
