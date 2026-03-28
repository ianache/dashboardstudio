# Store: cubejs

**Archivo:** `src/stores/cubejs.js`

Gestiona la conexión y comunicación con la API de CubeJS.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `apiUrl` | `string` | URL base de la API (ej: `http://localhost:4000/cubejs-api/v1`) |
| `token` | `string` | JWT para autenticación |
| `meta` | `object \| null` | Schema cargado (cubes, measures, dimensions) |
| `metaLoaded` | `boolean` | Indica si el schema fue cargado exitosamente |
| `cubeClient` | `object \| null` | Instancia del cliente `@cubejs-client/core` |

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `isConfigured` | `boolean` | `true` si hay apiUrl y token configurados |
| `cubes` | `array` | Lista de cubos del schema |
| `getMeasures(cubeName)` | `array` | Medidas de un cubo específico |
| `getDimensions(cubeName)` | `array` | Dimensiones de un cubo específico |
| `getAllMeasures` | `array` | Todas las medidas de todos los cubos |
| `getAllDimensions` | `array` | Todas las dimensiones de todos los cubos |

## Acciones

### `setConfig(apiUrl, token)`

Guarda la configuración en localStorage y recrea el cliente CubeJS.

```javascript
await cubeStore.setConfig('http://localhost:4000/cubejs-api/v1', 'mi-jwt-token')
```

### `loadMeta()`

Carga el schema de CubeJS (`/cubejs-api/v1/meta`). Lanza error si la conexión falla.

```javascript
await cubeStore.loadMeta()
// cubeStore.meta ahora tiene los cubos disponibles
```

### `executeQuery(query)`

Ejecuta una query CubeJS y retorna el resultado en formato `ResultSet`.

```javascript
const resultSet = await cubeStore.executeQuery({
  measures: ['Orders.count'],
  dimensions: ['Orders.status'],
  limit: 100
})
const data = resultSet.tablePivot()
```

### `testConnection()`

Prueba la conexión llamando a `loadMeta()`. Retorna `{ success: boolean, message: string }`.

### `getDimensionValues(member)`

Carga valores únicos de una dimensión (para listas de filtros). Usa caché interna para no repetir llamadas.

```javascript
const values = await cubeStore.getDimensionValues('Orders.status')
// ['completed', 'processing', 'shipped']
```

### `initFromStorage()`

Restaura configuración desde localStorage al iniciar la app.

## Formato de query CubeJS

```javascript
{
  measures: ['Orders.revenue', 'Orders.count'],
  dimensions: ['Orders.status'],
  timeDimensions: [{
    dimension: 'Orders.createdAt',
    granularity: 'month'
  }],
  filters: [{
    member: 'Orders.status',
    operator: 'equals',
    values: ['completed']
  }],
  limit: 1000
}
```

## Transformación de datos

El `ResultSet` de CubeJS se transforma en `useCubeQuery.js` al formato que consume `EChartWrapper`:

```javascript
// Resultado CubeJS → formato interno
resultSet.tablePivot().map(row => ({
  label: row[dimension],
  value: parseFloat(row[measure1]),
  value2: parseFloat(row[measure2])  // para gráficos combinados
}))
```

## Persistencia

- `localStorage['cubeApiUrl']`
- `localStorage['cubeToken']`
