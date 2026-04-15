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
          <div class="empty-state">
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
import { onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVisualizationConfiguratorStore } from '@/stores/visualizationConfigurator'
import { useUIStore } from '@/stores/ui'
import { useDashboardStore } from '@/stores/dashboard'

const router = useRouter()
const route = useRoute()
const store = useVisualizationConfiguratorStore()
const uiStore = useUIStore()
const dashboardStore = useDashboardStore()

onMounted(async () => {
  const dashboardId = route.params.dashboardId
  const widgetId = route.params.widgetId
  
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
</style>
