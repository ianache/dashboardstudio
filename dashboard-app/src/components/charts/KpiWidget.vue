<template>
  <div class="kpi-widget" :class="trendClass" :style="accentStyle">
    <!-- Loading -->
    <div v-if="loading" class="kpi-loading">
      <div class="kpi-spinner"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="kpi-error">{{ error }}</div>

    <!-- Content -->
    <template v-else>
      <!-- Icon + label row -->
      <div class="kpi-top">
        <div v-if="kpiIcon" class="kpi-icon-wrap">
          <span v-if="isMaterialIcon" class="material-symbols-outlined kpi-material-icon">{{ kpiIcon }}</span>
          <span v-else class="kpi-emoji-icon">{{ kpiIcon }}</span>
        </div>
        <span class="kpi-label">{{ label }}</span>
      </div>

      <!-- Main value -->
      <div class="kpi-value">{{ formattedValue }}</div>

      <!-- Trend row -->
      <div v-if="kpiOptions.showComparison !== false && hasTrend" class="kpi-trend-row">
        <span class="kpi-trend-badge" :class="trendBadgeClass">
          <svg v-if="trendDirection === 'up'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="18 15 12 9 6 15"/>
          </svg>
          <svg v-else-if="trendDirection === 'down'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          <span>{{ trendPercent }}</span>
        </span>
        <span class="kpi-comparison-label">{{ kpiOptions.comparisonLabel || 'vs período anterior' }}</span>
      </div>

      <!-- Comparison value -->
      <div v-if="kpiOptions.showComparison !== false && comparisonValue != null" class="kpi-comparison-value">
        {{ formattedComparison }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useCurrencyStore } from '@/stores/currencies'

const props = defineProps({
  data:     { type: Array,  default: () => [] },
  loading:  { type: Boolean, default: false },
  error:    { type: String,  default: null },
  widget:   { type: Object,  required: true }
})

const currencyStore = useCurrencyStore()

const kpiOptions = computed(() => props.widget.kpiOptions || {})
const measure    = computed(() => props.widget.cubeQuery?.measures?.[0] || {})

const row = computed(() => props.data?.[0] || null)

const currentValue    = computed(() => row.value ? Number(row.value.value)  : null)
const comparisonValue = computed(() => row.value && row.value.value2 != null ? Number(row.value.value2) : null)
const label           = computed(() => row.value?.label || props.widget.title || 'KPI')

const kpiIcon = computed(() => kpiOptions.value.icon || '')

const isMaterialIcon = computed(() => {
  const icon = kpiIcon.value
  if (!icon) return false
  // Material symbols use snake_case with letters/underscores only
  return /^[a-z][a-z0-9_]*$/.test(icon)
})

function formatValue(val) {
  if (val == null || isNaN(val)) return '—'
  const fmt = measure.value.format || 'numero'
  if (fmt === 'porcentaje') return val.toFixed(1) + '%'
  if (fmt === 'moneda') {
    const cur = measure.value.currencyId
      ? currencyStore.currencies?.find(c => c.id === measure.value.currencyId)
      : null
    const symbol = cur ? cur.symbol : '$'
    if (Math.abs(val) >= 1_000_000) return symbol + (val / 1_000_000).toFixed(2) + 'M'
    if (Math.abs(val) >= 1_000)     return symbol + (val / 1_000).toFixed(1) + 'K'
    return symbol + val.toLocaleString('es', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  }
  // numero
  if (Math.abs(val) >= 1_000_000) return (val / 1_000_000).toFixed(2) + 'M'
  if (Math.abs(val) >= 1_000)     return (val / 1_000).toFixed(1) + 'K'
  return val.toLocaleString('es', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const formattedValue      = computed(() => formatValue(currentValue.value))
const formattedComparison = computed(() => comparisonValue.value != null ? formatValue(comparisonValue.value) : null)

const trendRaw = computed(() => {
  if (currentValue.value == null || comparisonValue.value == null || comparisonValue.value === 0) return null
  return ((currentValue.value - comparisonValue.value) / Math.abs(comparisonValue.value)) * 100
})

const hasTrend        = computed(() => trendRaw.value != null)
const trendDirection  = computed(() => {
  if (trendRaw.value == null) return 'neutral'
  return trendRaw.value >= 0 ? 'up' : 'down'
})
const trendPercent    = computed(() => {
  if (trendRaw.value == null) return ''
  return Math.abs(trendRaw.value).toFixed(1) + '%'
})

// Good = up when not inverted, down when inverted
const isGood = computed(() => {
  if (!hasTrend.value) return null
  const invert = kpiOptions.value.invertTrend
  return invert ? trendDirection.value === 'down' : trendDirection.value === 'up'
})

const trendClass      = computed(() => {
  if (!hasTrend.value) return ''
  return isGood.value ? 'kpi--trend-good' : 'kpi--trend-bad'
})

const trendBadgeClass = computed(() => {
  if (!hasTrend.value) return ''
  return isGood.value ? 'kpi-badge--good' : 'kpi-badge--bad'
})

const accentStyle = computed(() => {
  const color = kpiOptions.value.accentColor
  if (color) return { '--kpi-accent': color }
  return {}
})
</script>

<style scoped>
.kpi-widget {
  --kpi-accent: var(--primary, #1890ff);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  height: 100%;
  padding: 16px 20px;
  gap: 6px;
  overflow: hidden;
  border-top: 3px solid var(--kpi-accent);
}

/* Loading */
.kpi-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.kpi-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border, #e8e8e8);
  border-top-color: var(--kpi-accent);
  border-radius: 50%;
  animation: kpi-spin 0.7s linear infinite;
}
@keyframes kpi-spin { to { transform: rotate(360deg); } }

.kpi-error {
  font-size: 12px;
  color: var(--error, #f5222d);
}

/* Top row */
.kpi-top {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.kpi-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--kpi-accent) 12%, transparent);
  flex-shrink: 0;
}

.kpi-material-icon {
  font-size: 18px;
  color: var(--kpi-accent);
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 20;
}
.kpi-emoji-icon {
  font-size: 16px;
  line-height: 1;
}

.kpi-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, #8c8c8c);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Main value */
.kpi-value {
  font-size: clamp(24px, 4cqw, 40px);
  font-weight: 700;
  color: var(--text, #1a1a2e);
  line-height: 1.1;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Trend */
.kpi-trend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.kpi-trend-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 7px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
}

.kpi-badge--good {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
.kpi-badge--bad {
  background: #fff2f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}

.kpi-comparison-label {
  font-size: 11px;
  color: var(--text-secondary, #8c8c8c);
}

.kpi-comparison-value {
  font-size: 12px;
  color: var(--text-secondary, #8c8c8c);
}
</style>
