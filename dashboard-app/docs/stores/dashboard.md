# Store: dashboard

**Archivo:** `src/stores/dashboard.js`

Gestiona el CRUD completo de dashboards y sus widgets, incluyendo posicionamiento en el grid.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `dashboards` | `array` | Lista de todos los dashboards (cargada desde localStorage) |

## Modelos de datos

### Dashboard

```javascript
{
  id: string,
  name: string,
  description: string,
  isPublic: boolean,
  assignedUsers: string[],   // IDs de usuarios viewers con acceso
  filters: FilterDef[],      // Definiciones de filtros del dashboard
  createdBy: string,         // ID del usuario que lo creó
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
  position: {
    x: number,   // columna (0-11)
    y: number,   // fila (0+)
    w: number,   // ancho en columnas
    h: number    // alto en filas
  },
  cubeQuery: {
    measures: [{ key: string, label: string, color: string }],
    dimensions: [{ key: string, label: string }],
    timeDimension: { dimension: string, granularity: string } | null,
    filters: [{ member: string, operator: string, values: any[] }],
    limit: number
  },
  chartOptions: object,      // Override JSON de opciones ECharts
  useMockData: boolean
}
```

### FilterDef (filtro de dashboard)

```javascript
{
  id: string,
  label: string,
  member: string,            // Dimensión CubeJS (ej: "Orders.status")
  type: 'string' | 'time' | 'number',
  operator: string           // 'equals', 'gte', 'lte', 'inDateRange', etc.
}
```

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `allDashboards` | `array` | Todos los dashboards |
| `getDashboard(id)` | `object \| null` | Dashboard por ID |
| `myDashboards` | `array` | Dashboards del usuario autenticado |
| `publicDashboards` | `array` | Dashboards marcados como públicos |
| `accessibleDashboards(userId)` | `array` | Dashboards públicos + asignados a ese usuario |

## Acciones

### Gestión de dashboards

| Acción | Descripción |
|---|---|
| `createDashboard({ name, description, createdBy })` | Crea un dashboard vacío; retorna el objeto creado |
| `updateDashboard(id, patch)` | Actualiza campos del dashboard (nombre, descripción, etc.) |
| `deleteDashboard(id)` | Elimina el dashboard y todos sus widgets |
| `duplicateDashboard(id)` | Clona el dashboard con un nuevo ID y nombre `"Copia de ..."` |

### Gestión de widgets

| Acción | Descripción |
|---|---|
| `addWidget(dashboardId, widgetData)` | Añade un widget al dashboard; retorna el widget creado |
| `updateWidget(dashboardId, widgetId, patch)` | Actualiza configuración del widget |
| `removeWidget(dashboardId, widgetId)` | Elimina un widget |
| `updateWidgetPosition(dashboardId, widgetId, position)` | Actualiza `{ x, y, w, h }` |

### Gestión de filtros

| Acción | Descripción |
|---|---|
| `addFilter(dashboardId, filterDef)` | Añade una definición de filtro al dashboard |
| `updateFilter(dashboardId, filterId, patch)` | Actualiza una definición de filtro |
| `removeFilter(dashboardId, filterId)` | Elimina un filtro |

### Asignación de usuarios

| Acción | Descripción |
|---|---|
| `toggleUserAccess(dashboardId, userId)` | Añade/quita un usuario de `assignedUsers` |
| `setPublic(dashboardId, isPublic)` | Cambia visibilidad pública |

## Persistencia

`persist()` es un helper privado que serializa `this.dashboards` a `localStorage['dashboards']`. Se llama al final de cada acción mutante.

## Posiciones de widgets (grid)

Las posiciones usan unidades de grid, no píxeles:

- **x**: columna de inicio (0 = izquierda, 11 = extremo derecho)
- **y**: fila de inicio (0 = arriba)
- **w**: ancho en columnas (máximo 12)
- **h**: alto en filas

La conversión a píxeles la realiza `DashboardGrid.vue`:

```
left  = GAP + x * (colWidth + GAP)
top   = GAP + y * (ROW_HEIGHT + GAP)
width = w * colWidth + (w - 1) * GAP
height = h * ROW_HEIGHT + (h - 1) * GAP
```

donde `GAP = 10px`, `ROW_HEIGHT = 90px` y `colWidth = (canvasWidth - GAP * 13) / 12`.
