import { defineStore } from 'pinia'

export const useVisualizationConfiguratorStore = defineStore('visualizationConfigurator', {
  state: () => ({
    dashboardId: null,
    widgetId: null,
    title: 'Nuevo Gráfico',
    selectedCube: null,
    measures: [],
    dimensions: [],
    filters: [],
    timeDimension: null,
    chartType: 'bar',
    chartOptions: {}
  }),

  actions: {
    setDashboardId(id) {
      this.dashboardId = id
    },

    setWidget(widget) {
      if (!widget) return
      
      this.widgetId = widget.id || null
      this.title = widget.title || 'Nuevo Gráfico'
      this.chartType = widget.chartType || 'bar'
      this.chartOptions = widget.chartOptions || {}
      
      if (widget.cubeQuery) {
        this.measures = widget.cubeQuery.measures || []
        this.dimensions = widget.cubeQuery.dimensions || []
        this.filters = widget.cubeQuery.filters || []
        this.timeDimension = widget.cubeQuery.timeDimension || null
        
        // Infer selectedCube from measures or dimensions if available
        if (this.measures.length > 0) {
          this.selectedCube = this.measures[0].split('.')[0]
        } else if (this.dimensions.length > 0) {
          this.selectedCube = this.dimensions[0].split('.')[0]
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
      if (!this.measures.includes(measure)) {
        this.measures.push(measure)
      }
    },

    removeMeasure(measureName) {
      this.measures = this.measures.filter(m => m !== measureName)
    },

    addDimension(dimension) {
      if (!this.dimensions.includes(dimension)) {
        this.dimensions.push(dimension)
      }
    },

    removeDimension(dimensionName) {
      this.dimensions = this.dimensions.filter(d => d !== dimensionName)
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
