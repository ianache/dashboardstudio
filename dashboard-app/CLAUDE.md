# Dashboard Studio — CLAUDE.md

## Resumen del proyecto

Aplicación web para **diseñar y ejecutar dashboards** conectados a CubeJS como capa semántica. Los usuarios con rol **Diseñador** crean dashboards con gráficos Apache ECharts; los usuarios **Visualizadores** acceden a los dashboards que les han sido asignados.

## Comandos esenciales

```bash
npm run dev      # Servidor de desarrollo → http://localhost:3000
npm run build    # Build de producción
npm run preview  # Vista previa del build
```

## Stack tecnológico

| Tecnología | Versión | Uso |
|---|---|---|
| Vue 3 | ^3.4 | Framework principal, Composition API + `<script setup>` |
| Pinia | ^2.1 | Estado global (4 stores) |
| Vue Router | ^4.3 | Navegación SPA con guards de rol |
| Apache ECharts | ^5.4 | Renderizado de gráficos (via vue-echarts) |
| vue-echarts | ^6.6 | Wrapper Vue para ECharts |
| @cubejs-client/core | ^0.35 | Cliente CubeJS para queries semánticas |
| @vueuse/core | ^10.9 | Utilidades reactivas de Vue |
| Vite | ^5.2 | Bundler y dev server |

## Arquitectura

```
src/
├── main.js                          # Bootstrap: registra ECharts modules + Pinia + Router
├── App.vue                          # Root: solo <router-view>
├── assets/main.css                  # Design system (CSS custom properties, componentes base)
│
├── router/index.js                  # Rutas + guards de autenticación y rol
│
├── stores/
│   ├── auth.js            # Autenticación, roles, usuarios mock, persistencia localStorage
│   ├── dashboard.js       # CRUD dashboards y widgets, persistencia localStorage
│   ├── cubejs.js          # Cliente CubeJS, meta schema, ejecución de queries
│   ├── ui.js              # Sidebar collapsed, breadcrumbs, alertas, dropdowns
│   └── colorPalettes.js   # Paletas de colores CRUD + defaultPaletteId, persistencia localStorage
│
├── composables/
│   └── useCubeQuery.js  # Fetch datos CubeJS, generador de mock data, descarga CSV
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.vue   # Shell: SideMenu + TopBar + <router-view> en main
│   │   ├── SideMenu.vue    # Sidebar colapsable (icono hamburguesa en TopBar)
│   │   └── TopBar.vue      # Breadcrumbs + dropdown alertas + dropdown usuario
│   │
│   ├── dashboard/
│   │   ├── DashboardGrid.vue      # Canvas de posicionamiento libre (12 cols), drag & resize
│   │   ├── DashboardWidget.vue    # Tarjeta widget: cabecera acciones + cuerpo EChartWrapper
│   │   └── ChartConfigModal.vue   # Modal 4 tabs: General / Datos CubeJS / Visualización / Esquema
│   │
│   └── charts/
│       └── EChartWrapper.vue  # Transforma datos → option ECharts según chartType
│
└── views/
    ├── LoginView.vue             # Pantalla de login con credenciales demo
    ├── HomeView.vue              # Dashboard de bienvenida con stats y acceso rápido
    ├── DashboardDesignerView.vue # Lista de dashboards + editor en modo diseño/preview
    ├── DashboardViewerView.vue   # Visualización de un dashboard (solo lectura)
    └── SettingsView.vue          # Config CubeJS, perfil de usuario, gestión de usuarios
```

## Modelo de datos

### Dashboard
```javascript
{
  id: string,
  name: string,
  description: string,
  isPublic: boolean,
  assignedUsers: string[],   // IDs de usuarios visualizadores
  createdBy: string,
  createdAt: ISO string,
  updatedAt: ISO string,
  widgets: Widget[]
}
```

### Widget
```javascript
{
  id: string,
  title: string,
  chartType: 'bar' | 'line' | 'pie' | 'gauge' | 'radar' | 'combined',
  position: { x: number, y: number, w: number, h: number },  // grid 12 cols
  cubeQuery: {
    measures: [{ key: string, label: string, color: string }],
    dimensions: [{ key: string, label: string }],
    timeDimension: { dimension: string, granularity: string } | null,
    filters: [{ member, operator, values }],
    limit: number
  },
  chartOptions: {},      // override de opciones ECharts (JSON libre)
  useMockData: boolean
}
```

## Roles y acceso

| Rol | Login demo | Capacidades |
|---|---|---|
| `designer` | admin@demo.com / admin123 | Crear/editar/eliminar dashboards, configurar widgets, asignar usuarios, ver todo |
| `viewer` | viewer@demo.com / viewer123 | Solo ver dashboards asignados o públicos |

- El guard de ruta `requiresDesigner` bloquea `/designer/*` para viewers
- `SideMenu` muestra la sección "DISEÑO" solo a designers
- `DashboardViewerView` verifica acceso: `isPublic || assignedUsers.includes(userId)`

## Persistencia

Todo se guarda en **localStorage** (sin backend real):
- `auth` → usuario y token de sesión actual
- `dashboards` → array de todos los dashboards con sus widgets
- `mockUsers` → usuarios y sus dashboards asignados
- `cubeApiUrl` / `cubeToken` → configuración de conexión CubeJS

## Grid del dashboard

`DashboardGrid.vue` implementa un canvas de posicionamiento libre:
- 12 columnas, alto de fila = 90px, gap = 10px
- Posición calculada con CSS `position: absolute` + coordenadas en píxeles
- En modo diseño: `mousedown/mousemove/mouseup` para drag y resize (handles E, S, SE)
- Snap automático a la celda de grid más cercana al soltar

## Integración CubeJS

`stores/cubejs.js` gestiona:
- `setConfig(apiUrl, token)` → persiste en localStorage
- `loadMeta()` → carga el schema (`/cubejs-api/v1/meta`)
- `executeQuery(query)` → ejecuta una query CubeJS

`composables/useCubeQuery.js`:
- Si `useMockData = true` o no hay token → genera datos simulados por tipo de gráfico
- Transforma el resultado CubeJS (`tablePivot()`) al formato `{ label, value, value2 }` que consume `EChartWrapper`

## ECharts — tipos de gráfico

`EChartWrapper.vue` construye la `option` ECharts según `chartType`:

| Tipo | Descripción |
|---|---|
| `bar` | Barras verticales, color por serie, borderRadius en tope |
| `line` | Líneas suaves con área semitransparente |
| `pie` | Donut chart con labels de porcentaje |
| `gauge` | Gauge semicircular con zonas rojo/amarillo/verde |
| `radar` | Gráfico de araña con área rellena |
| `combined` | Barras (eje Y izquierdo) + Línea (eje Y derecho) |

Las `chartOptions` del widget se fusionan en profundidad (`deepMerge`) sobre la opción base, permitiendo cualquier personalización ECharts.

## Variables CSS globales (`assets/main.css`)

```css
--primary: #1890ff        /* Color principal */
--sidebar-bg: #001529     /* Fondo sidebar oscuro */
--sidebar-width: 240px    /* Ancho sidebar expandido */
--sidebar-collapsed-width: 56px
--topbar-height: 56px
--bg: #f0f2f5             /* Fondo de contenido */
--border-radius: 8px
--shadow / --shadow-md    /* Sombras de tarjetas */
```

## Convenciones de código

- Todos los componentes usan `<script setup>` (Composition API)
- Stores Pinia en Options API style (`state/getters/actions`)
- Alias `@` → `src/` configurado en `vite.config.js`
- Sin TypeScript (JS puro)
- Sin framework CSS externo (estilos propios con CSS custom properties)
- `<style scoped>` en todos los componentes

## Configuración CubeJS (.env)

```env
VITE_CUBEJS_API_URL=http://localhost:4000/cubejs-api/v1
VITE_CUBEJS_TOKEN=<jwt-token>
```

También configurable en runtime desde la UI: **Configuración → Conexión CubeJS**.
