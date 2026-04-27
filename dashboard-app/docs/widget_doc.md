# Documentación técnica de Widgets — Dashboard Studio

> **Versión:** 1.0 · **Fecha:** 2026-04-26  
> Aplica a la rama `feature/visualimprove` y versiones posteriores.

---

## Índice

1. [Modelo de datos del Widget](#1-modelo-de-datos-del-widget)
2. [Configuración de Medidas (Measures)](#2-configuración-de-medidas-measures)
3. [Widget: Barras — `bar`](#3-widget-barras--bar)
4. [Widget: Líneas — `line`](#4-widget-líneas--line)
5. [Widget: Pastel / Donut — `pie`](#5-widget-pastel--donut--pie)
6. [Widget: Gauge — `gauge`](#6-widget-gauge--gauge)
7. [Widget: Radar — `radar`](#7-widget-radar--radar)
8. [Widget: Combinado — `combined`](#8-widget-combinado--combined)
9. [Widget: Tabla — `table`](#9-widget-tabla--table)
10. [Widget: KPI — `kpi`](#10-widget-kpi--kpi)
11. [Personalización avanzada con `chartOptions`](#11-personalización-avanzada-con-chartoptions)
12. [Paletas de colores](#12-paletas-de-colores)
13. [Datos de demostración (`useMockData`)](#13-datos-de-demostración-usemockdata)

---

## 1. Modelo de datos del Widget

Cada widget es un objeto JSON con la siguiente estructura:

```json
{
  "id": "string",
  "title": "string",
  "chartType": "bar | line | pie | gauge | radar | combined | table | kpi",
  "position": { "x": 0, "y": 0, "w": 6, "h": 3 },
  "cubeQuery": { ... },
  "chartOptions": { ... },
  "pieOptions":      { ... },
  "combinedOptions": { ... },
  "kpiOptions":      { ... },
  "colorPalette": "null | 'none' | '<palette-id>'",
  "useMockData": false
}
```

### Campos raíz

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | Identificador único generado por el backend. |
| `title` | `string` | Título que aparece en la cabecera del widget. |
| `chartType` | `string` | Tipo de visualización. Valores válidos descritos en las secciones siguientes. |
| `position` | `object` | Posición y tamaño en el grid. Explicado abajo. |
| `cubeQuery` | `object` | Configuración de la consulta CubeJS. Ver sección 2. |
| `chartOptions` | `object` | Opciones ECharts libres fusionadas encima de las predeterminadas. Ver sección 11. |
| `pieOptions` | `object` | Opciones específicas del tipo `pie`. Ver sección 5. |
| `combinedOptions` | `object` | Opciones específicas del tipo `combined`. Ver sección 8. |
| `kpiOptions` | `object` | Opciones específicas del tipo `kpi`. Ver sección 10. |
| `colorPalette` | `string \| null` | Paleta de colores. Ver sección 12. |
| `useMockData` | `boolean` | Si es `true`, usa datos simulados en lugar de CubeJS. |

### Position

```json
{ "x": 0, "y": 0, "w": 6, "h": 3 }
```

| Campo | Descripción |
|---|---|
| `x` | Columna de inicio (0–11 en un grid de 12 columnas). |
| `y` | Fila de inicio. |
| `w` | Ancho en columnas (1–12). |
| `h` | Alto en filas (1–10). Cada fila equivale a 90 px. |

---

## 2. Configuración de Medidas (Measures)

`cubeQuery` es el corazón de la consulta. Define qué datos se obtienen de CubeJS.

```json
{
  "measures": [
    {
      "key": "Orders.totalRevenue",
      "label": "Ingresos",
      "color": "#1890ff",
      "format": "moneda",
      "currencyId": "usd",
      "seriesType": "bar",
      "showLabel": true,
      "labelPosition": "top",
      "labelRotate": 0,
      "decimalPlaces": 2
    }
  ],
  "dimensions": [
    { "key": "Orders.status", "label": "Estado" }
  ],
  "timeDimension": {
    "dimension": "Orders.createdAt",
    "granularity": "month"
  },
  "filters": [
    { "member": "Orders.status", "operator": "equals", "values": ["completed"] }
  ],
  "limit": 100
}
```

### Parámetros de una Medida

| Campo | Tipo | Valores válidos | Descripción |
|---|---|---|---|
| `key` | `string` | `Cubo.campo` | Clave exacta del measure en CubeJS. Ej: `Orders.count`. |
| `label` | `string` | Libre | Etiqueta visible en leyenda, tooltip y ejes. |
| `color` | `string` | Hex CSS | Color por defecto de la serie cuando no hay paleta activa. |
| `format` | `string` | `numero`, `moneda`, `porcentaje` | Formato de los valores numéricos en tooltip y etiquetas. |
| `currencyId` | `string \| null` | ID de moneda | Solo aplica cuando `format = 'moneda'`. Determina el símbolo (ej: `$`, `€`). |
| `seriesType` | `string` | `bar`, `line`, `area` | Estilo de renderizado de la serie. Solo aplica en tipos `bar` y `combined`. |
| `showLabel` | `boolean` | `true \| false` | Muestra el valor directamente sobre cada punto/barra. |
| `labelPosition` | `string` | `top`, `inside`, `bottom`, `left`, `right` | Posición del label respecto al punto de datos. |
| `labelRotate` | `number` | `0–90` | Rotación en grados del label. |
| `decimalPlaces` | `number` | `0–6` | Decimales en el formateador de valores. Por defecto: `2`. |

### Parámetros de Dimensiones

| Campo | Descripción |
|---|---|
| `key` | Clave exacta de la dimensión en CubeJS. Ej: `Orders.status`. |
| `label` | Etiqueta visible en el eje X o columna de la tabla. |

### Parámetros de Dimensión de Tiempo (`timeDimension`)

| Campo | Valores válidos | Descripción |
|---|---|---|
| `dimension` | Cualquier campo fecha de CubeJS | Ej: `Orders.createdAt`. |
| `granularity` | `day`, `week`, `month`, `quarter`, `year` | Agrupación temporal de los datos. |

### Parámetros de Filtros

| Campo | Valores válidos | Descripción |
|---|---|---|
| `member` | `Cubo.campo` | Dimensión o medida sobre la que se filtra. |
| `operator` | `equals`, `notEquals`, `contains`, `gt`, `lt`, `gte`, `lte` | Operador de comparación. |
| `values` | `string[]` | Array de valores a comparar. |

---

## 3. Widget: Barras — `bar`

**Ícono:** 📊 · **Motor:** Apache ECharts

Muestra una o dos series de datos como barras verticales agrupadas. Ideal para comparar categorías o evolución temporal.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[n].label` | Etiqueta del eje X (categoría o período). |
| `data[n].value` | Valor de la primera medida (barra principal). |
| `data[n].value2` | Valor de la segunda medida (segunda barra). |

Se usa la primera medida para `value` y la segunda para `value2`. El sistema reconoce hasta **2 medidas** simultáneas.

### Comportamiento predeterminado

- Barras con `borderRadius: [4,4,0,0]` (esquinas superiores redondeadas).
- Ancho máximo de barra: `60 px`.
- Leyenda en la parte inferior (scroll si hay muchos ítems).
- Tooltip de eje completo con valores formateados.
- Si hay más de 8 categorías, las etiquetas del eje X se rotan 30°.

### Parámetros configurables

| Parámetro | Dónde se configura | Descripción |
|---|---|---|
| `measures[0].seriesType` | Datos → Medidas | Cambia la primera serie a `line` o `area` en lugar de `bar`. |
| `measures[1].seriesType` | Datos → Medidas | Cambia la segunda serie a `line` o `area`. |
| `measures[n].showLabel` | Datos → Medidas | Muestra etiquetas de valor sobre cada barra. |
| `measures[n].labelPosition` | Datos → Medidas | Posición del label: `top`, `inside`, `bottom`. |
| `measures[n].labelRotate` | Datos → Medidas | Rotación del label en grados. |
| `colorPalette` | Visualización | Paleta de colores aplicada a las series. |
| `chartOptions` | Visualización → JSON | Cualquier override de opciones ECharts. |

### Ejemplo mínimo

```json
{
  "title": "Ventas por mes",
  "chartType": "bar",
  "cubeQuery": {
    "measures": [{ "key": "Orders.totalRevenue", "label": "Ingresos", "color": "#1890ff", "format": "moneda", "currencyId": "usd" }],
    "timeDimension": { "dimension": "Orders.createdAt", "granularity": "month" },
    "limit": 12
  }
}
```

---

## 4. Widget: Líneas — `line`

**Ícono:** 📈 · **Motor:** Apache ECharts

Representa la evolución de una métrica a lo largo del tiempo o categorías. Incluye área semitransparente por defecto.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[n].label` | Etiqueta del eje X. |
| `data[n].value` | Valor de la primera (y única) medida. |

Este tipo usa **1 medida**. Si se configuran varias, solo se usa la primera.

### Comportamiento predeterminado

- Línea suave (`smooth: true`).
- Área semitransparente (opacidad 0.1) bajo la línea.
- Eje X sin `boundaryGap` (los datos comienzan desde el borde).
- Tooltip de eje.

### Parámetros configurables

| Parámetro | Dónde se configura | Descripción |
|---|---|---|
| `measures[0].showLabel` | Datos → Medidas | Muestra el valor sobre cada punto. |
| `measures[0].labelPosition` | Datos → Medidas | Posición del label respecto al punto. |
| `measures[0].color` | Datos → Medidas | Color de la línea y el área. |
| `colorPalette` | Visualización | Aplica el primer color de la paleta a la serie. |
| `chartOptions` | Visualización → JSON | Override de opciones ECharts. |

### Para eliminar el área rellena

```json
{ "series": [{ "areaStyle": null }] }
```

---

## 5. Widget: Pastel / Donut — `pie`

**Ícono:** 🥧 · **Motor:** Apache ECharts

Gráfico de anillo (donut) para representar la distribución proporcional de categorías.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[n].label` | Nombre de la categoría / segmento. |
| `data[n].value` | Valor del segmento. |

Usa **1 medida** (los colores de segmentos provienen de la paleta activa o de los colores predeterminados del sistema).

### Opciones específicas — `pieOptions`

Se configuran en la pestaña **Visualización → Opciones del gráfico Pie**.

```json
{
  "pieOptions": {
    "showValue":   false,
    "showPercent": true,
    "showTotal":   false
  }
}
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `showValue` | `boolean` | `false` | Muestra el valor absoluto en la etiqueta de cada segmento. |
| `showPercent` | `boolean` | `true` | Muestra el porcentaje en la etiqueta de cada segmento. |
| `showTotal` | `boolean` | `false` | Muestra el total de todos los segmentos en el centro del donut, junto al nombre de la medida. Cuando está activo, el radio interior se ajusta para dejar espacio al texto central. |

### Comportamiento predeterminado

- Radio interior: `35%`–`65%` (donut). Con `showTotal: true` se ajusta a `40%`–`68%`.
- Tooltip muestra nombre, valor formateado y porcentaje.
- Efecto hover con sombra en el segmento seleccionado.
- Leyenda scroll en la parte inferior.

### Ejemplo con total al centro

```json
{
  "title": "Distribución por región",
  "chartType": "pie",
  "cubeQuery": {
    "measures": [{ "key": "Orders.count", "label": "Pedidos", "format": "numero" }],
    "dimensions": [{ "key": "Orders.region", "label": "Región" }]
  },
  "pieOptions": { "showValue": false, "showPercent": true, "showTotal": true }
}
```

---

## 6. Widget: Gauge — `gauge`

**Ícono:** 🎯 · **Motor:** Apache ECharts

Marcador semicircular para visualizar un valor único en una escala 0–100. Ideal para KPIs de cumplimiento o porcentajes de avance.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[0].value` | Valor numérico entre 0 y 100 (representa el porcentaje del marcador). |
| `data[0].label` | Etiqueta mostrada debajo del marcador (generalmente el nombre de la medida). |

Solo se usa **el primer elemento** del array de datos y **1 medida**.

### Comportamiento predeterminado

- Escala fija: `min = 0`, `max = 100`.
- Zonas de color:
  - **Rojo** `#f5222d`: 0–30%.
  - **Amarillo** `#faad14`: 30–70%.
  - **Verde** `#52c41a`: 70–100%.
- El valor se muestra en el centro, formateado con `%`.
- No aplica paletas de color (los colores de zona son fijos).

### Personalización avanzada

Para cambiar el rango de la escala o los colores de zonas:

```json
{
  "series": [{
    "min": 0,
    "max": 200,
    "axisLine": {
      "lineStyle": {
        "color": [[0.5, "#f5222d"], [0.8, "#faad14"], [1, "#52c41a"]]
      }
    },
    "detail": { "formatter": "{value} km/h" }
  }]
}
```

---

## 7. Widget: Radar — `radar`

**Ícono:** 🕸️ · **Motor:** Apache ECharts

Gráfico de araña para comparar múltiples dimensiones de una misma entidad en un espacio poligonal.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[n].label` | Nombre del eje / dimensión del radar. |
| `data[n].value` | Valor en ese eje (se normaliza sobre `max = 100`). |

Cada fila de datos es un vértice del polígono. Usa **1 medida** y múltiples dimensiones (o múltiples filas).

### Comportamiento predeterminado

- `max = 100` para todos los indicadores (normalizado).
- Radio del polígono: `60%` del área.
- Área rellena con `opacity: 0.2`.
- Línea exterior con grosor 2.
- Tooltip por ítem.

### Personalización avanzada

Para configurar rangos distintos por eje (cuando los indicadores tienen escalas diferentes):

```json
{
  "radar": {
    "indicator": [
      { "name": "Ventas",     "max": 10000 },
      { "name": "Satisfacción", "max": 100 },
      { "name": "Tiempo",     "max": 60 }
    ]
  }
}
```

> **Nota:** Si se sobreescriben los `indicator` vía `chartOptions`, asegurarse de incluir todos los ejes en el mismo orden que los datos.

---

## 8. Widget: Combinado — `combined`

**Ícono:** 📉 · **Motor:** Apache ECharts

Combina barras y línea en el mismo gráfico, permitiendo comparar dos métricas con escalas posiblemente distintas. Es el único tipo que admite **eje Y secundario**.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[n].label` | Etiqueta del eje X. |
| `data[n].value` | Valor de la primera medida (por defecto: barras). |
| `data[n].value2` | Valor de la segunda medida (por defecto: línea). |

Requiere exactamente **2 medidas**.

### Opciones específicas — `combinedOptions`

Se configuran en **Visualización → Opciones del gráfico Combinado**.

```json
{
  "combinedOptions": {
    "showSecondaryYAxis": false
  }
}
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `showSecondaryYAxis` | `boolean` | `false` | Activa el eje Y derecho para la segunda serie. Útil cuando las dos métricas tienen escalas muy diferentes (ej: cantidad de unidades vs. ingresos). Cuando está activo, cada serie tiene su propio eje Y etiquetado con el nombre de la medida. |

### Parámetros de medidas aplicables

| Parámetro | Serie 1 (eje izq.) | Serie 2 (eje der.) |
|---|---|---|
| `seriesType` | `bar` (predeterminado), `line`, `area` | `line` (predeterminado), `bar`, `area` |
| `showLabel` | ✓ | ✓ |
| `color` | ✓ | ✓ |
| `format` | ✓ | ✓ |

### Ejemplo: Unidades vendidas vs. ingresos

```json
{
  "title": "Unidades vs Ingresos",
  "chartType": "combined",
  "cubeQuery": {
    "measures": [
      { "key": "Orders.count",        "label": "Unidades",  "seriesType": "bar",  "format": "numero" },
      { "key": "Orders.totalRevenue", "label": "Ingresos",  "seriesType": "line", "format": "moneda", "currencyId": "usd" }
    ],
    "timeDimension": { "dimension": "Orders.createdAt", "granularity": "month" }
  },
  "combinedOptions": { "showSecondaryYAxis": true }
}
```

---

## 9. Widget: Tabla — `table`

**Ícono:** 🗒️ · **Motor:** HTML nativo (no ECharts)

Presenta los datos en formato tabular con ordenamiento por columna y paginación.

### Fuente de datos

El widget tabla prioriza el campo `raw` del resultado de CubeJS (objeto con todas las columnas) sobre los campos simplificados `label`/`value`. Cuando hay datos de CubeJS reales, cada fila del resultado se muestra como una fila de tabla, con todas sus columnas.

En modo de datos de demostración, se simulan 50 filas con campos: `id`, `fecha`, `producto`, `región`, `estado`, `cantidad`, `precio`, `total`.

### Construcción de columnas

Las columnas se derivan automáticamente de la configuración `cubeQuery`:

1. Si hay `timeDimension`, se añade una columna de tiempo.
2. Las `dimensions` definidas generan columnas de texto (alineadas a la izquierda).
3. Las `measures` definidas generan columnas numéricas (alineadas a la derecha, formato localizado).
4. Si no hay configuración de CubeJS, las columnas se infieren de las claves del primer objeto de datos.

### Funciones interactivas

| Función | Descripción |
|---|---|
| **Ordenamiento** | Clic en cualquier cabecera alterna entre ascendente, descendente y sin orden. Las columnas numéricas se ordenan por valor; el resto por orden lexicográfico con `localeCompare('es')`. |
| **Paginación** | Controles de página en el pie: primera, anterior, siguiente, última. Indicador de rango visible: "1–20 de 50 filas". |
| **Filas por página** | Selector con opciones: 20, 25, 50, 100 filas. |

### Parámetros configurables

La tabla **no tiene** secciones de opciones propias (`pieOptions`, `combinedOptions`, `kpiOptions`). Su comportamiento se controla exclusivamente con `cubeQuery`.

| Configuración | Efecto |
|---|---|
| `dimensions` | Cada dimensión agrega una columna de texto. La etiqueta de columna proviene del campo `label`. |
| `measures` | Cada medida agrega una columna numérica. Los valores se formatean con separador de miles en español. |
| `timeDimension` | Añade una columna de fecha al inicio. La cabecera usa el nombre del campo (sin el cubo). |
| `limit` | Limita el número de filas devueltas por CubeJS. |

---

## 10. Widget: KPI — `kpi`

**Ícono:** 🔢 · **Motor:** HTML nativo (no ECharts)

Muestra un indicador de métricas de alto nivel con valor principal, tendencia respecto a un período anterior e indicador visual de color.

### Fuente de datos

| Campo de datos | Descripción |
|---|---|
| `data[0].value` | Valor actual (medida 1). |
| `data[0].value2` | Valor de comparación del período anterior (medida 2, opcional). |
| `data[0].label` | Etiqueta del período o dimensión. Suele no usarse directamente (se muestra el `title` del widget). |

La **tendencia** se calcula automáticamente:

```
tendencia (%) = ((valor_actual - valor_anterior) / |valor_anterior|) × 100
```

Si no se configura una segunda medida, la sección de tendencia no se muestra.

### Opciones específicas — `kpiOptions`

Se configuran en **Visualización → Opciones del KPI**.

```json
{
  "kpiOptions": {
    "icon":             "",
    "accentColor":      "",
    "invertTrend":      false,
    "showComparison":   true,
    "comparisonLabel":  "vs período anterior"
  }
}
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `icon` | `string` | `""` | Nombre de un **Material Symbol** (snake_case, sin espacios) o cualquier emoji. Se muestra en un chip de fondo translúcido junto a la etiqueta. Ejemplos: `trending_up`, `paid`, `directions_car`, `💰`. |
| `accentColor` | `string` | `""` | Color hexadecimal CSS que reemplaza el color primario de la barra superior y el icono. Si está vacío, usa `var(--primary)` (`#1890ff`). |
| `invertTrend` | `boolean` | `false` | Por defecto, un valor creciente (↑) se muestra en verde y uno decreciente (↓) en rojo. Con `invertTrend: true` se invierte la lógica: útil para métricas donde crecer es malo (ej: costo, tasa de devoluciones, tiempo de respuesta). |
| `showComparison` | `boolean` | `true` | Muestra u oculta la fila de tendencia (badge ↑↓ + etiqueta de comparación). |
| `comparisonLabel` | `string` | `"vs período anterior"` | Texto libre que acompaña al badge de tendencia. Ej: `"vs mes anterior"`, `"vs año 2024"`, `"vs presupuesto"`. |

### Formato del valor

El formato del valor principal se toma de `cubeQuery.measures[0].format`:

| `format` | Resultado |
|---|---|
| `numero` | Número localizado en español. Valores ≥ 1K abreviados (ej: `125.4K`). Valores ≥ 1M abreviados (ej: `1.25M`). |
| `moneda` | Símbolo de la moneda (`currencyId`) + valor abreviado. Ej: `$ 125.4K`, `€ 1.25M`. |
| `porcentaje` | Valor con 1 decimal + símbolo `%`. Ej: `87.3%`. |

### Diseño visual

```
┌──────────────────────────────────────────┐
│ [barra de acento — 3px]                   │
│                                           │
│  [ícono]  LABEL (en mayúsculas)           │
│                                           │
│  $1.25M                                   │
│                                           │
│  ↑ 12.4%   vs mes anterior                │
│                                           │
└──────────────────────────────────────────┘
```

### Colores del badge de tendencia

| Estado | Color del badge |
|---|---|
| Subida (positivo, normal) | Verde `#52c41a` |
| Bajada (negativo, normal) | Rojo `#f5222d` |
| Subida (positivo, invertido) | Rojo `#f5222d` |
| Bajada (negativo, invertido) | Verde `#52c41a` |

### Ejemplo completo

```json
{
  "title": "Ingresos del mes",
  "chartType": "kpi",
  "position": { "x": 0, "y": 0, "w": 3, "h": 2 },
  "cubeQuery": {
    "measures": [
      { "key": "Orders.totalRevenue", "label": "Ingresos", "format": "moneda", "currencyId": "usd" },
      { "key": "Orders.prevMonthRevenue", "label": "Mes anterior", "format": "moneda", "currencyId": "usd" }
    ],
    "limit": 1
  },
  "kpiOptions": {
    "icon": "paid",
    "accentColor": "#52c41a",
    "invertTrend": false,
    "showComparison": true,
    "comparisonLabel": "vs mes anterior"
  }
}
```

---

## 11. Personalización avanzada con `chartOptions`

Todos los tipos basados en ECharts (`bar`, `line`, `pie`, `gauge`, `radar`, `combined`) aceptan un campo `chartOptions` con opciones libres de la [API de ECharts v5](https://echarts.apache.org/en/option.html).

Las opciones se **fusionan** sobre la configuración predeterminada usando `deepMerge`. Los arrays siempre reemplazan (no se concatenan).

### Reglas de fusión

- Los **objetos** se mezclan recursivamente (profundidad máxima: 10 niveles).
- Los **arrays** reemplazan completamente el array base.
- Los valores `null` anulan la propiedad del objeto base.

### Casos de uso frecuentes

**Mostrar valores dentro de las barras:**
```json
{
  "series": [{ "label": { "show": true, "position": "inside", "color": "#fff" } }]
}
```

**Cambiar el formato del tooltip del gauge:**
```json
{
  "series": [{ "detail": { "formatter": "{value} unidades" } }]
}
```

**Añadir líneas de referencia:**
```json
{
  "series": [{
    "markLine": {
      "data": [{ "yAxis": 5000, "name": "Objetivo" }]
    }
  }]
}
```

**Rotar etiquetas del eje X:**
```json
{
  "xAxis": { "axisLabel": { "rotate": 45 } }
}
```

**Ocultar leyenda:**
```json
{
  "legend": { "show": false }
}
```

### IA Assist

El modal de configuración incluye un panel **IA Assist** (pestaña Visualización) que genera automáticamente `chartOptions` a partir de una descripción en lenguaje natural. Requiere una clave de API configurada en **Configuración → LLM**.

---

## 12. Paletas de colores

El sistema resuelve el color de cada serie en el siguiente orden de precedencia:

```
widget.colorPalette  →  dashboardPalette  →  paletteStore.defaultPaletteId  →  COLORES_SISTEMA
```

| Valor de `colorPalette` | Comportamiento |
|---|---|
| `null` (por defecto) | Hereda la paleta configurada en el dashboard padre. |
| `"none"` | No aplica ninguna paleta; cada medida usa su `color` individual. |
| `"<palette-id>"` | Aplica la paleta específica del widget, ignorando la del dashboard. |

Los colores del sistema (cuando no hay paleta):
`#1890ff · #52c41a · #faad14 · #f5222d · #722ed1 · #13c2c2 · #fa8c16 · #eb2f96 · #2f54eb · #a0d911`

> **Nota:** En el widget `kpi` el color de la paleta **no aplica** al valor principal. El color de acento del KPI se configura exclusivamente con `kpiOptions.accentColor`.

---

## 13. Datos de demostración (`useMockData`)

Cuando `useMockData: true` o cuando no hay conexión a CubeJS (sin token o sin URL), el sistema genera datos simulados por tipo de widget. Los datos de demostración son aleatorios y cambian en cada recarga.

| `chartType` | Datos simulados |
|---|---|
| `bar`, `line`, `combined` | 8 meses (Ene–Ago) con `value` ∈ [2000, 10000] y `value2` ∈ [1000, 6000]. |
| `pie` | 5 categorías (Electrónica, Ropa, Hogar, Deportes, Libros) con `value` ∈ [100, 600]. |
| `gauge` | 1 valor ∈ [50, 90]. |
| `radar` | 5 regiones (Norte, Sur, Este, Oeste, Centro) con `value` ∈ [20, 100]. |
| `table` | 50 filas con campos: id, fecha, producto, región, estado, cantidad, precio, total. |
| `kpi` | 1 fila con `value` ∈ [100K, 1M] y `value2` ∈ [100K, 1M] (para calcular la tendencia). |

---

*Generado automáticamente a partir del código fuente de Dashboard Studio.*
