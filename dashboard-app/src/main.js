import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  BarChart,
  LineChart,
  PieChart,
  GaugeChart,
  RadarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
  GraphicComponent
} from 'echarts/components'

// ECharts registers mousewheel listeners without { passive: true }, triggering
// browser violations. Patch addEventListener globally so wheel-type events are
// always passive, which is safe — ECharts never calls preventDefault() on them.
;(function patchPassiveWheelListeners() {
  const original = EventTarget.prototype.addEventListener
  EventTarget.prototype.addEventListener = function (type, fn, options) {
    if (type === 'mousewheel' || type === 'wheel' || type === 'touchstart' || type === 'touchmove') {
      if (typeof options === 'object' && options !== null) {
        options = { ...options, passive: true }
      } else {
        options = { passive: true, capture: options === true }
      }
    }
    return original.call(this, type, fn, options)
  }
})()

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './assets/main.css'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  GaugeChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
  GraphicComponent
])

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore()

// Initialize auth from BFF session before mounting to avoid UI flickering
authStore.initialize()
  .then((success) => {
    if (!success) {
      authStore.login()
      return
    }
    app.use(router)
    app.component('v-chart', ECharts)
    app.mount('#app')
  })
  .catch(err => {
    console.error('Failed to initialize app:', err)
    // Fallback error display if initialization fails completely
    document.body.innerHTML = 
      '<div style="padding:40px;font-family:sans-serif;max-width:700px">' +
      '<h2 style="color:#d32f2f">Error de inicialización</h2>' +
      '<p>No se pudo iniciar la aplicación. Por favor, intente recargar la página.</p>' +
      '</div>'
  })
