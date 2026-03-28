import { ref, computed } from 'vue'
import { buildCubeFilter } from './useCubeQuery'

export function useDashboardFilters(dashboardRef) {
  const activeFilterValues = ref({})

  const resolvedDashboardFilters = computed(() => {
    const schema = dashboardRef.value?.filters || []
    return schema.flatMap(f => buildCubeFilter(f, activeFilterValues.value[f.id]))
  })

  function resetFilters() {
    activeFilterValues.value = {}
  }

  return { activeFilterValues, resolvedDashboardFilters, resetFilters }
}
