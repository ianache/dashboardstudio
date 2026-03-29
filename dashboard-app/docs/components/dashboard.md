# Componentes de Dashboard

## DashboardGrid.vue

**Archivo:** `src/components/dashboard/DashboardGrid.vue`

Canvas de 12 columnas para posicionamiento libre de widgets con soporte para drag & drop y redimensionado.

### Props

| Prop | Tipo | Descripción |
|---|---|---|
| `widgets` | `Array` | Lista de widgets a renderizar |
| `isDesignMode` | `Boolean` | Activa drag, resize y handles de diseño |
| `dashboardId` | `String` | ID del dashboard (para actualizar posiciones) |
| `dashboardFilters` | `Array` | Filtros activos del dashboard |
| `dashboardPalette` | `String \| null` | ID de paleta del dashboard; se propaga a todos los widgets |

### Emits

| Evento | Payload | Descripción |
|---|---|---|
| `configure-widget` | `widget` | Usuario clic en ⚙️ del widget |
| `remove-widget` | `widgetId` | Usuario clic en 🗑️ del widget |

### Constantes de grid

```javascript
COL_COUNT = 12       // número de columnas
ROW_HEIGHT = 90      // px por fila
GAP = 10             // px de separación entre celdas
```

### Funciones internas clave

#### `getColWidth()`
Calcula el ancho en píxeles de cada columna en función del ancho actual del canvas.

```javascript
(canvasRef.offsetWidth - GAP * (COL_COUNT + 1)) / COL_COUNT
```

#### `clientToCanvas(clientX, clientY)`
Convierte coordenadas del puntero (relativas a la ventana) a coordenadas del canvas, considerando el scroll:

```javascript
{
  x: clientX - rect.left + canvasRef.scrollLeft,
  y: clientY - rect.top  + canvasRef.scrollTop
}
```

#### `snapCol(pxLeft)` / `snapRow(pxTop)`
Convierten píxeles a unidades de grid con redondeo al más cercano:

```javascript
snapCol(pxLeft) = Math.round((pxLeft - GAP) / (colWidth + GAP))
snapRow(pxTop)  = Math.round((pxTop  - GAP) / (ROW_HEIGHT + GAP))
```

### Drag de widgets

1. `DashboardWidget` emite `drag-start` cuando el usuario hace `mousedown` en su header
2. `DashboardGrid` llama `startDrag(e, widget)`:
   - Registra `grabOffsetX/Y` (dónde dentro del widget se hizo el click)
   - Guarda posición del puntero en canvas
3. Listeners globales en `document` rastrean `mousemove` y `mouseup`
4. Al soltar (`mouseup`): calcula posición final con snap y llama `dashboardStore.updateWidgetPosition()`

> Los listeners globales evitan que el drag se cancele si el cursor sale del canvas.

### Resize de widgets

Handles visibles en modo diseño al hover:
- **E** (derecho): cambia `w`
- **S** (inferior): cambia `h`
- **SE** (esquina): cambia `w` y `h`

El resize actualiza la posición en tiempo real durante `mousemove`, con mínimo `w=1`, `h=1`.

### Ghost de drop

Durante el drag se muestra un rectángulo semitransparente azul (`drag-ghost`) que indica dónde caerá el widget al soltar, con snap en tiempo real.

---

## DashboardWidget.vue

**Archivo:** `src/components/dashboard/DashboardWidget.vue`

Tarjeta de widget individual: gestiona la obtención de datos y renderiza el gráfico.

### Props

| Prop | Tipo | Descripción |
|---|---|---|
| `widget` | `Object` | Configuración completa del widget |
| `isDesignMode` | `Boolean` | Activa controles de diseño |
| `isSelected` | `Boolean` | Resalta con borde de selección |
| `dashboardFilters` | `Array` | Filtros del dashboard padre |
| `dashboardPalette` | `String \| null` | ID de paleta del dashboard; se pasa a `EChartWrapper` |

### Emits

| Evento | Descripción |
|---|---|
| `configure` | Abrir modal de configuración |
| `remove` | Eliminar widget |
| `select` | Seleccionar widget (modo diseño) |
| `drag-start` | Inicio de drag (desde el header) |
| `resize-start` (dir, event) | Inicio de resize |

### Estructura visual

```
┌─────────────────────────────────────┐
│ [icon] Título          [⚙][↻][⬇][🗑]│  ← widget-header (drag handle)
├─────────────────────────────────────┤
│                                     │
│           EChartWrapper             │  ← widget-body (flex: 1)
│                                     │
├─────────────────────────────────────┤
│ Actualizado: 14:32                  │  ← widget-footer (solo vista)
└─────────────────────────────────────┘
   ──►  ▐  ◄── resize handles (diseño)
   ──────────────────────────────────▐
```

### Obtención de datos

Usa el composable `useCubeQuery(widget, dashboardFiltersRef)`.

Los datos se recargan automáticamente cuando cambia:
- `widget.cubeQuery` (watch deep)
- `widget.useMockData`
- `dashboardFilters`

### Botones de acción

| Botón | Condición | Acción |
|---|---|---|
| ⚙️ Configurar | Solo diseño | Emite `configure` |
| ↻ Actualizar | Siempre | Llama `fetchData()` |
| ⬇ CSV | Siempre | Llama `downloadCSV(data, title)` |
| 🗑 Eliminar | Solo diseño | Emite `remove` |

---

## ChartConfigModal.vue

**Archivo:** `src/components/dashboard/ChartConfigModal.vue`

Modal de 4 pestañas para configurar completamente un widget.

### Props

| Prop | Tipo | Descripción |
|---|---|---|
| `widget` | `Object` | Widget a configurar |
| `dashboardId` | `String` | ID del dashboard |

### Emits

| Evento | Descripción |
|---|---|
| `close` | Cerrar el modal |

### Pestañas

#### 1. General
- Título del widget
- Tipo de gráfico (`bar`, `line`, `pie`, `gauge`, `radar`, `combined`)
- Toggle "Usar datos simulados"
- Tamaño (ancho/alto en unidades de grid)

#### 2. Datos (CubeJS)
- Selector de medidas (con color y label)
- Selector de dimensiones (con label)
- Dimensión de tiempo + granularidad (`day`, `week`, `month`, `quarter`, `year`)
- Filtros (member, operador, valores)
- Límite de registros

#### 3. Visualización
- **Selector de paleta de colores** con tres opciones especiales:
  - *Heredar* (`null`): usa la paleta del dashboard o la predeterminada del sistema
  - *Sin paleta* (`'none'`): desactiva herencia, usa colores propios de las medidas
  - *Paleta nombrada*: anula cualquier herencia
- Editor JSON de `chartOptions` (se fusiona sobre la configuración base de ECharts)
- Asistente IA para generar opciones ECharts mediante prompt de lenguaje natural

#### 4. Schema
- Browser del meta-schema de CubeJS
- Lista de cubos, medidas y dimensiones disponibles
- Clic en un elemento lo añade a la consulta

---

## DashboardFilterBar.vue

**Archivo:** `src/components/dashboard/DashboardFilterBar.vue`

Barra de filtros interactivos a nivel de dashboard.

### Props

| Prop | Tipo | Descripción |
|---|---|---|
| `filters` | `Array` | Definiciones de filtros del dashboard (`FilterDef[]`) |
| `modelValue` | `Object` | Valores activos `{ filterId: value }` |

### Emits

| Evento | Payload | Descripción |
|---|---|---|
| `update:modelValue` | `{ filterId: value }` | Cuando cambia un valor |

### Tipos de filtro

| `FilterDef.type` | Control renderizado |
|---|---|
| `'string'` | Multi-select (carga valores desde CubeJS o mock) |
| `'time'` | Selector de rango de fechas (`dateFrom`/`dateTo`) |
| `'number'` | Dos inputs numéricos (mín/máx) |

Los valores de los selectores string se cargan con `cubeStore.getDimensionValues(member)`.
