<template>
  <div class="filter-bar">
    <!-- Filtros configurados -->
    <template v-if="filters.length > 0 || isDesignMode">
    <div v-for="filter in filters" :key="filter.id" class="filter-chip">
      <span class="filter-label">{{ filter.label }}</span>

      <!-- String / Boolean → multi-select con checkboxes -->
      <template v-if="filter.type === 'string' || filter.type === 'boolean'">
        <div class="multiselect-wrap" :ref="el => setRef(filter.id, el)">
          <button
            class="multiselect-trigger"
            :class="{ active: openDropdown === filter.id }"
            @click="toggleDropdown(filter.id)"
          >
            <span class="multiselect-summary">{{ getSummary(filter) }}</span>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>

          <div v-if="openDropdown === filter.id" class="multiselect-dropdown">
            <div v-if="loadingValues[filter.id]" class="multiselect-loading">Cargando...</div>
            <template v-else>
              <!-- Seleccionar todos -->
              <label class="multiselect-option multiselect-all">
                <input
                  type="checkbox"
                  :checked="isAllSelected(filter)"
                  @change="toggleAll(filter)"
                />
                <span>Todos</span>
              </label>
              <div class="multiselect-divider"></div>
              <!-- Opciones individuales -->
              <label
                v-for="v in dimensionValues[filter.id]"
                :key="v"
                class="multiselect-option"
              >
                <input
                  type="checkbox"
                  :checked="isSelected(filter, v)"
                  @change="toggleValue(filter, v)"
                />
                <span>{{ v }}</span>
              </label>
              <div v-if="!dimensionValues[filter.id]?.length" class="multiselect-empty">
                Sin valores disponibles
              </div>
            </template>
          </div>
        </div>
      </template>

      <!-- Time → rango de fechas -->
      <template v-else-if="filter.type === 'time'">
        <input
          type="date"
          class="form-input filter-control filter-date"
          :value="(modelValue[filter.id] || {}).from || ''"
          @change="onDateChange(filter.id, 'from', $event.target.value)"
        />
        <span class="filter-date-sep">—</span>
        <input
          type="date"
          class="form-input filter-control filter-date"
          :value="(modelValue[filter.id] || {}).to || ''"
          @change="onDateChange(filter.id, 'to', $event.target.value)"
        />
      </template>

      <!-- Number → rango numérico -->
      <template v-else-if="filter.type === 'number'">
        <input
          type="number"
          class="form-input filter-control filter-number"
          placeholder="Mín"
          :value="(modelValue[filter.id] || {}).min ?? ''"
          @change="onNumberChange(filter.id, 'min', $event.target.value)"
        />
        <span class="filter-date-sep">—</span>
        <input
          type="number"
          class="form-input filter-control filter-number"
          placeholder="Máx"
          :value="(modelValue[filter.id] || {}).max ?? ''"
          @change="onNumberChange(filter.id, 'max', $event.target.value)"
        />
      </template>

      <!-- Botón eliminar (solo diseño) -->
      <button v-if="isDesignMode" class="filter-remove-btn" @click="removeFilter(filter.id)" title="Eliminar filtro">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- Panel para añadir filtro (solo diseño) -->
    <div v-if="isDesignMode" class="filter-add-area">
      <template v-if="!showAddPanel">
        <button class="btn btn-secondary btn-sm" @click="showAddPanel = true">
          + Añadir filtro
        </button>
      </template>
      <template v-else>
        <div class="filter-add-panel">
          <select v-model="newDimension" class="form-input form-select" style="min-width:200px">
            <option value="">Seleccionar dimensión...</option>
            <optgroup
              v-for="cube in groupedDimensions"
              :key="cube.name"
              :label="cube.name"
            >
              <option
                v-for="dim in cube.dimensions"
                :key="dim.fullName"
                :value="dim.fullName"
              >{{ dim.fullName }} ({{ dim.type }})</option>
            </optgroup>
          </select>
          <input
            v-model="newLabel"
            type="text"
            class="form-input"
            placeholder="Etiqueta del filtro"
            style="width:140px"
          />
          <button class="btn btn-primary btn-sm" @click="confirmAdd" :disabled="!newDimension">
            Añadir
          </button>
          <button class="btn btn-secondary btn-sm" @click="cancelAdd">
            Cancelar
          </button>
        </div>
      </template>
    </div>
    </template>

    <!-- Refresh control -->
    <div class="refresh-control" ref="refreshControlRef">
      <button
        class="refresh-trigger"
        :class="{ 'is-auto': refreshInterval !== 'manual' }"
        @click.stop="refreshOpen = !refreshOpen"
        title="Frecuencia de actualización"
      >
        <svg
          class="refresh-icon"
          :class="{ spinning: refreshInterval !== 'manual' }"
          width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2.2"
        >
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        <span class="refresh-label-text">{{ refreshLabel }}</span>
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      <div v-if="refreshOpen" class="refresh-dropdown" @click.stop>
        <div
          v-for="preset in REFRESH_PRESETS"
          :key="preset.value"
          class="refresh-option"
          :class="{ selected: isPresetSelected(preset.value) }"
          @click="selectRefresh(preset.value)"
        >
          <span>{{ preset.label }}</span>
          <svg v-if="isPresetSelected(preset.value)" class="refresh-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- Custom interval modal -->
    <Teleport to="body">
      <div v-if="showCustomModal" class="custom-refresh-overlay" @click.self="showCustomModal = false">
        <div class="custom-refresh-box">
          <header class="crb-header">
            <h4>Intervalo personalizado</h4>
            <button class="crb-close" @click="showCustomModal = false">&times;</button>
          </header>
          <div class="crb-body">
            <label class="crb-label">Duración entre actualizaciones</label>
            <div class="crb-input-row">
              <input
                type="number"
                v-model.number="customMinutes"
                min="0.5"
                step="0.5"
                class="form-input crb-input"
                @keyup.enter="confirmCustom"
                autofocus
              />
              <span class="crb-unit">minutos</span>
            </div>
            <p class="crb-hint">Mínimo 0.5 minutos (30 segundos)</p>
          </div>
          <footer class="crb-footer">
            <button class="btn btn-secondary btn-sm" @click="showCustomModal = false">Cancelar</button>
            <button class="btn btn-primary btn-sm" @click="confirmCustom" :disabled="!customMinutes || customMinutes < 0.5">Aplicar</button>
          </footer>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import { useCubeStore } from '@/stores/cubejs'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps({
  dashboardId: { type: String, required: true },
  filters: { type: Array, default: () => [] },
  modelValue: { type: Object, default: () => ({}) },
  isDesignMode: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const cubeStore = useCubeStore()
const dashboardStore = useDashboardStore()

const dimensionValues = ref({})
const loadingValues = ref({})
const openDropdown = ref(null)

// refs de los wrappers para detectar click fuera
const wrapperRefs = ref({})
function setRef(id, el) { wrapperRefs.value[id] = el }

// ── Auto-refresh ──────────────────────────────────────────────
const REFRESH_PRESETS = [
  { value: 'manual', label: 'Manual' },
  { value: 5000,     label: '5s' },
  { value: 10000,    label: '10s' },
  { value: 30000,    label: '30s' },
  { value: 'custom', label: 'Personalizado' },
]
const refreshInterval = ref('manual')   // 'manual' | ms (number)
const refreshOpen = ref(false)
const showCustomModal = ref(false)
const customMinutes = ref(1)
const refreshControlRef = ref(null)
let refreshTimer = null

const refreshLabel = computed(() => {
  const v = refreshInterval.value
  if (v === 'manual') return 'Manual'
  if (v === 5000)  return '5s'
  if (v === 10000) return '10s'
  if (v === 30000) return '30s'
  const mins = v / 60000
  return Number.isInteger(mins) ? `${mins} min` : `${mins.toFixed(1)} min`
})

function isPresetSelected(presetValue) {
  const v = refreshInterval.value
  if (presetValue === 'custom') {
    return typeof v === 'number' && ![5000, 10000, 30000].includes(v)
  }
  return v === presetValue
}

function selectRefresh(value) {
  refreshOpen.value = false
  if (value === 'custom') { showCustomModal.value = true; return }
  applyRefreshMs(value)
}

function applyRefreshMs(ms) {
  stopTimer()
  refreshInterval.value = ms
  if (ms !== 'manual') {
    refreshTimer = setInterval(() => emit('refresh'), ms)
  }
}

function confirmCustom() {
  if (!customMinutes.value || customMinutes.value < 0.5) return
  showCustomModal.value = false
  applyRefreshMs(Math.round(customMinutes.value * 60000))
}

function stopTimer() {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}
// ─────────────────────────────────────────────────────────────

// Panel de añadir filtro
const showAddPanel = ref(false)
const newDimension = ref('')
const newLabel = ref('')

const groupedDimensions = computed(() => {
  const map = {}
  cubeStore.allDimensions.forEach(d => {
    if (!map[d.cubeName]) map[d.cubeName] = { name: d.cubeName, dimensions: [] }
    map[d.cubeName].dimensions.push(d)
  })
  return Object.values(map)
})

// Cargar valores para comboboxes
async function loadValues(filter) {
  if (filter.type !== 'string' && filter.type !== 'boolean') return
  if (dimensionValues.value[filter.id] || loadingValues.value[filter.id]) return
  if (!cubeStore.token) return

  loadingValues.value[filter.id] = true
  try {
    const values = await cubeStore.loadDimensionValues(filter.dimension)
    dimensionValues.value[filter.id] = values
  } catch {
    dimensionValues.value[filter.id] = []
  } finally {
    loadingValues.value[filter.id] = false
  }
}

onMounted(() => {
  props.filters.forEach(loadValues)
  document.addEventListener('mousedown', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onClickOutside)
  stopTimer()
})

watch(() => props.filters.map(f => f.id).join(','), () => {
  props.filters.forEach(loadValues)
})

// Cerrar dropdown al hacer click fuera
function onClickOutside(e) {
  if (openDropdown.value) {
    const el = wrapperRefs.value[openDropdown.value]
    if (el && !el.contains(e.target)) openDropdown.value = null
  }
  if (refreshOpen.value) {
    const rc = refreshControlRef.value
    if (rc && !rc.contains(e.target)) refreshOpen.value = false
  }
}

function toggleDropdown(filterId) {
  openDropdown.value = openDropdown.value === filterId ? null : filterId
}

// Multi-select helpers
function getSelected(filterId) {
  const v = props.modelValue[filterId]
  return Array.isArray(v) ? v : []
}

function isAllSelected(filter) {
  const selected = getSelected(filter.id)
  return selected.length === 0
}

function isSelected(filter, value) {
  return getSelected(filter.id).includes(value)
}

function getSummary(filter) {
  const selected = getSelected(filter.id)
  if (selected.length === 0) return 'Todos'
  if (selected.length === 1) return selected[0]
  return `${selected.length} seleccionados`
}

function toggleAll(filter) {
  // Si ya está "todos", no hace nada; si hay selección específica, la limpia
  emit('update:modelValue', { ...props.modelValue, [filter.id]: [] })
}

function toggleValue(filter, value) {
  const current = getSelected(filter.id)
  const next = current.includes(value)
    ? current.filter(v => v !== value)
    : [...current, value]
  emit('update:modelValue', { ...props.modelValue, [filter.id]: next })
}

// Date handlers
function onDateChange(filterId, key, value) {
  const current = props.modelValue[filterId] || {}
  emit('update:modelValue', { ...props.modelValue, [filterId]: { ...current, [key]: value || '' } })
}

// Number handlers
function onNumberChange(filterId, key, value) {
  const current = props.modelValue[filterId] || {}
  const parsed = value !== '' ? Number(value) : ''
  emit('update:modelValue', { ...props.modelValue, [filterId]: { ...current, [key]: parsed } })
}

// Añadir filtro
function confirmAdd() {
  if (!newDimension.value) return
  const dim = cubeStore.allDimensions.find(d => d.fullName === newDimension.value)
  if (!dim) return
  const label = newLabel.value.trim() || dim.fullName.split('.').pop()
  dashboardStore.addDashboardFilter(props.dashboardId, {
    dimension: dim.fullName,
    label,
    type: dim.type
  })
  cancelAdd()
}

function cancelAdd() {
  showAddPanel.value = false
  newDimension.value = ''
  newLabel.value = ''
}

function removeFilter(filterId) {
  dashboardStore.removeDashboardFilter(props.dashboardId, filterId)
  const updated = { ...props.modelValue }
  delete updated[filterId]
  delete dimensionValues.value[filterId]
  delete loadingValues.value[filterId]
  delete wrapperRefs.value[filterId]
  emit('update:modelValue', updated)
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 10px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

/* Multi-select */
.multiselect-wrap {
  position: relative;
}

.multiselect-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
  min-width: 120px;
  transition: border-color 0.15s;
}
.multiselect-trigger:hover,
.multiselect-trigger.active { border-color: var(--primary); }
.multiselect-trigger svg { margin-left: auto; color: var(--text-secondary); flex-shrink: 0; }

.multiselect-summary {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.multiselect-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 180px;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  z-index: 200;
  padding: 4px 0;
}

.multiselect-loading,
.multiselect-empty {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.multiselect-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  user-select: none;
  transition: background 0.1s;
}
.multiselect-option:hover { background: var(--bg); }
.multiselect-option input[type="checkbox"] { cursor: pointer; accent-color: var(--primary); }

.multiselect-all { font-weight: 600; }

.multiselect-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

/* Date / Number */
.filter-control {
  height: 28px;
  padding: 2px 8px;
  font-size: 13px;
  min-width: 120px;
  width: auto;
}

.filter-date { min-width: 130px; width: 130px; }
.filter-number { min-width: 80px; width: 80px; }

.filter-date-sep {
  font-size: 12px;
  color: var(--text-secondary);
}

.filter-remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  flex-shrink: 0;
  transition: all 0.15s;
}
.filter-remove-btn:hover { background: #fff2f0; color: var(--error); }

.filter-add-area { }

.filter-add-panel {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Refresh control ── */
.refresh-control {
  position: relative;
  margin-left: auto;
  flex-shrink: 0;
}

.refresh-trigger {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 9px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.refresh-trigger:hover { border-color: var(--primary); color: var(--primary); }
.refresh-trigger.is-auto { border-color: var(--primary); color: var(--primary); background: rgba(24,144,255,0.05); }

.refresh-icon { flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.refresh-icon.spinning { animation: spin 2s linear infinite; }

.refresh-label-text { font-weight: 500; }

.refresh-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 160px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  z-index: 300;
  padding: 4px 0;
}

.refresh-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 12px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  transition: background 0.1s;
}
.refresh-option:hover { background: #f5f7fa; }
.refresh-option.selected { color: var(--primary); font-weight: 500; background: rgba(24,144,255,0.05); }
.refresh-check { color: var(--primary); flex-shrink: 0; }

/* ── Custom interval modal ── */
.custom-refresh-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.custom-refresh-box {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  width: 320px;
  max-width: 95vw;
  overflow: hidden;
}

.crb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--border);
}
.crb-header h4 { margin: 0; font-size: 15px; font-weight: 600; }
.crb-close {
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0 2px;
}
.crb-close:hover { color: var(--text); }

.crb-body { padding: 16px; }
.crb-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px; }

.crb-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.crb-input { width: 100px; }
.crb-unit { font-size: 13px; color: var(--text-secondary); }
.crb-hint { font-size: 12px; color: var(--text-secondary); margin: 8px 0 0; }

.crb-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
}
</style>
