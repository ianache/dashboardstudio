# Arquitectura

## Estructura de directorios

```
src/
├── main.js                          # Bootstrap: registra ECharts, Pinia, Router
├── App.vue                          # Root: solo <router-view>
├── assets/main.css                  # Design system (CSS custom properties)
│
├── router/index.js                  # Rutas + guards de autenticación y rol
│
├── stores/
│   ├── auth.js                      # Autenticación, roles, usuarios mock
│   ├── dashboard.js                 # CRUD dashboards y widgets
│   ├── cubejs.js                    # Cliente CubeJS, meta schema, queries
│   ├── ui.js                        # Sidebar, breadcrumbs, alertas, dropdowns
│   ├── dataTypes.js                 # Tipos de datos SQL personalizados
│   └── dimensionalModel.js          # Modelos dimensionales (star schema)
│
├── composables/
│   ├── useCubeQuery.js              # Fetch datos CubeJS, mock data, CSV
│   └── useDashboardFilters.js       # Construcción de filtros activos
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.vue            # Shell: SideMenu + TopBar + router-view
│   │   ├── SideMenu.vue             # Sidebar colapsable con navegación por rol
│   │   └── TopBar.vue               # Breadcrumbs, alertas, menú de usuario
│   │
│   ├── dashboard/
│   │   ├── DashboardGrid.vue        # Canvas 12 cols, drag & resize
│   │   ├── DashboardWidget.vue      # Tarjeta widget: header + EChartWrapper
│   │   ├── DashboardFilterBar.vue   # Controles de filtros de dashboard
│   │   └── ChartConfigModal.vue     # Modal 4 tabs de configuración de widget
│   │
│   └── charts/
│       └── EChartWrapper.vue        # Transforma datos → option ECharts
│
└── views/
    ├── LoginView.vue
    ├── HomeView.vue
    ├── DashboardDesignerView.vue     # Lista + editor de dashboards
    ├── DashboardViewerView.vue       # Vista de solo lectura
    ├── SettingsView.vue              # Config CubeJS, perfil, usuarios
    ├── DimensionalModelListView.vue  # Lista de modelos dimensionales
    ├── DimensionalModelEditorView.vue # Editor canvas de modelos
    └── DataTypesView.vue             # Tipos de datos SQL
```

## Jerarquía de componentes

```
App.vue
└── RouterView
    ├── LoginView               # / login (sin layout)
    └── AppLayout               # / (autenticado)
        ├── SideMenu            # sidebar fijo (colapsable)
        ├── TopBar              # header fijo
        └── RouterView (main)
            ├── HomeView
            ├── DashboardDesignerView
            │   └── DashboardGrid
            │       └── DashboardWidget (n)
            │           └── EChartWrapper
            ├── DashboardViewerView
            │   ├── DashboardFilterBar
            │   └── DashboardGrid
            │       └── DashboardWidget (n)
            │           └── EChartWrapper
            ├── DimensionalModelListView
            ├── DimensionalModelEditorView
            ├── DataTypesView
            └── SettingsView
```

## Flujo de datos

```
┌─────────────────────────────────────────────────────────────┐
│                     Pinia Stores                            │
│  auth ─── dashboard ─── cubejs ─── ui ─── dataTypes ─── dm │
└──────┬──────────┬──────────┬─────────────────────────────────┘
       │          │          │
       ▼          ▼          ▼
   Guards      Views      Composables
   (router)    (CRUD)     (useCubeQuery)
                │              │
                ▼              ▼
           DashboardGrid   ECharts data
                │
                ▼
           DashboardWidget
                │
                ▼
           EChartWrapper ◄── chartOptions override
```

### Flujo de un widget

1. `DashboardWidget` monta → llama `useCubeQuery(widget, filtersRef)`
2. `useCubeQuery` comprueba si hay token CubeJS; si no, genera **mock data** por tipo de gráfico
3. Con token: construye query CubeJS, llama a `cubeStore.executeQuery()`
4. El resultado se transforma a `{ label, value, value2 }` en el composable
5. `EChartWrapper` recibe `data` + `chartType` → genera `option` ECharts
6. Si el widget tiene `chartOptions` (JSON personalizado), se fusiona con `deepMerge`

### Flujo de filtros de dashboard

1. `DashboardFilterBar` emite cambios de valor → `activeFilterValues`
2. `useDashboardFilters` computa `resolvedDashboardFilters` (array de filtros CubeJS)
3. `DashboardViewerView`/`DashboardDesignerView` pasan `dashboardFilters` como prop a `DashboardGrid`
4. `DashboardGrid` los pasa a cada `DashboardWidget`
5. `DashboardWidget` los pasa a `useCubeQuery` que los incorpora en la query

## Persistencia

Todo se almacena en **localStorage** (sin backend):

| Clave | Contenido |
|---|---|
| `auth` | Usuario autenticado y token de sesión |
| `dashboards` | Array de dashboards con widgets |
| `mockUsers` | Usuarios con dashboards asignados |
| `cubeApiUrl` / `cubeToken` | Configuración CubeJS |
| `dataTypes` | Tipos de datos SQL personalizados |
| `dimensionalModels` | Modelos dimensionales |

## Sistema de grid

`DashboardGrid.vue` implementa un canvas de posicionamiento libre:

- **12 columnas**, alto de fila = 90 px, gap = 10 px
- Posicionamiento con CSS `position: absolute` calculado en píxeles
- **Drag**: listeners globales `document.mousemove/mouseup`; `grabOffsetX/Y` evita saltos
- **Resize**: handles E (ancho), S (alto), SE (diagonal)
- **Snap**: columna más cercana al soltar (`snapCol`, `snapRow`)
- `clientToCanvas(clientX, clientY)` descuenta el scroll del canvas

## Convenciones de código

| Aspecto | Convención |
|---|---|
| Componentes | `<script setup>` (Composition API) |
| Stores | Options API (`state/getters/actions`) |
| Alias | `@` → `src/` |
| Tipado | JavaScript puro (sin TypeScript) |
| CSS | `<style scoped>` + CSS custom properties |
| Framework CSS | Ninguno (estilos propios) |

## Variables CSS globales

```css
--primary: #1890ff         /* Color principal */
--error: #ff4d4f           /* Color de error */
--sidebar-bg: #001529      /* Fondo sidebar */
--sidebar-width: 240px
--sidebar-collapsed-width: 56px
--topbar-height: 56px
--bg: #f0f2f5              /* Fondo de contenido */
--border: #e8e8e8
--border-radius: 8px
--shadow / --shadow-md     /* Sombras de tarjetas */
--text / --text-secondary  /* Colores de texto */
```
