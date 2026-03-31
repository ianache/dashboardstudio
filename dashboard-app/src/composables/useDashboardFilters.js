import { ref, computed, watch } from 'vue'
import { buildCubeFilter } from './useCubeQuery'

export function useDashboardFilters(dashboardRef) {
  const activeFilterValues = ref({})

  function getStorageKey(id) {
    return `ds_filters_${id}`
  }

  function saveFilters() {
    if (!dashboardRef.value?.id) return
    localStorage.setItem(getStorageKey(dashboardRef.value.id), JSON.stringify(activeFilterValues.value))
  }

  // Load rules or fallback dynamically
  watch(() => dashboardRef.value, (db) => {
    if (!db || !db.id) {
      activeFilterValues.value = {}
      return
    }

    try {
      const stored = localStorage.getItem(getStorageKey(db.id))
      let values = stored ? JSON.parse(stored) : {}
      
      let modified = false
      if (db.filters) {
        db.filters.forEach(f => {
          if (f.type === 'time' && (!values[f.id] || (!values[f.id].from && !values[f.id].to))) {
            const today = new Date().toISOString().split('T')[0]
            values[f.id] = { from: today, to: today }
            modified = true
          }
        })
      }
      activeFilterValues.value = values
      if (modified) saveFilters()
    } catch {
      activeFilterValues.value = {}
    }
  }, { immediate: true })

  // Trigger writes back to session browser cache
  watch(activeFilterValues, () => saveFilters(), { deep: true })

  const resolvedDashboardFilters = computed(() => {
    const schema = dashboardRef.value?.filters || []
    return schema.flatMap(f => buildCubeFilter(f, activeFilterValues.value[f.id]))
  })

  function resetFilters() {
    activeFilterValues.value = {}
    if (dashboardRef.value?.filters) {
      dashboardRef.value.filters.forEach(f => {
        if (f.type === 'time') {
          const today = new Date().toISOString().split('T')[0]
          activeFilterValues.value[f.id] = { from: today, to: today }
        }
      })
    }
  }

  return { activeFilterValues, resolvedDashboardFilters, resetFilters }
}
