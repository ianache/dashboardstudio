<template>
  <div class="echart-wrapper">
    <div v-if="loading" class="chart-loading">
      <div class="spinner"></div>
    </div>
    <div v-else-if="error" class="chart-error">
      <span class="chart-error-icon">⚠️</span>
      <span>{{ error }}</span>
    </div>
    <v-chart
      v-else
      :option="chartOption"
      :autoresize="true"
      style="width: 100%; height: 100%;"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useColorPaletteStore } from '@/stores/colorPalettes'

const paletteStore = useColorPaletteStore()

const props = defineProps({
  chartType: { type: String, default: 'bar' },
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  widget: { type: Object, required: true },
  dashboardPalette: { type: String, default: null }
})

const COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
  '#13c2c2', '#fa8c16', '#eb2f96', '#2f54eb', '#a0d911'
]

const activePaletteId = computed(() => {
  const wp = props.widget.colorPalette
  if (wp === 'none') return null
  return wp || props.dashboardPalette || paletteStore.defaultPaletteId || null
})

const activeColors = computed(() => {
  if (!activePaletteId.value) return COLORS
  return paletteStore.getPaletteById(activePaletteId.value)?.colors ?? COLORS
})

function seriesColor(index, measureColor) {
  if (activePaletteId.value) return activeColors.value[index % activeColors.value.length]
  return measureColor || COLORS[index % COLORS.length]
}

const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) {
    return buildEmptyOption()
  }

  const baseOption = buildBaseOption()
  const customOptions = props.widget.chartOptions || {}

  // Inject palette and merge
  const option = deepMerge({ color: activeColors.value }, baseOption)
  return deepMerge(option, customOptions)
})

function buildBaseOption() {
  switch (props.chartType) {
    case 'bar':    return buildBarOption()
    case 'line':   return buildLineOption()
    case 'pie':    return buildPieOption()
    case 'gauge':  return buildGaugeOption()
    case 'radar':  return buildRadarOption()
    case 'combined': return buildCombinedOption()
    default:       return buildBarOption()
  }
}

function buildSeriesItem(name, data, color, seriesType) {
  if (seriesType === 'bar') {
    return { name, type: 'bar', data, itemStyle: { color, borderRadius: [4, 4, 0, 0] }, barMaxWidth: 60 }
  }
  return {
    name, type: 'line', data, smooth: true,
    lineStyle: { color, width: 2 },
    itemStyle: { color },
    areaStyle: seriesType === 'area' ? { color, opacity: 0.15 } : undefined
  }
}

function formatValue(value, measure) {
  if (value == null) return ''
  const decimals = measure?.decimalPlaces ?? 2
  const fmt = measure?.format
  if (fmt === 'currency') return new Intl.NumberFormat('es', { style: 'currency', currency: 'USD', minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value)
  if (fmt === 'percent') return `${(value * 100).toFixed(decimals)}%`
  if (fmt === 'number') return new Intl.NumberFormat('es', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value)
  return value
}

function buildBarOption() {
  const labels = props.data.map(d => d.label)
  const measures = props.widget.cubeQuery?.measures || []
  const rawData = [props.data.map(d => d.value), props.data.map(d => d.value2 || 0)]

  const series = measures.slice(0, 2).map((m, i) =>
    buildSeriesItem(m.label || `Serie ${i + 1}`, rawData[i], seriesColor(i, m.color), m.seriesType || 'bar')
  )

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const label = params[0]?.axisValueLabel || params[0]?.name || ''
        const lines = params.map((p, i) => `${p.marker}${p.seriesName}: <b>${formatValue(p.value, measures[i])}</b>`)
        return [label, ...lines].join('<br/>')
      }
    },
    legend: { bottom: 0, type: 'scroll' },
    grid: { top: 10, left: 40, right: 16, bottom: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { rotate: labels.length > 8 ? 30 : 0, overflow: 'truncate', width: 80 }
    },
    yAxis: { type: 'value' },
    series
  }
}

function buildLineOption() {
  const labels = props.data.map(d => d.label)
  const values = props.data.map(d => d.value)
  const measures = props.widget.cubeQuery?.measures || []
  const seriesName = measures[0]?.label || 'Valor'
  const color = seriesColor(0, measures[0]?.color)

  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { top: 10, left: 40, right: 16, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: labels, boundaryGap: false },
    yAxis: { type: 'value' },
    series: [{
      name: seriesName,
      type: 'line',
      data: values,
      smooth: true,
      lineStyle: { color, width: 2 },
      itemStyle: { color },
      areaStyle: { color, opacity: 0.1 }
    }]
  }
}

function buildPieOption() {
  const opts = props.widget.pieOptions || {}
  const showValue   = opts.showValue   ?? false
  const showPercent = opts.showPercent ?? true
  const showTotal   = opts.showTotal   ?? false

  const total = props.data.reduce((s, d) => s + (d.value || 0), 0)
  const measures = props.widget.cubeQuery?.measures || []
  const metricLabel = measures[0]?.label || 'Total'

  const seriesData = props.data.map((d, i) => ({
    name: d.label,
    value: d.value,
    itemStyle: { color: activeColors.value[i % activeColors.value.length] }
  }))

  let labelParts = ['{b}']
  if (showValue && showPercent) labelParts.push('{c} ({d}%)')
  else if (showValue)           labelParts.push('{c}')
  else if (showPercent)         labelParts.push('{d}%')
  const labelFormatter = labelParts.join('\n')
  const showLabel = showValue || showPercent

  const graphic = showTotal ? [{
    type: 'text',
    left: 'center',
    top: 'center',
    style: {
      text: `${metricLabel}\n${total.toLocaleString('es', { maximumFractionDigits: 2 })}`,
      textAlign: 'center',
      fill: '#333',
      fontSize: 13,
      fontWeight: 'bold',
      lineHeight: 20
    }
  }] : []

  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    graphic,
    series: [{
      type: 'pie',
      radius: showTotal ? ['40%', '68%'] : ['35%', '65%'],
      center: ['50%', '45%'],
      data: seriesData,
      label: { show: showLabel, formatter: labelFormatter, fontSize: 12 },
      labelLine: { show: showLabel },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } }
    }]
  }
}

function buildGaugeOption() {
  const value = props.data[0]?.value ?? 0
  const measures = props.widget.cubeQuery?.measures || []
  const seriesName = measures[0]?.label || 'Valor'

  return {
    tooltip: { formatter: '{b}: {c}%' },
    series: [{
      name: seriesName,
      type: 'gauge',
      center: ['50%', '60%'],
      radius: '80%',
      min: 0,
      max: 100,
      axisLine: {
        lineStyle: {
          width: 16,
          color: [[0.3, '#f5222d'], [0.7, '#faad14'], [1, '#52c41a']]
        }
      },
      pointer: { itemStyle: { color: 'auto' } },
      axisTick: { distance: -20, length: 8, lineStyle: { color: '#fff', width: 2 } },
      splitLine: { distance: -24, length: 16, lineStyle: { color: '#fff', width: 4 } },
      axisLabel: { color: 'inherit', distance: 28, fontSize: 11 },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: 'inherit',
        fontSize: 20,
        fontWeight: 'bold',
        offsetCenter: [0, '70%']
      },
      data: [{ value, name: seriesName }]
    }]
  }
}

function buildRadarOption() {
  const indicators = props.data.map(d => ({ name: d.label, max: 100 }))
  const values = props.data.map(d => d.value)
  const measures = props.widget.cubeQuery?.measures || []
  const seriesName = measures[0]?.label || 'Valor'
  const color = seriesColor(0, measures[0]?.color)

  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, data: [seriesName] },
    radar: {
      indicator: indicators,
      radius: '60%',
      center: ['50%', '50%']
    },
    series: [{
      name: seriesName,
      type: 'radar',
      data: [{
        value: values,
        name: seriesName,
        areaStyle: { color, opacity: 0.2 },
        lineStyle: { color, width: 2 },
        itemStyle: { color }
      }]
    }]
  }
}

function buildCombinedOption() {
  const labels = props.data.map(d => d.label)
  const measures = props.widget.cubeQuery?.measures || []
  const m0 = measures[0] || {}
  const m1 = measures[1] || {}
  const name0 = m0.label || 'Serie 1'
  const name1 = m1.label || 'Serie 2'
  const color0 = seriesColor(0, m0.color)
  const color1 = seriesColor(1, m1.color)

  const s0 = { ...buildSeriesItem(name0, props.data.map(d => d.value), color0, m0.seriesType || 'bar'), yAxisIndex: 0 }
  const s1 = { ...buildSeriesItem(name1, props.data.map(d => d.value2 || 0), color1, m1.seriesType || 'line'), yAxisIndex: 1 }

  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { bottom: 0, data: [name0, name1] },
    grid: { top: 10, left: 40, right: 40, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: [
      { type: 'value', name: name0, position: 'left' },
      { type: 'value', name: name1, position: 'right' }
    ],
    series: [s0, s1]
  }
}

function buildEmptyOption() {
  return {
    title: {
      text: 'Sin datos',
      left: 'center',
      top: 'center',
      textStyle: { color: '#c0c0c0', fontSize: 14 }
    }
  }
}

/**
 * Safer deepMerge with recursion limit and basic circular reference guard
 */
function deepMerge(target, source, depth = 0) {
  if (depth > 10) return target // Limit depth to avoid stack overflow
  if (!source || typeof source !== 'object') return target
  if (Array.isArray(source)) return source // Don't merge arrays, replace them
  
  const result = { ...target }
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      // Circular reference guard (simple check)
      if (source[key] === source) continue
      result[key] = deepMerge(result[key] || {}, source[key], depth + 1)
    } else {
      result[key] = source[key]
    }
  }
  return result
}
</script>

<style scoped>
.echart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ff4d4f;
  font-size: 13px;
  text-align: center;
  padding: 16px;
}
.chart-error-icon { font-size: 24px; }
</style>
