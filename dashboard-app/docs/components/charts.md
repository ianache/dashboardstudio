# Componente: EChartWrapper

**Archivo:** `src/components/charts/EChartWrapper.vue`

Transforma datos internos al formato de opciones de Apache ECharts y renderiza el gráfico.

## Props

| Prop | Tipo | Descripción |
|---|---|---|
| `chartType` | `String` | Tipo de gráfico (`bar`, `line`, `pie`, `gauge`, `radar`, `combined`) |
| `data` | `Array` | Datos en formato `[{ label, value, value2? }]` |
| `loading` | `Boolean` | Muestra skeleton de carga |
| `error` | `String \| null` | Mensaje de error a mostrar |
| `widget` | `Object` | Widget completo (accede a `chartOptions` y `colorPalette`) |
| `dashboardPalette` | `String \| null` | ID de paleta del dashboard padre |

## Resolución de colores

Los colores de las series se resuelven en este orden de prioridad:

```
widget.colorPalette === 'none'   →  sin paleta (usa colores de medidas)
widget.colorPalette === <id>     →  paleta específica del widget
dashboardPalette prop            →  paleta del dashboard
paletteStore.defaultPaletteId   →  paleta predeterminada del sistema
(ninguna)                        →  array COLORS hardcoded
```

Consultar [colorPalettes store](../stores/colorPalettes.md) para detalles del sistema de paletas.

## Formato de datos internos

```javascript
[
  { label: 'Enero',   value: 1200, value2: 950 },
  { label: 'Febrero', value: 1500, value2: 1100 },
  // ...
]
```

- `label`: eje X / categoría / sector del pie
- `value`: métrica principal (eje Y izquierdo / porcentaje / valor)
- `value2`: métrica secundaria (solo para `combined`)

## Tipos de gráfico

### `bar` — Barras verticales

- Ejes X (categorías) e Y (valores)
- Colores de las barras: extraídos de `widget.cubeQuery.measures[].color`
- `borderRadius` en la parte superior de cada barra
- Tooltip con valores formateados

### `line` — Líneas suaves

- Línea suavizada (`smooth: true`)
- Área semitransparente bajo la línea
- Soporte para múltiples series

### `pie` — Donut

- Donut con radio interior del 50%
- Labels con porcentaje y nombre
- Tooltip con valor absoluto y porcentaje

### `gauge` — Gauge semicircular

- Muestra el primer valor `data[0].value`
- Zonas de color:
  - 0–60%: verde (`#52c41a`)
  - 60–80%: amarillo (`#faad14`)
  - 80–100%: rojo (`#f5222d`)
- Título centrado bajo el gauge

### `radar` — Araña / Radar

- Área rellena semitransparente
- Indicadores basados en los labels de datos
- El valor máximo de cada eje se calcula como `max(values) * 1.2`

### `combined` — Barras + Línea

- Barras en eje Y izquierdo (usando `value`)
- Línea suavizada en eje Y derecho (usando `value2`)
- Dos ejes Y independientes

## `chartOptions` (override personalizado)

Si el widget tiene `chartOptions` con contenido JSON, se fusiona sobre la opción base:

```javascript
const finalOption = deepMerge(baseOption, widget.chartOptions)
```

`deepMerge` hace una fusión profunda recursiva — puedes sobreescribir cualquier propiedad de ECharts sin reemplazar el objeto completo.

### Ejemplo de override

```json
{
  "xAxis": { "axisLabel": { "rotate": 45 } },
  "color": ["#ff6b6b", "#4ecdc4", "#45b7d1"]
}
```

## Estados especiales

### Cargando

Se muestra un skeleton animado (pulso) en lugar del gráfico.

### Sin datos

```
📊
Sin datos disponibles
```

### Error

```
⚠
Error al cargar datos
[mensaje de error]
```

## Auto-resize

El componente usa `vue-echarts` con `autoresize: true`, por lo que el gráfico se re-renderiza automáticamente cuando cambia el tamaño del contenedor (ej: al redimensionar un widget).

## Registro de módulos ECharts

Los módulos necesarios se registran en `main.js` con `use()`:

```javascript
use([
  CanvasRenderer,
  BarChart, LineChart, PieChart, GaugeChart, RadarChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DataZoomComponent, ToolboxComponent, MarkLineComponent
])
```
