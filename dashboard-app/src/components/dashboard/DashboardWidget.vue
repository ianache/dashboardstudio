<template>
  <div
    ref="widgetRef"
    class="dashboard-widget"
    :class="{ 'is-design': isDesignMode, 'is-selected': isSelected, 'is-maximized': isMaximized }"
    @click.stop="isDesignMode && $emit('select')"
  >
    <!-- Widget Header -->
    <div class="widget-header" :class="{ 'drag-handle': isDesignMode }"
         @mousedown="isDesignMode && $emit('drag-start', $event)">
      <div class="widget-title">
        <span class="chart-type-icon">{{ chartTypeIcon }}</span>
        <span>{{ widget.title || 'Sin título' }}</span>
      </div>
      <div class="widget-actions">
        <button
          v-if="isDesignMode"
          class="widget-action-btn"
          data-tooltip="Formato del widget"
          @click.stop="$emit('layout')"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
          </svg>
        </button>
        <button
          v-if="isDesignMode"
          class="widget-action-btn"
          data-tooltip="Configurar gráfico"
          @click.stop="$emit('configure')"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06-.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
        <button
          class="widget-action-btn"
          :data-tooltip="isMaximized ? 'Minimizar' : 'Maximizar'"
          @click.stop="$emit('toggle-maximize')"
        >
          <svg v-if="!isMaximized" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 3 21 3 21 9"/>
            <polyline points="9 21 3 21 3 15"/>
            <line x1="21" y1="3" x2="14" y2="10"/>
            <line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 14 10 14 10 20"/>
            <polyline points="20 10 14 10 14 4"/>
            <line x1="14" y1="10" x2="21" y2="3"/>
            <line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
        </button>
        <button
          class="widget-action-btn"
          data-tooltip="Actualizar datos"
          :class="{ 'spinning': loading }"
          @click.stop="refresh"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>
        <button
          class="widget-action-btn"
          data-tooltip="Descargar CSV"
          @click.stop="handleDownload"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>
        <button
          class="widget-action-btn"
          data-tooltip="Exportar PNG"
          @click.stop="handleExportPNG"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </button>
        <button
          v-if="isDesignMode"
          class="widget-action-btn widget-action-danger"
          data-tooltip="Eliminar widget"
          @click.stop="$emit('remove')"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Chart Body -->
    <div class="widget-body" :class="{ 'widget-body--table': widget.chartType === 'table', 'widget-body--kpi': widget.chartType === 'kpi' }">
      <DataTableWidget
        v-if="widget.chartType === 'table'"
        :data="data"
        :loading="loading"
        :error="errorMsg"
        :widget="widget"
      />
      <KpiWidget
        v-else-if="widget.chartType === 'kpi'"
        :data="data"
        :loading="loading"
        :error="errorMsg"
        :widget="widget"
      />
      <EChartWrapper
        v-else
        :chart-type="widget.chartType"
        :data="data"
        :loading="loading"
        :error="errorMsg"
        :widget="widget"
        :dashboard-palette="dashboardPalette"
      />
    </div>

    <!-- Last updated -->
    <div v-if="lastUpdated && !isDesignMode" class="widget-footer">
      Actualizado: {{ formatUpdated(lastUpdated) }}
    </div>

    <!-- Design mode resize handles -->
    <template v-if="isDesignMode">
      <div class="resize-handle resize-e" @mousedown.stop="$emit('resize-start', 'e', $event)"></div>
      <div class="resize-handle resize-s" @mousedown.stop="$emit('resize-start', 's', $event)"></div>
      <div class="resize-handle resize-se" @mousedown.stop="$emit('resize-start', 'se', $event)"></div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, watch, ref } from 'vue'
import EChartWrapper from '../charts/EChartWrapper.vue'
import DataTableWidget from '../charts/DataTableWidget.vue'
import KpiWidget from '../charts/KpiWidget.vue'
import { useCubeQuery, downloadCSV } from '@/composables/useCubeQuery'
import { useCubeStore } from '@/stores/cubejs'
import html2canvas from 'html2canvas'

const props = defineProps({
  widget: { type: Object, required: true },
  isDesignMode: { type: Boolean, default: false },
  isSelected: { type: Boolean, default: false },
  isMaximized: { type: Boolean, default: false },
  dashboardFilters: { type: Array, default: () => [] },
  dashboardPalette: { type: String, default: null }
})

const emit = defineEmits(['configure', 'layout', 'remove', 'select', 'resize-start', 'drag-start', 'toggle-maximize'])

const cubeStore = useCubeStore()
const dashboardFiltersRef = computed(() => props.dashboardFilters)
const { data, loading, error: errorMsg, lastUpdated, fetchData } = useCubeQuery(props.widget, dashboardFiltersRef)

const CHART_ICONS = {
  bar: '📊', line: '📈', pie: '🥧', gauge: '🎯', radar: '🕸️', combined: '📉', table: '🗒️', kpi: '🔢'
}

const chartTypeIcon = computed(() => CHART_ICONS[props.widget.chartType] || '📊')

function refresh() {
  fetchData()
}

const widgetRef = ref(null)

async function handleExportPNG() {
  if (!widgetRef.value) return
  const el = widgetRef.value
  const actionsEl = el.querySelector('.widget-actions')
  
  if (actionsEl) actionsEl.style.display = 'none'
  
  try {
    const canvas = await html2canvas(el, {
      backgroundColor: '#ffffff',
      scale: 2
    })
    const dataUrl = canvas.toDataURL('image/png')
    const baseName = (props.widget.title || 'grafico').toLowerCase()
    
    // Convert to slug (no accents, replaced spaces)
    const fileName = baseName
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') + '.png'
      
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = fileName
    a.click()
  } catch (err) {
    console.error('Error exportando PNG:', err)
  } finally {
    if (actionsEl) actionsEl.style.display = ''
  }
}

function handleDownload() {
  downloadCSV(data.value, props.widget.title || 'datos')
}

function formatUpdated(date) {
  if (!date) return ''
  return date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  // Use requestAnimationFrame to defer heavy work until after initial frame
  requestAnimationFrame(() => {
    fetchData()
  })
})

watch(() => props.widget.cubeQuery, () => fetchData(), { deep: true })
watch(() => props.widget.useMockData, () => fetchData())
watch(() => props.dashboardFilters, () => fetchData())
watch(() => cubeStore.token, (token) => { if (token) fetchData() })
</script>


<style scoped>
.dashboard-widget {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  overflow: hidden;
  height: 100%;
  position: relative;
  transition: box-shadow 0.2s, border-color 0.2s, top 0.3s ease, left 0.3s ease, width 0.3s ease, height 0.3s ease;
}
.dashboard-widget.is-design { cursor: move; }
.dashboard-widget.is-design:hover { box-shadow: 0 4px 16px rgba(24,144,255,0.15); border-color: #a0d4ff; }
.dashboard-widget.is-selected { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }

.dashboard-widget.is-maximized {
  position: fixed !important;
  top: 40px !important;
  left: 40px !important;
  right: 40px !important;
  bottom: 40px !important;
  width: auto !important;
  height: auto !important;
  z-index: 9999 !important;
  margin: 0 !important;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* Header */
.widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: #fafafa;
  flex-shrink: 0;
  min-height: 40px;
  gap: 8px;
}
.drag-handle { cursor: grab; }
.drag-handle:active { cursor: grabbing; }

.widget-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.widget-title span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chart-type-icon { font-size: 14px; flex-shrink: 0; }

.widget-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.widget-action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  position: relative;
}
.widget-action-btn:hover { background: var(--bg); color: var(--primary); }
.widget-action-btn.spinning svg { animation: spin 0.8s linear infinite; }
.widget-action-danger:hover { color: var(--error); background: #fff2f0; }

/* Body */
.widget-body {
  flex: 1;
  min-height: 0;
  padding: 8px;
  overflow: hidden;
}
.widget-body--table { padding: 0; }
.widget-body--kpi { padding: 0; }

/* Footer */
.widget-footer {
  padding: 2px 12px;
  font-size: 11px;
  color: var(--text-secondary);
  background: #fafafa;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

/* Resize handles */
.resize-handle {
  position: absolute;
  background: var(--primary);
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 2px;
}
.dashboard-widget:hover .resize-handle { opacity: 0.6; }
.resize-handle:hover { opacity: 1 !important; cursor: se-resize; }

.resize-e {
  right: 0; top: 50%; transform: translateY(-50%);
  width: 6px; height: 40px; cursor: e-resize;
  border-radius: 3px 0 0 3px;
}
.resize-s {
  bottom: 0; left: 50%; transform: translateX(-50%);
  height: 6px; width: 40px; cursor: s-resize;
  border-radius: 3px 3px 0 0;
}
.resize-se {
  right: 0; bottom: 0;
  width: 14px; height: 14px; cursor: se-resize;
  border-radius: 6px 0 0 0;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
