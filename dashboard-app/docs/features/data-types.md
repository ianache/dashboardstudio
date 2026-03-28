# Feature: Tipos de Datos

## Descripción general

La sección **Tipos de Datos** (`/models/data-types`) permite gestionar una biblioteca de tipos de datos SQL personalizados que se usan al definir campos en los modelos dimensionales.

## Propósito

En lugar de asignar tipos SQL en texto libre (con riesgo de errores), los campos de las tablas referencian un tipo de datos con ID. Esto permite:

- Garantizar consistencia en los nombres de tipos a lo largo del modelo
- Generar DDL correcto con tamaños, precisiones y escalas configuradas
- Distinguir tipos con reglas especiales (ej: `SERIAL` → `INTEGER` en FK)

## Vista (`DataTypesView`)

La vista muestra una tabla con todos los tipos definidos:

| ID | Nombre | Tipo base | Tamaño | Precisión | Escala | SQL resultante | Acciones |
|---|---|---|---|---|---|---|---|
| dt-serial | ID Autonumérico | SERIAL | — | — | — | `SERIAL` | ✏ 🗑 |
| dt-varchar | Texto Corto | VARCHAR | 255 | — | — | `VARCHAR(255)` | ✏ 🗑 |
| dt-numeric | Numérico | NUMERIC | — | 10 | 2 | `NUMERIC(10,2)` | ✏ 🗑 |

### Añadir tipo

Formulario inline o modal con:
- **Nombre** (descriptivo, ej: "Precio unitario")
- **Tipo base** (selector con los 22 tipos PostgreSQL disponibles)
- **Tamaño** (solo si el tipo base tiene `hasSize = true`, ej: VARCHAR)
- **Precisión y Escala** (solo si tiene `hasPrecision = true`, ej: NUMERIC)

### Editar tipo

Clic en ✏ convierte la fila en editable inline. Los cambios se propagan inmediatamente a todos los campos que usen ese tipo (la referencia es por ID).

### Eliminar tipo

Clic en 🗑 → confirmación → elimina el tipo. Los campos que lo usaban mantienen el ID como valor crudo (se mostrará el ID en lugar del nombre hasta que se reasigne).

### Restaurar predeterminados

Botón **"Restaurar predeterminados"** reemplaza todos los tipos con los 14 tipos estándar del sistema.

## Integración con el editor de modelos

En el panel de propiedades del editor de modelo, el selector de tipo de campo muestra los nombres de los tipos del store:

```html
<select v-model="field.dataType">
  <option v-for="dt in dtStore.allTypes" :key="dt.id" :value="dt.id">
    {{ dt.name }}
  </option>
</select>
```

El valor guardado en el campo es el `id` del tipo (ej: `'dt-numeric'`), no el string SQL.

## Resolución de tipos en DDL

La función `pgTypeForCol(field)` en el editor resuelve el tipo SQL final:

```javascript
function pgTypeForCol(field) {
  const dt = dtStore.getById(field.dataType)
  if (dt) {
    // SERIAL/BIGSERIAL no son válidos en columnas FK
    if (field.isFk) {
      if (dt.baseType === 'SERIAL')    return 'INTEGER'
      if (dt.baseType === 'BIGSERIAL') return 'BIGINT'
    }
    return dtStore.sqlOf(field.dataType)  // → 'NUMERIC(10,2)', etc.
  }
  // Fallback para valores legacy en texto libre
  return normalizePgType(field.dataType)
}
```

## Tipos predeterminados

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
