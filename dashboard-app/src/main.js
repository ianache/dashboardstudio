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
  MarkLineComponent,
  GraphicComponent
])

// ── Session persistence ───────────────────────────────────────
// Storing tokens in sessionStorage lets keycloak-js rehydrate them on
// page refresh, bypassing the need for any iframe or browser redirect.
// The Keycloak server at oauth2.qa.comsatel.com.pe sets
// "frame-ancestors 'self'" CSP, which blocks iframe-based silent checks.
const KC_TOKEN     = 'kc_token'
const KC_REFRESH   = 'kc_refresh'
const KC_ID_TOKEN  = 'kc_id'

function storeTokens() {
  if (keycloak.token)        sessionStorage.setItem(KC_TOKEN,    keycloak.token)
  if (keycloak.refreshToken) sessionStorage.setItem(KC_REFRESH,  keycloak.refreshToken)
  if (keycloak.idToken)      sessionStorage.setItem(KC_ID_TOKEN, keycloak.idToken)
}

function clearStoredTokens() {
  sessionStorage.removeItem(KC_TOKEN)
  sessionStorage.removeItem(KC_REFRESH)
  sessionStorage.removeItem(KC_ID_TOKEN)
}

keycloak
  .init({
    // Pass any previously stored tokens. When valid, keycloak-js uses them
    // directly — no redirect, no iframe. Falls back to onLoad behavior only
    // when both the access token and refresh token are expired.
    onLoad: 'check-sso',
    token:        sessionStorage.getItem(KC_TOKEN)    || undefined,
    refreshToken: sessionStorage.getItem(KC_REFRESH)  || undefined,
    idToken:      sessionStorage.getItem(KC_ID_TOKEN) || undefined,
    checkLoginIframe: false,
    pkceMethod: 'S256'
  })
  .then(authenticated => {
    if (!authenticated) {
      clearStoredTokens()
      keycloak.login({ redirectUri: window.location.href })
      return
    }

    storeTokens()

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
          if (refreshed) {
            storeTokens()
            authStore.onTokenRefreshed()
          }
        })
        .catch(() => {
          clearStoredTokens()
          authStore.logout()
        })
    }

    app.mount('#app')
  })
  .catch(err => {
    console.error('Keycloak init failed:', err)
    const kcUrl = import.meta.env.VITE_KEYCLOAK_URL || 'http://keycloak.local'
    const realm = import.meta.env.VITE_KEYCLOAK_REALM || 'dashboard'
    const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'dashboard-app'
    const errDetail = err instanceof Error ? err.message : (typeof err === 'string' ? err : JSON.stringify(err))
    document.body.innerHTML =
      '<div style="padding:40px;font-family:sans-serif;max-width:700px">' +
      '<h2 style="color:#d32f2f">Error de autenticación</h2>' +
      '<p>La inicialización de Keycloak falló. Causa probable:</p>' +
      '<ul style="line-height:2">' +
      '<li>El <strong>Redirect URI</strong> <code>' + window.location.origin + '/*</code> no está registrado en el cliente Keycloak</li>' +
      '<li>El <strong>Web Origin</strong> <code>' + window.location.origin + '</code> no está en la lista de orígenes permitidos del cliente</li>' +
      '<li>El realm <code>' + realm + '</code> o client <code>' + clientId + '</code> no existen en Keycloak</li>' +
      '</ul>' +
      '<details style="margin-top:16px">' +
      '<summary style="cursor:pointer;color:#666">Detalle técnico del error</summary>' +
      '<pre style="background:#f5f5f5;padding:12px;border-radius:6px;margin-top:8px;white-space:pre-wrap;font-size:12px">' +
      (errDetail || '(sin detalle)') + '</pre>' +
      '</details>' +
      '<hr style="margin:24px 0">' +
      '<p style="font-size:13px;color:#666">Servidor: <strong>' + kcUrl + '</strong> — Realm: <strong>' + realm + '</strong> — Client: <strong>' + clientId + '</strong></p>' +
      '</div>'
  })
