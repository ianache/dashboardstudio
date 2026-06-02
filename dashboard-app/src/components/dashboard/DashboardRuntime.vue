<template>
  <div 
    class="dashboard-runtime" 
    :class="[`layout-${filterPlacement}`, { 'is-design': isDesignMode }]"
  >
    <div class="runtime-filters">
      <DashboardFilterBar
        :dashboard-id="dashboardId"
        :filters="filters"
        :is-design-mode="isDesignMode"
        :vertical="isVertical"
        v-model="filterValues"
        @refresh="$emit('refresh')"
      />
    </div>
    
    <div class="grid-container">
      <DashboardGrid
        :widgets="widgets"
        :is-design-mode="isDesignMode"
        :dashboard-id="dashboardId"
        :dashboard-filters="resolvedFilters"
        :dashboard-palette="palette"
        @configure-widget="$emit('configure-widget', $event)"
        @layout-widget="$emit('layout-widget', $event)"
        @remove-widget="$emit('remove-widget', $event)"
        @widget-data-updated="$emit('widget-data-updated', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFilterBar from './DashboardFilterBar.vue'
import DashboardGrid from './DashboardGrid.vue'

const props = defineProps({
  dashboardId: { type: String, required: true },
  widgets: { type: Array, default: () => [] },
  filters: { type: Array, default: () => [] },
  filterValues: { type: Object, default: () => ({}) },
  resolvedFilters: { type: Array, default: () => [] },
  palette: { type: String, default: null },
  isDesignMode: { type: Boolean, default: false },
  // Layout placement: 'top' | 'left' | 'right'
  filterPlacement: { type: String, default: 'top' }
})

const emit = defineEmits([
  'update:filterValues', 
  'refresh',
  'configure-widget',
  'layout-widget',
  'remove-widget',
  'widget-data-updated'
])

const filterValues = computed({
  get: () => props.filterValues,
  set: (val) => emit('update:filterValues', val)
})

const isVertical = computed(() => ['left', 'right'].includes(props.filterPlacement))
</script>

<style scoped>
.dashboard-runtime {
  display: flex;
  width: 100%;
  flex: 1;
  gap: 20px; /* Consistent gap between filters and grid */
  overflow: hidden;
  min-height: 0;
}

/* Layout variations */
.layout-top {
  flex-direction: column;
}

.layout-left {
  flex-direction: row;
}

.layout-right {
  flex-direction: row-reverse;
}

/* Filter container */
.runtime-filters {
  flex-shrink: 0;
  z-index: 20;
  display: flex;
}

.layout-top .runtime-filters {
  width: 100%;
}

.layout-left .runtime-filters,
.layout-right .runtime-filters {
  width: 260px;
  height: 100%;
}

.grid-container {
  flex: 1;
  background: transparent;
  border: none;
  border-radius: 0;
  overflow: auto;
  padding: 0;
}
</style>
