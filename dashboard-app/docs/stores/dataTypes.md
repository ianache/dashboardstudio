# Store: dataTypes

**Archivo:** `src/stores/dataTypes.js`

Gestiona la biblioteca de tipos de datos SQL personalizados, usados en los campos de los modelos dimensionales.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `types` | `array` | Lista de tipos de datos (cargada desde localStorage) |

## Modelo de tipo de dato

```javascript
{
  id: string,           // Identificador único (ej: 'dt-varchar', 'dt-numeric')
  name: string,         // Nombre descriptivo (ej: 'Texto corto')
  baseType: string,     // Tipo base PostgreSQL (ej: 'VARCHAR', 'NUMERIC')
  size: number | null,  // Longitud para tipos con hasSize (ej: 255 para VARCHAR)
  precision: number | null,  // Precisión para tipos con hasPrecision
  scale: number | null,      // Escala para tipos decimales
}
```

## Tipos base disponibles

| Base | hasSize | hasPrecision | Ejemplo SQL |
|---|---|---|---|
| `VARCHAR` | Sí | No | `VARCHAR(255)` |
| `CHAR` | Sí | No | `CHAR(10)` |
| `TEXT` | No | No | `TEXT` |
| `INTEGER` | No | No | `INTEGER` |
| `BIGINT` | No | No | `BIGINT` |
| `SMALLINT` | No | No | `SMALLINT` |
| `SERIAL` | No | No | `SERIAL` |
| `BIGSERIAL` | No | No | `BIGSERIAL` |
| `NUMERIC` | No | Sí | `NUMERIC(10,2)` |
| `DECIMAL` | No | Sí | `DECIMAL(10,2)` |
| `REAL` | No | No | `REAL` |
| `DOUBLE PRECISION` | No | No | `DOUBLE PRECISION` |
| `MONEY` | No | No | `MONEY` |
| `BOOLEAN` | No | No | `BOOLEAN` |
| `DATE` | No | No | `DATE` |
| `TIME` | No | No | `TIME` |
| `TIMESTAMP` | No | No | `TIMESTAMP` |
| `TIMESTAMPTZ` | No | No | `TIMESTAMPTZ` |
| `UUID` | No | No | `UUID` |
| `JSONB` | No | No | `JSONB` |
| `JSON` | No | No | `JSON` |
| `BYTEA` | No | No | `BYTEA` |

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `allTypes` | `array` | Todos los tipos definidos |
| `getById(id)` | `object \| null` | Tipo por ID |
| `sqlOf(id)` | `string` | Cadena SQL completa del tipo (ej: `'VARCHAR(255)'`); si no existe, retorna el ID como fallback |

## Acciones

| Acción | Descripción |
|---|---|
| `addType(typeData)` | Crea un nuevo tipo; retorna el objeto creado |
| `updateType(id, patch)` | Actualiza un tipo existente |
| `deleteType(id)` | Elimina un tipo |
| `restoreDefaults()` | Restaura los 14 tipos predefinidos (reemplaza la lista actual) |

## Función `sqlTypeString(dt)`

Función pura que genera la cadena SQL a partir de un objeto tipo:

```javascript
sqlTypeString({ baseType: 'VARCHAR', size: 100 })   // → 'VARCHAR(100)'
sqlTypeString({ baseType: 'NUMERIC', precision: 10, scale: 2 }) // → 'NUMERIC(10,2)'
sqlTypeString({ baseType: 'BOOLEAN' })               // → 'BOOLEAN'
```

## Tipos predefinidos (por defecto)

| ID | Nombre | SQL |
|---|---|---|
| `dt-serial` | ID Autonumérico | `SERIAL` |
| `dt-bigserial` | ID Grande Autonumérico | `BIGSERIAL` |
| `dt-int` | Entero | `INTEGER` |
| `dt-bigint` | Entero Grande | `BIGINT` |
| `dt-smallint` | Entero Pequeño | `SMALLINT` |
| `dt-numeric` | Numérico (10,2) | `NUMERIC(10,2)` |
| `dt-decimal` | Decimal (10,4) | `DECIMAL(10,4)` |
| `dt-money` | Dinero | `MONEY` |
| `dt-varchar` | Texto Corto | `VARCHAR(255)` |
| `dt-text` | Texto Largo | `TEXT` |
| `dt-boolean` | Booleano | `BOOLEAN` |
| `dt-date` | Fecha | `DATE` |
| `dt-timestamp` | Fecha y Hora | `TIMESTAMP` |
| `dt-uuid` | UUID | `UUID` |

## Relación con modelos dimensionales

Cada campo de un nodo (tabla de hecho o dimensión) tiene un `dataType` que referencia el `id` de un tipo de este store. La función `pgTypeForCol(field)` en el editor resuelve el SQL correcto con las siguientes reglas especiales:

- `SERIAL` en columna FK → se convierte a `INTEGER` (las secuencias no son válidas como FK)
- `BIGSERIAL` en columna FK → se convierte a `BIGINT`

## Persistencia

`localStorage['dataTypes']` — array de tipos.
