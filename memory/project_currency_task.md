---
name: Tarea pendiente - Monedas en Configurar Métrica
description: Implementar selector de moneda en ChartConfigModal cuando Formato = Moneda
type: project
---

## Tarea: Monedas en "Configurar Métrica"

**Why:** El usuario quiere que al seleccionar Formato "Moneda" en una medida del widget, aparezca un selector de moneda definida en BD.

**Estado:** Investigación completada, implementación pendiente.

### Lo que se sabe

**Backend pattern:** Seguir exactamente `backend/app/api/endpoints/data_types.py`

**Archivos a crear/modificar:**

#### 1. Backend — Migration nueva
- Archivo: `backend/alembic/versions/005_add_currencies_table.py`
- Tabla: `currencies` con columnas: `id` (VARCHAR PK), `code` (VARCHAR 10), `symbol` (VARCHAR 10), `name` (VARCHAR 100), `is_active` (BOOLEAN default True)

#### 2. Backend — SQLAlchemy model
- Archivo: `backend/app/models/models.py`
- Agregar clase `Currency` similar a `DataType`

#### 3. Backend — Schema
- Archivo: `backend/app/schemas/schemas.py`
- Agregar: `CurrencyBase`, `CurrencyResponse`

#### 4. Backend — Endpoint
- Archivo: `backend/app/api/endpoints/currencies.py`
- Solo GET (read-only para frontend)
- Seed con defaults si tabla vacía:
  - `{ id: "cur-usd", code: "USD", symbol: "US$", name: "United States Dollar" }`
  - `{ id: "cur-pen-sol", code: "PEN", symbol: "S/", name: "Sol Peruano" }`
- Registrar en `backend/app/main.py`

#### 5. Frontend — API service
- Archivo: `dashboard-app/src/services/api.js`
- Agregar `currenciesApi = { async getAll() { return apiRequest('/api/v1/currencies/') } }`

#### 6. Frontend — Store
- Archivo: `dashboard-app/src/stores/currencies.js`
- Simple store: state `{ currencies: [] }`, action `loadFromBackend()`

#### 7. Frontend — ChartConfigModal.vue
- En cada `measure-row` agregar:
  - Select "Formato": `['numero', 'moneda', 'porcentaje']`
  - Si formato === 'moneda': select de monedas del store
- Guardar en `measure.format` y `measure.currencyId`
- El model `cubeQuery.measures` pasa de `{ key, label, color, seriesType }` a `{ key, label, color, seriesType, format, currencyId }`

#### 8. Frontend — EChartWrapper.vue (opcional futuro)
- El `format` y `currencyId` en measures se puede usar para formatear tooltips/labels con el símbolo de moneda

### Seed SQL equivalente
```python
DEFAULT_CURRENCIES = [
    {"id": "cur-usd",     "code": "USD", "symbol": "US$", "name": "United States Dollar"},
    {"id": "cur-pen-sol", "code": "PEN", "symbol": "S/",  "name": "Sol Peruano"},
]
```

**How to apply:** Continuar en nueva conversación con contexto limpio. El trabajo está en `feature/backend`.
