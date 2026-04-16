import { defineStore } from 'pinia'
import { useCubeStore } from './cubejs'

export const useVisualizationConfiguratorStore = defineStore('visualizationConfigurator', {
  state: () => ({
    dashboardId: null,
    widgetId: null,
    title: 'Nuevo Gráfico',
    selectedCube: null,
    measures: [], // Array of objects: { fullName, title, type, memberType }
    dimensions: [], // Array of objects: { fullName, title, type, memberType }
    filters: [],
    timeDimension: null,
    chartType: 'bar',
    chartOptions: {}
  }),

  actions: {
    setDashboardId(id) {
      this.dashboardId = id
    },

    setTitle(title) {
      this.title = title
    },

    setWidget(widget) {
      if (!widget) return
      
      this.widgetId = widget.id || null
      this.title = widget.title || 'Nuevo Gráfico'
      this.chartType = widget.chartType || 'bar'
      this.chartOptions = widget.chartOptions || {}
      
      if (widget.cubeQuery) {
        const cubeStore = useCubeStore()
        
        // Map string names to full objects from metadata if available
        this.measures = (widget.cubeQuery.measures || []).map(m => {
          const fullName = typeof m === 'string' ? m : m.key || m.fullName
          const meta = cubeStore.allMeasures.find(am => am.fullName === fullName)
          const base = meta || { fullName: fullName, title: fullName.split('.').pop() }
          
          // Restore alias and format if they exist in the saved query
          if (typeof m === 'object') {
            return {
              ...base,
              alias: m.label !== base.title ? m.label : undefined,
              format: m.format
            }
          }
          return base
        })
        
        this.dimensions = (widget.cubeQuery.dimensions || []).map(d => {
          const fullName = typeof d === 'string' ? d : d.key || d.fullName
          const meta = cubeStore.allDimensions.find(ad => ad.fullName === fullName)
          const base = meta || { fullName: fullName, title: fullName.split('.').pop() }
          
          // Restore alias if it exists
          if (typeof d === 'object') {
            return {
              ...base,
              alias: d.label !== base.title ? d.label : undefined
            }
          }
          return base
        })
        
        this.filters = (widget.cubeQuery.filters || []).map(f => {
          const fullName = f.member || f.fullName
          const meta = cubeStore.allDimensions.find(ad => ad.fullName === fullName)
          const base = meta || { fullName: fullName, title: fullName.split('.').pop() }
          return {
            ...base,
            operator: f.operator,
            values: f.values
          }
        })
        this.timeDimension = widget.cubeQuery.timeDimension || null
        
        // Infer selectedCube from measures or dimensions if available
        if (this.measures.length > 0) {
          this.selectedCube = this.measures[0].fullName.split('.')[0]
        } else if (this.dimensions.length > 0) {
          this.selectedCube = this.dimensions[0].fullName.split('.')[0]
        }
      }
    },

    setCube(cubeName) {
      if (this.selectedCube !== cubeName) {
        this.selectedCube = cubeName
        // Reset selections when cube changes
        this.measures = []
        this.dimensions = []
        this.filters = []
        this.timeDimension = null
      }
    },

    addMeasure(measure) {
      const fullName = typeof measure === 'string' ? measure : measure.fullName
      if (!this.measures.find(m => m.fullName === fullName)) {
        if (typeof measure === 'string') {
          this.measures.push({ fullName, title: fullName.split('.').pop() })
        } else {
          this.measures.push(measure)
        }
      }
    },

    removeMeasure(measureFullName) {
      this.measures = this.measures.filter(m => m.fullName !== measureFullName)
    },

    updateMeasure(fullName, updates) {
      const index = this.measures.findIndex(m => m.fullName === fullName)
      if (index !== -1) {
        this.measures[index] = { ...this.measures[index], ...updates }
      }
    },

    addDimension(dimension) {
      const fullName = typeof dimension === 'string' ? dimension : dimension.fullName
      if (!this.dimensions.find(d => d.fullName === fullName)) {
        if (typeof dimension === 'string') {
          this.dimensions.push({ fullName, title: fullName.split('.').pop() })
        } else {
          this.dimensions.push(dimension)
        }
      }
    },

    removeDimension(dimensionFullName) {
      this.dimensions = this.dimensions.filter(d => d.fullName !== dimensionFullName)
    },

    removeFilter(filterFullName) {
      this.filters = this.filters.filter(f => f.fullName !== filterFullName)
    },

    updateFilter(fullName, updates) {
      const index = this.filters.findIndex(f => f.fullName === fullName)
      if (index !== -1) {
        this.filters[index] = { ...this.filters[index], ...updates }
      }
    },

    setChartType(type) {
      this.chartType = type
    },

    reset() {
      this.dashboardId = null
      this.widgetId = null
      this.title = 'Nuevo Gráfico'
      this.selectedCube = null
      this.measures = []
      this.dimensions = []
      this.filters = []
      this.timeDimension = null
      this.chartType = 'bar'
      this.chartOptions = {}
    }
  }
})
