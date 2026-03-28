<template>
  <div v-if="filters.length > 0 || isDesignMode" class="filter-bar">
    <!-- Filtros configurados -->
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

const emit = defineEmits(['update:modelValue'])

const cubeStore = useCubeStore()
const dashboardStore = useDashboardStore()

const dimensionValues = ref({})
const loadingValues = ref({})
const openDropdown = ref(null)

// refs de los wrappers para detectar click fuera
const wrapperRefs = ref({})
function setRef(id, el) { wrapperRefs.value[id] = el }

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
})

watch(() => props.filters, (filters) => {
  filters.forEach(loadValues)
}, { deep: true })

// Cerrar dropdown al hacer click fuera
function onClickOutside(e) {
  if (!openDropdown.value) return
  const el = wrapperRefs.value[openDropdown.value]
  if (el && !el.contains(e.target)) openDropdown.value = null
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

.filter-add-area { margin-left: auto; }

.filter-add-panel {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
