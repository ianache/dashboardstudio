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
  MarkLineComponent
} from 'echarts/components'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import keycloak from './services/keycloak'
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
  MarkLineComponent
])

keycloak
  .init({
    onLoad: 'login-required',
    checkLoginIframe: false,
    pkceMethod: 'S256'
  })
  .then(authenticated => {
    if (!authenticated) {
      // Shouldn't happen with onLoad: 'login-required', but guard anyway
      keycloak.login()
      return
    }

    const app = createApp(App)
    const pinia = createPinia()

    app.use(pinia)
    app.use(router)
    app.component('v-chart', ECharts)

    const authStore = useAuthStore()
    authStore.initFromKeycloak(keycloak)

    // Refresh token before it expires (60s buffer)
    keycloak.onTokenExpired = () => {
      keycloak
        .updateToken(60)
        .then(refreshed => {
          if (refreshed) authStore.onTokenRefreshed()
        })
        .catch(() => authStore.logout())
    }

    app.mount('#app')
  })
  .catch(err => {
    console.error('Keycloak init failed:', err)
    document.body.innerHTML =
      '<div style="padding:40px;font-family:sans-serif;color:#d32f2f">' +
      '<h2>Error de autenticación</h2>' +
      '<p>No se pudo conectar con el servidor de autenticación. ' +
      'Verifica que Keycloak esté disponible en <strong>' +
      (import.meta.env.VITE_KEYCLOAK_URL || 'http://keycloak.local') +
      '</strong></p>' +
      '</div>'
  })
