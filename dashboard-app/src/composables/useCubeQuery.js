import { ref, computed } from 'vue'
import { useCubeStore } from '@/stores/cubejs'

// Mock data generators per chart type
function generateMockData(widget) {
  const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
  const categories = ['Electrónica', 'Ropa', 'Hogar', 'Deportes', 'Libros']
  const regions = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']

  switch (widget.chartType) {
    case 'bar':
    case 'line':
    case 'combined':
      return months.slice(0, 8).map(m => ({
        label: m,
        value: Math.floor(Math.random() * 8000) + 2000,
        value2: Math.floor(Math.random() * 5000) + 1000
      }))

    case 'pie':
      return categories.map(c => ({
        label: c,
        value: Math.floor(Math.random() * 500) + 100
      }))

    case 'gauge':
      return [{ label: 'Avance', value: Math.floor(Math.random() * 40) + 50 }]

    case 'radar':
      return regions.map(r => ({
        label: r,
        value: Math.floor(Math.random() * 80) + 20
      }))

    default:
      return []
  }
}

export function normalizeMember(key) {
  const parts = key.split('.')
  if (parts.length === 3 && parts[0] === parts[1]) return `${parts[1]}.${parts[2]}`
  return key
}

export function buildCubeFilter(filterDef, value) {
  if (value === null || value === undefined || value === '') return []
  const dimension = normalizeMember(filterDef.dimension)
  const { type } = filterDef
  if (type === 'string' || type === 'boolean') {
    // value es un array de strings seleccionados; array vacío = todos = sin filtro
    if (!Array.isArray(value) || value.length === 0) return []
    return [{ member: dimension, operator: 'equals', values: value.map(String) }]
  }
  if (type === 'time') {
    const vals = [value.from, value.to].filter(Boolean)
    if (!vals.length) return []
    return [{ member: dimension, operator: 'inDateRange', values: vals }]
  }
  if (type === 'number') {
    const filters = []
    if (value.min !== '' && value.min != null)
      filters.push({ member: dimension, operator: 'gte', values: [String(value.min)] })
    if (value.max !== '' && value.max != null)
      filters.push({ member: dimension, operator: 'lte', values: [String(value.max)] })
    return filters
  }
  return []
}

export function useCubeQuery(widget, dashboardFilters) {
  const cubeStore = useCubeStore()
  const data = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)

  async function fetchData() {
    loading.value = true
    error.value = null

    try {
      if (widget.useMockData || !cubeStore.token || !cubeStore.apiUrl) {
        // Use mock data
        await new Promise(r => setTimeout(r, 300 + Math.random() * 400))
        data.value = generateMockData(widget)
      } else {
        // Build CubeJS query from widget config
        const query = buildCubeQuery(widget)
        const result = await cubeStore.executeQuery(query)
        data.value = transformCubeResult(result, widget)
      }
      lastUpdated.value = new Date()
    } catch (err) {
      error.value = err.message
      // Fallback to mock data on error
      data.value = generateMockData(widget)
    } finally {
      loading.value = false
    }
  }

  function buildCubeQuery(widget) {
    const { cubeQuery } = widget
    const measures = cubeQuery.measures.map(m => m.key).filter(k => k)
    const dimensions = cubeQuery.dimensions.map(d => d.key).filter(k => k)

    if (measures.length === 0) {
      throw new Error('Debes configurar al menos una medida con clave válida.')
    }

    const widgetFilters = (cubeQuery.filters || []).filter(f => f.member)
    const extraFilters = dashboardFilters?.value || []

    const query = {
      measures,
      dimensions,
      limit: cubeQuery.limit || 100,
      filters: [...widgetFilters, ...extraFilters]
    }

    if (cubeQuery.timeDimension) {
      query.timeDimensions = [{
        dimension: cubeQuery.timeDimension.dimension,
        granularity: cubeQuery.timeDimension.granularity || 'month'
      }]
    }

    return query
  }

  function transformCubeResult(result, widget) {
    const tableData = result.tablePivot ? result.tablePivot() : result.loadResponse?.results?.[0]?.data || []
    const { cubeQuery } = widget

    const dimKey = cubeQuery.dimensions[0]?.key ||
      (cubeQuery.timeDimension ? `${cubeQuery.timeDimension.dimension}.${cubeQuery.timeDimension.granularity}` : null)

    return tableData.map(row => {
      const label = dimKey ? row[dimKey] : 'Total'
      const value = cubeQuery.measures[0] ? Number(row[cubeQuery.measures[0].key]) || 0 : 0
      const value2 = cubeQuery.measures[1] ? Number(row[cubeQuery.measures[1].key]) || 0 : 0
      return { label, value, value2, raw: row }
    })
  }

  return { data, loading, error, lastUpdated, fetchData }
}

export function downloadCSV(data, filename) {
  if (!data || data.length === 0) return

  const headers = Object.keys(data[0]).filter(k => k !== 'raw')
  const csvContent = [
    headers.join(','),
    ...data.map(row =>
      headers.map(h => {
        const val = row[h]
        if (val === null || val === undefined) return ''
        const str = String(val)
        return str.includes(',') || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"`
          : str
      }).join(',')
    )
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename.replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
