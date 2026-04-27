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

        <!-- ── KPI-specific section ─────────────────────────── -->
        <template v-if="isKpi">
          <hr class="divider" />

          <div class="form-group">
            <label class="form-label">Ícono (Material Symbol o emoji)</label>
            <div class="icon-picker-row">
              <div class="icon-preview" :class="{ empty: !form.kpi.icon }">
                <span v-if="form.kpi.icon && isMaterialIcon(form.kpi.icon)"
                      class="material-symbols-outlined kpi-preview-icon">{{ form.kpi.icon }}</span>
                <span v-else-if="form.kpi.icon" class="kpi-emoji-preview">{{ form.kpi.icon }}</span>
                <span v-else class="material-symbols-outlined kpi-preview-icon" style="opacity:0.25">category</span>
              </div>
              <input
                v-model="form.kpi.icon"
                type="text"
                class="form-input"
                placeholder="Ej: trending_up, paid, 💰"
              />
            </div>
            <span class="form-hint">Nombre de un Material Symbol (snake_case) o cualquier emoji</span>
          </div>

          <div class="form-group">
            <label class="form-label">Color de acento</label>
            <div class="color-row">
              <input v-model="form.kpi.accentColor" type="color" class="color-swatch-picker" title="Seleccionar color" />
              <input v-model="form.kpi.accentColor" type="text" class="form-input" placeholder="#1890ff" />
              <button class="btn-icon-sm" title="Restablecer" @click="form.kpi.accentColor = ''">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Etiqueta de comparación</label>
            <input v-model="form.kpi.comparisonLabel" type="text" class="form-input" placeholder="vs período anterior" />
          </div>

          <div class="form-group">
            <label class="form-label">Opciones de tendencia</label>
            <div class="toggle-list">
              <label class="toggle-row" @click.prevent="form.kpi.showComparison = !form.kpi.showComparison">
                <span class="toggle-track" :class="{ on: form.kpi.showComparison }">
                  <span class="toggle-thumb"></span>
                </span>
                <span class="toggle-label">Mostrar tendencia</span>
                <span class="toggle-hint">Muestra el badge ↑↓ y la comparación con el período anterior</span>
              </label>
              <label class="toggle-row" @click.prevent="form.kpi.invertTrend = !form.kpi.invertTrend">
                <span class="toggle-track" :class="{ on: form.kpi.invertTrend }">
                  <span class="toggle-thumb"></span>
                </span>
                <span class="toggle-label">Invertir sentido (↑ = malo)</span>
                <span class="toggle-hint">Útil para costos, devoluciones u otras métricas donde crecer es negativo</span>
              </label>
            </div>
          </div>
        </template>

        <!-- ── Gauge section ──────────────────────────────── -->
        <template v-else-if="isGauge">
          <hr class="divider" />

          <div class="form-group">
            <label class="form-label">Variante</label>
            <div class="gauge-variant-grid">
              <div v-for="v in gaugeVariants" :key="v.value"
                   class="gauge-variant-card" :class="{ selected: form.gauge.variant === v.value }"
                   @click="form.gauge.variant = v.value">
                <span class="gv-icon">{{ v.icon }}</span>
                <span class="gv-label">{{ v.label }}</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Escala</label>
            <div class="gauge-scale-row">
              <div class="gauge-scale-field">
                <label>Mínimo</label>
                <input v-model.number="form.gauge.min" type="number" class="form-input" />
              </div>
              <div class="gauge-scale-field">
                <label>Máximo</label>
                <input v-model.number="form.gauge.max" type="number" class="form-input" />
              </div>
              <div class="gauge-scale-field">
                <label>Unidad</label>
                <input v-model="form.gauge.unit" type="text" class="form-input" placeholder="%" maxlength="10" />
              </div>
              <div class="gauge-scale-field">
                <label>Grosor arco</label>
                <input v-model.number="form.gauge.arcWidth" type="number" min="4" max="40" class="form-input" />
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">
              <input type="checkbox" v-model="form.gauge.showZones" style="margin-right:6px" />
              Zonas de color
            </label>
            <div v-if="form.gauge.showZones" class="zones-list">
              <div v-for="(zone, i) in form.gauge.zones" :key="i" class="zone-row">
                <input v-model="form.gauge.zones[i].color" type="color" class="color-swatch-picker" />
                <label class="zone-label">Hasta {{ Math.round(zone.threshold * form.gauge.max) }} {{ form.gauge.unit }}</label>
                <input v-model.number="form.gauge.zones[i].threshold" type="range" min="0.01" max="1" step="0.01"
                       class="zone-slider" />
                <span class="zone-pct">{{ Math.round(zone.threshold * 100) }}%</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Opciones</label>
            <div class="toggle-list">
              <label class="toggle-row" @click.prevent="form.gauge.showPointer = !form.gauge.showPointer">
                <span class="toggle-track" :class="{ on: form.gauge.showPointer }"><span class="toggle-thumb"></span></span>
                <span class="toggle-label">Mostrar aguja</span>
              </label>
              <label class="toggle-row" @click.prevent="form.gauge.showTicks = !form.gauge.showTicks">
                <span class="toggle-track" :class="{ on: form.gauge.showTicks }"><span class="toggle-thumb"></span></span>
                <span class="toggle-label">Mostrar marcas y etiquetas de escala</span>
              </label>
            </div>
          </div>
        </template>

        <!-- ── ECharts layout section (hidden for KPI and gauge) ── -->
        <template v-else>
          <hr class="divider" />

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
        </template>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">Cancelar</button>
        <button class="btn btn-primary" @click="save">Guardar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  widget: { type: Object, required: true }
})
const emit = defineEmits(['close', 'save'])

const isKpi   = computed(() => props.widget.chartType === 'kpi')
const isGauge = computed(() => props.widget.chartType === 'gauge')

const gaugeVariants = [
  { value: 'semicircle', label: 'Semicírculo', icon: '🌡️' },
  { value: 'circle',     label: 'Círculo',     icon: '⭕' },
  { value: 'progress',   label: 'Progreso',    icon: '🔵' },
  { value: 'speed',      label: 'Velocímetro', icon: '🏎️' },
]

const legendOptions = [
  { value: 'top',    label: 'Arriba' },
  { value: 'bottom', label: 'Abajo' },
  { value: 'left',   label: 'Izquierda' },
  { value: 'right',  label: 'Derecha' }
]

const co  = props.widget.chartOptions || {}
const grid = co.grid || {}
const leg  = co.legend || {}
const kpi  = props.widget.kpiOptions || {}
const go   = props.widget.gaugeOptions || {}

function inferPosition(l) {
  if (l.left === 0 || l.left === '0') return 'left'
  if (l.right === 0 || l.right === '0') return 'right'
  if (l.top === 0 || l.top === '0') return 'top'
  return 'bottom'
}

function isMaterialIcon(icon) {
  return /^[a-z][a-z0-9_]*$/.test(icon)
}

const form = reactive({
  title:          props.widget.title || '',
  // ECharts layout fields
  gridTop:        grid.top    ?? 10,
  gridBottom:     grid.bottom ?? 40,
  gridLeft:       grid.left   ?? 40,
  gridRight:      grid.right  ?? 16,
  legendShow:     leg.show !== false,
  legendPosition: inferPosition(leg),
  // KPI fields
  kpi: {
    icon:            kpi.icon            ?? '',
    accentColor:     kpi.accentColor     ?? '',
    comparisonLabel: kpi.comparisonLabel ?? 'vs período anterior',
    showComparison:  kpi.showComparison  !== false,
    invertTrend:     kpi.invertTrend     ?? false
  },
  // Gauge fields
  gauge: {
    variant:     go.variant     || 'semicircle',
    min:         go.min         ?? 0,
    max:         go.max         ?? 100,
    unit:        go.unit        ?? '%',
    showZones:   go.showZones   !== false,
    zones:       JSON.parse(JSON.stringify(go.zones || [
      { threshold: 0.3, color: '#f5222d' },
      { threshold: 0.7, color: '#faad14' },
      { threshold: 1.0, color: '#52c41a' }
    ])),
    arcWidth:    go.arcWidth    ?? 16,
    showPointer: go.showPointer !== false,
    showTicks:   go.showTicks   !== false,
  }
})

function legendConfig(pos) {
  const base = { show: true, type: 'scroll' }
  if (pos === 'top')    return { ...base, orient: 'horizontal', top: 0,    bottom: 'auto', left: 'center', right: 'auto' }
  if (pos === 'bottom') return { ...base, orient: 'horizontal', bottom: 0, top: 'auto',   left: 'center', right: 'auto' }
  if (pos === 'left')   return { ...base, orient: 'vertical',   left: 0,   right: 'auto', top: 'middle',  bottom: 'auto' }
  /* right */           return { ...base, orient: 'vertical',   right: 0,  left: 'auto',  top: 'middle',  bottom: 'auto' }
}

function save() {
  if (isGauge.value) {
    emit('save', { title: form.title, gaugeOptions: { ...form.gauge } })
    return
  }
  if (isKpi.value) {
    emit('save', {
      title:      form.title,
      kpiOptions: { ...form.kpi }
    })
  } else {
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
}
</script>

<style scoped>
.layout-modal { width: 420px; max-width: 95vw; }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

.form-label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.form-hint  { font-size: 11px; color: var(--text-secondary); margin-top: 4px; display: block; }

.divider { border: none; border-top: 1px solid var(--border); margin: 0; }

/* ECharts layout */
.margins-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.margin-field label { font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px; }
.margin-input { width: 100%; }
.legend-positions { display: flex; gap: 16px; flex-wrap: wrap; }
.legend-option { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }

/* KPI icon picker */
.icon-picker-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.icon-preview {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1.5px solid var(--border);
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color 0.15s;
}
.icon-preview:not(.empty) { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 10%, #fff); }
.kpi-preview-icon { font-size: 20px; color: var(--primary); font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 20; }
.kpi-emoji-preview { font-size: 20px; line-height: 1; }

/* Accent color */
.color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.color-swatch-picker {
  width: 36px;
  height: 36px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  padding: 2px;
  background: #fff;
  flex-shrink: 0;
}
.btn-icon-sm {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.btn-icon-sm:hover { border-color: var(--error); color: var(--error); background: #fff2f0; }

/* Toggle switches */
.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.toggle-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.toggle-track {
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: #d9d9d9;
  flex-shrink: 0;
  position: relative;
  transition: background 0.2s;
  margin-top: 1px;
}
.toggle-track.on { background: var(--primary, #1890ff); }
.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s;
}
.toggle-track.on .toggle-thumb { transform: translateX(16px); }
.toggle-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.3;
}
.toggle-hint {
  display: block;
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
}
/* Make label a flex column for hint */
.toggle-row > span:last-child:not(.toggle-track):not(.toggle-label) { display: block; }
.toggle-row { flex-wrap: wrap; }
.toggle-label, .toggle-hint { flex-basis: calc(100% - 46px); }
.toggle-hint { flex-basis: 100%; padding-left: 46px; margin-top: -8px; }

/* Gauge variant picker */
.gauge-variant-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 4px; }
.gauge-variant-card { display: flex; flex-direction: column; align-items: center; padding: 10px 6px; border: 2px solid var(--border); border-radius: 8px; cursor: pointer; transition: all 0.15s; text-align: center; }
.gauge-variant-card:hover { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 8%, #fff); }
.gauge-variant-card.selected { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 8%, #fff); }
.gv-icon { font-size: 22px; margin-bottom: 4px; }
.gv-label { font-size: 11px; font-weight: 600; color: var(--text); }

/* Gauge scale row */
.gauge-scale-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; margin-top: 4px; }
.gauge-scale-field label { font-size: 11px; color: var(--text-secondary); display: block; margin-bottom: 3px; }

/* Zones */
.zones-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.zone-row { display: flex; align-items: center; gap: 8px; }
.zone-label { font-size: 12px; color: var(--text-secondary); white-space: nowrap; min-width: 80px; }
.zone-slider { flex: 1; }
.zone-pct { font-size: 11px; color: var(--text-secondary); width: 32px; text-align: right; }
</style>
