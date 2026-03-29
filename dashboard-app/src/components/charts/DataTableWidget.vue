<template>
  <div class="dt-wrapper">
    <!-- Loading -->
    <div v-if="loading" class="dt-center">
      <div class="spinner"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="dt-center dt-error">
      <span class="dt-error-icon">⚠️</span>
      <span>{{ error }}</span>
    </div>

    <!-- Empty -->
    <div v-else-if="rows.length === 0" class="dt-center dt-empty">
      Sin datos disponibles
    </div>

    <!-- Table + footer -->
    <template v-else>
      <div class="dt-scroll-area">
        <table class="dt-table">
          <thead>
            <tr>
              <th
                v-for="col in columns"
                :key="col.key"
                class="dt-th"
                :class="{ 'dt-th-active': sortKey === col.key, 'dt-th-num': col.isNumeric }"
                @click="toggleSort(col.key)"
              >
                <span class="dt-th-inner">
                  <span class="dt-th-label">{{ col.label }}</span>
                  <svg v-if="sortKey === col.key && sortDir === 'asc'"
                    class="dt-sort-icon dt-sort-on" width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 4l8 16H4z"/>
                  </svg>
                  <svg v-else-if="sortKey === col.key && sortDir === 'desc'"
                    class="dt-sort-icon dt-sort-on" width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 20l8-16H4z"/>
                  </svg>
                  <svg v-else class="dt-sort-icon dt-sort-off"
                    width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M8 9l4-4 4 4M16 15l-4 4-4-4"/>
                  </svg>
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in pagedRows" :key="i" class="dt-row">
              <td
                v-for="col in columns"
                :key="col.key"
                class="dt-td"
                :class="{ 'dt-td-num': col.isNumeric }"
              >
                {{ formatCell(row[col.key], col.isNumeric) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div class="dt-footer">
        <span class="dt-range-info">
          {{ rangeStart }}–{{ rangeEnd }} de {{ sortedRows.length }} filas
        </span>
        <div class="dt-controls">
          <label class="dt-ctrl-label">Filas por página:</label>
          <select v-model="pageSize" class="dt-page-select" @change="currentPage = 1">
            <option v-for="s in PAGE_SIZES" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="dt-nav">
          <button class="dt-nav-btn" :disabled="currentPage === 1"    @click="currentPage = 1"          title="Primera">«</button>
          <button class="dt-nav-btn" :disabled="currentPage === 1"    @click="currentPage--"            title="Anterior">‹</button>
          <span class="dt-page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button class="dt-nav-btn" :disabled="currentPage >= totalPages" @click="currentPage++"       title="Siguiente">›</button>
          <button class="dt-nav-btn" :disabled="currentPage >= totalPages" @click="currentPage = totalPages" title="Última">»</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: null },
  widget:  { type: Object,  required: true }
})

const PAGE_SIZES = [20, 25, 50, 100]
const pageSize   = ref(20)
const currentPage = ref(1)
const sortKey    = ref(null)
const sortDir    = ref('asc')

// ── Rows ─────────────────────────────────────────────────────
const rows = computed(() => props.data.map(d => {
  if (d.raw && Object.keys(d.raw).length > 0) return d.raw
  // Fallback: build from label/value fields
  const dims = props.widget.cubeQuery?.dimensions || []
  const meas = props.widget.cubeQuery?.measures   || []
  const row  = {}
  if (dims[0]?.key) row[dims[0].key] = d.label
  if (meas[0]?.key) row[meas[0].key] = d.value
  if (meas[1]?.key) row[meas[1].key] = d.value2
  return Object.keys(row).length ? row : { label: d.label, value: d.value }
}))

// ── Columns ───────────────────────────────────────────────────
const columns = computed(() => {
  const dims = (props.widget.cubeQuery?.dimensions || []).filter(d => d.key)
  const meas = (props.widget.cubeQuery?.measures   || []).filter(m => m.key)
  const td   = props.widget.cubeQuery?.timeDimension

  if (dims.length || meas.length || td) {
    const cols = []
    if (td?.dimension) {
      const key = `${td.dimension}.${td.granularity || 'month'}`
      cols.push({ key, label: td.dimension.split('.').pop(), isNumeric: false })
    }
    dims.forEach(d => cols.push({
      key: d.key,
      label: d.label || d.key.split('.').pop(),
      isNumeric: false
    }))
    meas.forEach(m => cols.push({
      key: m.key,
      label: m.label || m.key.split('.').pop(),
      isNumeric: true
    }))
    return cols
  }

  // Fallback: infer from first row
  const first = rows.value[0]
  if (!first) return []
  return Object.keys(first).map(k => ({
    key: k,
    label: k.includes('.') ? k.split('.').pop() : k,
    isNumeric: first[k] !== null && first[k] !== '' && !isNaN(Number(first[k]))
  }))
})

// ── Sort ──────────────────────────────────────────────────────
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  currentPage.value = 1
}

const sortedRows = computed(() => {
  if (!sortKey.value) return rows.value
  const key = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...rows.value].sort((a, b) => {
    const av = a[key], bv = b[key]
    if (av === bv) return 0
    if (av === null || av === undefined) return 1
    if (bv === null || bv === undefined) return -1
    const an = Number(av), bn = Number(bv)
    if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir
    return String(av).localeCompare(String(bv), 'es') * dir
  })
})

// ── Pagination ────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)))
const rangeStart = computed(() => (currentPage.value - 1) * pageSize.value + 1)
const rangeEnd   = computed(() => Math.min(currentPage.value * pageSize.value, sortedRows.value.length))

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

// ── Formatting ────────────────────────────────────────────────
function formatCell(val, isNumeric) {
  if (val === null || val === undefined) return '—'
  if (isNumeric) {
    const n = Number(val)
    if (!isNaN(n)) return n.toLocaleString('es', { maximumFractionDigits: 2 })
  }
  return String(val)
}
</script>

<style scoped>
.dt-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  font-size: 13px;
}

/* Center states */
.dt-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-secondary);
}
.dt-error { color: #ff4d4f; }
.dt-error-icon { font-size: 22px; }
.dt-empty { font-size: 13px; }

/* Scrollable area */
.dt-scroll-area {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

/* Table */
.dt-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.dt-th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #fafafa;
  border-bottom: 2px solid var(--border);
  padding: 0;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
.dt-th:hover { background: var(--primary-light); }
.dt-th-active { background: var(--primary-light); color: var(--primary); }

.dt-th-inner {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  width: 100%;
}
.dt-th-label { flex: 1; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.3px; }
.dt-th-num .dt-th-inner { justify-content: flex-end; }
.dt-th-num .dt-th-label { text-align: right; }

.dt-sort-icon { flex-shrink: 0; }
.dt-sort-off { opacity: 0.3; }
.dt-sort-on { color: var(--primary); }

.dt-row:nth-child(even) { background: #fafafa; }
.dt-row:hover { background: var(--primary-light); }

.dt-td {
  padding: 7px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dt-td-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}

/* Footer */
.dt-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 12px;
  border-top: 1px solid var(--border);
  background: #fafafa;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.dt-range-info { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
.dt-controls { display: flex; align-items: center; gap: 6px; }
.dt-ctrl-label { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.dt-page-select {
  font-size: 12px;
  padding: 3px 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}
.dt-nav { display: flex; align-items: center; gap: 2px; }
.dt-nav-btn {
  min-width: 26px; height: 26px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  color: var(--text);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.dt-nav-btn:hover:not(:disabled) { background: var(--primary-light); border-color: var(--primary); color: var(--primary); }
.dt-nav-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.dt-page-info { font-size: 12px; color: var(--text-secondary); padding: 0 6px; white-space: nowrap; }
</style>
