# Feature: Integración CubeJS

## Descripción general

CubeJS actúa como **capa semántica** entre los dashboards y la base de datos subyacente. La aplicación se conecta a una API CubeJS para cargar el schema (cubos, medidas, dimensiones) y ejecutar consultas analíticas.

## Configuración

### Desde la UI

1. Menú lateral → **Configuración**
2. Sección **Conexión CubeJS**
3. Ingresar **URL de la API** (ej: `http://localhost:4000/cubejs-api/v1`)
4. Ingresar **Token JWT**
5. Clic en **Probar conexión** → valida cargando el meta-schema

### Variables de entorno (`.env`)

```env
VITE_CUBEJS_API_URL=http://localhost:4000/cubejs-api/v1
VITE_CUBEJS_TOKEN=<jwt-token>
```

Las variables de entorno se leen al iniciar la app si no hay configuración en localStorage.

## Composable `useCubeQuery`

**Archivo:** `src/composables/useCubeQuery.js`

Composable de Vue para obtener datos de CubeJS o generar datos simulados.

### Uso

```javascript
const { data, loading, error, lastUpdated, fetchData } =
  useCubeQuery(widget, dashboardFiltersRef)
```

### Parámetros

| Parámetro | Tipo | Descripción |
|---|---|---|
| `widget` | `Object` | Configuración del widget (cubeQuery, chartType, useMockData) |
| `dashboardFiltersRef` | `Ref<Array>` | Filtros activos del dashboard |

### Retorna

| Campo | Tipo | Descripción |
|---|---|---|
| `data` | `Ref<Array>` | Datos en formato `[{ label, value, value2? }]` |
| `loading` | `Ref<boolean>` | Estado de carga |
| `error` | `Ref<string\|null>` | Mensaje de error |
| `lastUpdated` | `Ref<Date\|null>` | Última actualización |
| `fetchData()` | `Function` | Fuerza una nueva obtención de datos |

### Lógica de decisión

```
fetchData()
  │
  ├── useMockData === true ?
  │   └── generateMockData(chartType) → data
  │
  ├── !cubeStore.isConfigured ?
  │   └── generateMockData(chartType) → data
  │
  └── ejecutar query CubeJS
        ├── construir query desde widget.cubeQuery + dashboardFilters
        ├── cubeStore.executeQuery(query)
        └── transformar ResultSet → [{ label, value }]
              ├── success → data
              └── error   → error message + fallback mock data
```

### Construcción de la query

```javascript
{
  measures: widget.cubeQuery.measures.map(m => m.key),
  dimensions: widget.cubeQuery.dimensions.map(d => d.key),
  timeDimensions: widget.cubeQuery.timeDimension
    ? [{ dimension: td.dimension, granularity: td.granularity }]
    : [],
  filters: [
    ...widget.cubeQuery.filters,
    ...dashboardFilters   // filtros a nivel de dashboard
  ],
  limit: widget.cubeQuery.limit || 1000
}
```

### Transformación del resultado

```javascript
// CubeJS TablePivot → formato interno
resultSet.tablePivot().map(row => ({
  label: row[firstDimension] || row[timeDimension],
  value: parseFloat(row[firstMeasure] || 0),
  value2: parseFloat(row[secondMeasure] || 0)  // para combined
}))
```

## Datos simulados (mock data)

Cuando no hay conexión CubeJS (o `useMockData = true`), se generan datos realistas por tipo de gráfico:

| Chart Type | Mock generado |
|---|---|
| `bar` | 6 categorías con valores entre 500–5000 |
| `line` | 8 meses con tendencia ascendente |
| `pie` | 5 sectores con porcentajes distribuidos |
| `gauge` | Un único valor entre 0–100 |
| `radar` | 5 ejes con valores normalizados |
| `combined` | 6 meses con dos series numéricas |

Los datos simulados tienen nombres y valores aleatorios pero coherentes con el tipo de gráfico.

## Función `buildCubeFilter`

```javascript
buildCubeFilter(filterDef, activeValue)
```

Convierte la definición de un filtro de dashboard y su valor activo en uno o más objetos de filtro CubeJS:

| Tipo | Operador CubeJS generado |
|---|---|
| `string` | `{ member, operator: 'equals', values: [value] }` |
| `time` | `{ member, operator: 'inDateRange', values: [from, to] }` |
| `number` (min) | `{ member, operator: 'gte', values: [min] }` |
| `number` (max) | `{ member, operator: 'lte', values: [max] }` |

## Función `downloadCSV`

```javascript
downloadCSV(data, filename)
```

Genera y descarga un archivo CSV a partir del array de datos. El archivo tiene columnas `label`, `value` (y `value2` si existe).

## Meta-schema

Al conectar a CubeJS, se carga el schema con todos los cubos disponibles:

```javascript
// Estructura del meta-schema
{
  cubes: [
    {
      name: 'Orders',
      measures: [
        { name: 'Orders.count', title: 'Count', type: 'count' },
        { name: 'Orders.revenue', title: 'Revenue', type: 'sum' }
      ],
      dimensions: [
        { name: 'Orders.status', title: 'Status', type: 'string' },
        { name: 'Orders.createdAt', title: 'Created At', type: 'time' }
      ]
    }
  ]
}
```

El schema se carga una vez y se cachea en el store. Se puede recargar desde **Configuración → Recargar schema**.

## Operadores de filtro disponibles

| Operador | Descripción |
|---|---|
| `equals` | Igual a |
| `notEquals` | Distinto de |
| `contains` | Contiene (texto) |
| `startsWith` | Empieza con |
| `endsWith` | Termina con |
| `gt` | Mayor que |
| `gte` | Mayor o igual que |
| `lt` | Menor que |
| `lte` | Menor o igual que |
| `inDateRange` | En rango de fechas |
| `beforeDate` | Antes de fecha |
| `afterDate` | Después de fecha |
| `set` | Tiene valor (no nulo) |
| `notSet` | No tiene valor (nulo) |
