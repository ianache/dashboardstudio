<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal card layout-modal">
      <div class="modal-header">
        <h3>Formato del widget</h3>
        <button class="btn-icon" @click="$emit('close')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- Title -->
        <div class="form-group">
          <label class="form-label">Título del widget</label>
          <input v-model="form.title" class="form-input" placeholder="Título" />
        </div>

        <hr class="divider" />

        <!-- Grid margins -->
        <div class="form-group">
          <label class="form-label">Márgenes del gráfico (px)</label>
          <div class="margins-grid">
            <div class="margin-field">
              <label>Superior</label>
              <input v-model.number="form.gridTop"   type="number" min="0" class="form-input margin-input" />
            </div>
            <div class="margin-field">
              <label>Inferior</label>
              <input v-model.number="form.gridBottom" type="number" min="0" class="form-input margin-input" />
            </div>
            <div class="margin-field">
              <label>Izquierdo</label>
              <input v-model.number="form.gridLeft"   type="number" min="0" class="form-input margin-input" />
            </div>
            <div class="margin-field">
              <label>Derecho</label>
              <input v-model.number="form.gridRight"  type="number" min="0" class="form-input margin-input" />
            </div>
          </div>
        </div>

        <hr class="divider" />

        <!-- Legend -->
        <div class="form-group">
          <label class="form-label">
            <input type="checkbox" v-model="form.legendShow" style="margin-right:6px" />
            Mostrar leyenda
          </label>
        </div>
        <div v-if="form.legendShow" class="form-group">
          <label class="form-label">Posición de la leyenda</label>
          <div class="legend-positions">
            <label v-for="opt in legendOptions" :key="opt.value" class="legend-option">
              <input type="radio" v-model="form.legendPosition" :value="opt.value" />
              {{ opt.label }}
            </label>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">Cancelar</button>
        <button class="btn btn-primary" @click="save">Guardar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const props = defineProps({
  widget: { type: Object, required: true }
})
const emit = defineEmits(['close', 'save'])

const legendOptions = [
  { value: 'top',    label: 'Arriba' },
  { value: 'bottom', label: 'Abajo' },
  { value: 'left',   label: 'Izquierda' },
  { value: 'right',  label: 'Derecha' }
]

// Read current values from widget.chartOptions
const co = props.widget.chartOptions || {}
const grid = co.grid || {}
const leg  = co.legend || {}

// Infer current legend position from stored ECharts legend object
function inferPosition(l) {
  if (l.left === 0 || l.left === '0') return 'left'
  if (l.right === 0 || l.right === '0') return 'right'
  if (l.top === 0 || l.top === '0') return 'top'
  return 'bottom'
}

const form = reactive({
  title:          props.widget.title || '',
  gridTop:        grid.top    ?? 10,
  gridBottom:     grid.bottom ?? 40,
  gridLeft:       grid.left   ?? 40,
  gridRight:      grid.right  ?? 16,
  legendShow:     leg.show !== false,
  legendPosition: inferPosition(leg)
})

function legendConfig(pos) {
  const base = { show: true, type: 'scroll' }
  if (pos === 'top')    return { ...base, orient: 'horizontal', top: 0,    bottom: 'auto', left: 'center', right: 'auto' }
  if (pos === 'bottom') return { ...base, orient: 'horizontal', bottom: 0, top: 'auto',   left: 'center', right: 'auto' }
  if (pos === 'left')   return { ...base, orient: 'vertical',   left: 0,   right: 'auto', top: 'middle',  bottom: 'auto' }
  /* right */           return { ...base, orient: 'vertical',   right: 0,  left: 'auto',  top: 'middle',  bottom: 'auto' }
}

function save() {
  const chartOptions = { ...(props.widget.chartOptions || {}) }

  chartOptions.grid = {
    ...(chartOptions.grid || {}),
    top: form.gridTop,
    bottom: form.gridBottom,
    left: form.gridLeft,
    right: form.gridRight,
    containLabel: true
  }

  chartOptions.legend = form.legendShow
    ? legendConfig(form.legendPosition)
    : { show: false }

  emit('save', { title: form.title, chartOptions })
}
</script>

<style scoped>
.layout-modal { width: 420px; max-width: 95vw; }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

.form-label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }

.divider { border: none; border-top: 1px solid var(--border); margin: 0; }

.margins-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.margin-field label { font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px; }
.margin-input { width: 100%; }

.legend-positions { display: flex; gap: 16px; flex-wrap: wrap; }
.legend-option { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
</style>
