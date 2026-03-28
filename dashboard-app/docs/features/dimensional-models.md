# Feature: Modelos Dimensionales

## Descripción general

El módulo de Modelos Dimensionales permite diseñar visualmente esquemas de tipo **star schema** y **snowflake** con tablas de hechos, dimensiones y relaciones. Incluye exportación a DDL SQL y esquemas CubeJS.

## Vistas involucradas

| Vista | Ruta | Descripción |
|---|---|---|
| `DimensionalModelListView` | `/models` | Lista y gestión de modelos |
| `DimensionalModelEditorView` | `/models/:id` | Editor canvas del modelo |
| `DataTypesView` | `/models/data-types` | Biblioteca de tipos SQL |

---

## Lista de modelos (`/models`)

### Modelo Global

Al entrar a la lista, `ensureGlobalModel()` garantiza que siempre existe un modelo marcado como **GLOBAL**. Este modelo es especial:

- Marcado con badge violeta `GLOBAL`
- No puede eliminarse
- Contiene dimensiones compartidas reutilizables en otros modelos

### Tarjeta de modelo

Cada tarjeta muestra:
- Icono y nombre del modelo (editable con clic)
- Descripción (editable con clic)
- Badges: nº de tablas de hechos, dimensiones, relaciones
- Botones: Editar, Eliminar (no disponible para Global)

### Edición inline

- Clic en el nombre → input de texto
- Clic en la descripción → textarea
- Enter o blur guardan el cambio; Escape lo cancela

### Crear nuevo modelo

- Botón **"Nuevo Modelo"** o link en sidebar
- Modal con nombre (obligatorio) y descripción
- Al crear → navega directamente al editor

---

## Editor de modelo (`/models/:id`)

### Toolbar

```
[← Volver]  [Nombre ✏]  [■ CubeJS] [⬡ DDL] [⬆ Import YAML] [⬇ Export YAML]  [+ Hecho] [+ Dimensión] [🌐 + Dim. Global]
```

| Botón | Descripción |
|---|---|
| **← Volver** | Navega a `/models` |
| **Nombre** | Doble clic para editar; Enter/blur para guardar |
| **CubeJS** | Exporta todos los cubos como `.js` individuales en un ZIP |
| **DDL** | Genera sentencias `CREATE TABLE` en un archivo `.ddl` |
| **Import YAML** | Carga un modelo desde archivo YAML exportado previamente |
| **Export YAML** | Exporta el modelo actual a YAML para respaldo |
| **+ Hecho** | Añade una tabla de hechos al canvas |
| **+ Dimensión** | Añade una tabla de dimensión al canvas |
| **+ Dim. Global** | (Solo si no es el modelo Global) Abre modal para añadir dimensiones del modelo Global como referencias de solo lectura |

### Canvas

El canvas es un área con scroll donde los nodos se posicionan como elementos `div` con `position: absolute`. Las relaciones se dibujan como líneas SVG sobre el canvas.

#### Nodo de tabla

```
┌─────────────────────────┐  ← fact: azul / dimension: verde
│ [HECHO] ventas_hechos   │
├─────────────────────────┤
│ ⠿ 🔑 id_venta  serial  │  ← ⠿ es el drag handle (solo dims)
│    🔗 id_cliente int   │  ← FK generada automáticamente
│    #  total    numeric │
│    +  Añadir campo     │
└─────────────────────────┘
```

- **Icono ⠿**: solo en campo llave de dimensión; se arrastra hacia una tabla de hechos para crear relación + FK
- **Icono 🔑**: campo llave primaria
- **Icono 🔗**: campo llave foránea
- **Nodos Global ref**: borde punteado violeta, icono 🌐 en header, campos en solo lectura

#### Crear relación con drag-and-drop

1. Localiza el campo llave (🔑) de una dimensión
2. Arrastra el handle ⠿ hacia una tabla de hechos
3. Al soltar:
   - Se crea automáticamente un campo FK en la tabla de hechos con nombre `{dim}_{campo_llave}` y descripción `FK → DimName.fieldName`
   - Se añade una relación `1:N` entre los nodos
   - La línea SVG aparece en el canvas

#### Selección de nodos y relaciones

- **Clic en nodo**: abre el panel de propiedades con los campos editables
- **Clic en línea de relación**: abre panel de propiedades con cardinalidad
- **Clic en canvas vacío**: deselecciona

### Panel de propiedades (derecha)

El panel aparece a la derecha del canvas cuando hay un nodo o relación seleccionado.

#### Panel de nodo (fact / dimension)

```
[Tabla de Hecho]               [■ CubeJS]  [✕]
─────────────────────────────────────────────
Nombre: [__________________________]

CAMPOS                                    [≡ desc]
┌──────────────────────────────────────────────┐
│🔑  [nombre_campo]  [tipo ▾]              [✕] │
│    [descripción...]                           │ ← toggleable
├──────────────────────────────────────────────┤
│    [campo_fk    ]  [tipo ▾]              [✕] │
└──────────────────────────────────────────────┘
[+ Añadir campo]
─────────────────────────────────────────────
[Eliminar tabla]
```

- **🔑 toggle**: clic para marcar/desmarcar campo como llave primaria
- **Tipo**: selector de tipos del `dataTypes` store
- **≡ desc**: muestra/oculta fila de descripción (oculta por defecto)
- **CubeJS ■**: exporta solo este cubo como archivo `.js`

#### Panel de nodo (referencia global — solo lectura)

```
[Dimensión]  [Global]       [■ CubeJS]  [✕]
────────────────────────────────────────────
🌐 Dimensión del modelo Global — solo lectura

CAMPOS
  🔑 id         serial
  A  nombre     varchar
  A  país       varchar

[Quitar del modelo]
```

#### Panel de relación

```
[Relación]                              [✕]
───────────────────────────────────────────
  dim_cliente  →  fct_ventas

Cardinalidad: [1:N ▾]
───────────────────────────────────────────
[Eliminar relación]
```

---

## Modelo Global — Dimensiones compartidas

### Concepto

El modelo Global actúa como biblioteca central. Sus dimensiones se pueden incluir como referencias de solo lectura en cualquier otro modelo:

```
Modelo Global
├── dim_cliente   ← definición maestra
└── dim_tiempo    ← definición maestra

Modelo Ventas
├── fct_ventas
├── dim_cliente [🌐 referencia] → campos vienen del modelo Global
└── dim_tiempo  [🌐 referencia] → campos vienen del modelo Global
```

### Añadir dimensión global

1. En el editor de un modelo no-Global, clic en **"+ Dim. Global"**
2. Modal muestra las dimensiones del modelo Global que aún no están referenciadas
3. Seleccionar una o más (checkbox) → **Añadir**
4. Los nodos aparecen en el canvas con borde punteado violeta

Las referencias se resuelven en tiempo real: si cambias un campo en el modelo Global, todos los modelos que lo referencian lo ven inmediatamente (sin necesidad de actualizar).

---

## Exportación DDL / SQL

El botón DDL genera sentencias `CREATE TABLE` en PostgreSQL:

```sql
-- ============================================================
-- Modelo Dimensional: Ventas
-- Generado: 2026-03-28T10:00:00.000Z
-- ============================================================

-- TABLAS DE DIMENSIONES
CREATE TABLE dim_cliente (
    id_cliente                     SERIAL PRIMARY KEY,
    nombre                         VARCHAR(255),  -- Nombre completo
    pais                           VARCHAR(100)
);

-- TABLAS DE HECHOS
CREATE TABLE fct_ventas (
    id_venta                       SERIAL PRIMARY KEY,
    dim_cliente_id_cliente         INTEGER,       -- FK → dim_cliente.id_cliente
    total                          NUMERIC(10,2),
    CONSTRAINT fk_fct_ventas_dim_cliente_id_cliente
        FOREIGN KEY (dim_cliente_id_cliente) REFERENCES dim_cliente(id_cliente)
);
```

### Reglas de tipos para FK

Los campos FK no pueden usar `SERIAL`/`BIGSERIAL` (que crean secuencias). La función `pgTypeForCol(field)` los convierte:

| Tipo original | Tipo en FK |
|---|---|
| `SERIAL` | `INTEGER` |
| `BIGSERIAL` | `BIGINT` |

---

## Exportación CubeJS

### Cubo por tabla

El botón **CubeJS** genera un ZIP con un archivo `.js` por cada tabla del modelo. El botón **■** en el panel de propiedades exporta solo el cubo de la tabla seleccionada.

### Nombre del cubo

El nombre del cubo se deriva del nombre de la tabla eliminando prefijos comunes y convirtiendo a PascalCase:

| Nombre tabla | Cubo generado |
|---|---|
| `dim_cliente` | `Cliente` |
| `fct_ventas` | `Ventas` |
| `fact_orders` | `Orders` |
| `stg_productos` | `Productos` |

### Estructura generada — Dimensión

```javascript
cube(`Cliente`, {
  sql_table: `dim_cliente`,

  measures: {
    count: { type: `count` },
  },

  dimensions: {
    idCliente: {
      sql: `${CUBE}.id_cliente`,
      type: `number`,
      primary_key: true,
    },
    nombre: {
      sql: `${CUBE}.nombre`,
      type: `string`,
      title: `Nombre completo`,
    },
  },
});
```

### Estructura generada — Tabla de hechos

```javascript
cube(`Ventas`, {
  sql_table: `fct_ventas`,

  joins: {
    Cliente: {
      sql: `${CUBE}.dim_cliente_id_cliente = ${Cliente}.id_cliente`,
      relationship: `many_to_one`,
    },
  },

  measures: {
    count: { type: `count` },
    total: {
      sql: `${CUBE}.total`,
      type: `sum`,
    },
  },

  dimensions: {
    idVenta: {
      sql: `${CUBE}.id_venta`,
      type: `number`,
      primary_key: true,
    },
  },

  pre_aggregations: {
    main: {
      type: `rollup`,
      measures: [CUBE.count, CUBE.total],
      refresh_key: { every: `1 hour` },
    },
  },
});
```

---

## Import / Export YAML

### Exportar

El botón **Export YAML** genera un archivo `nombre-modelo.yaml` con la estructura completa del modelo.

```yaml
name: Ventas
description: Modelo de ventas por cliente
nodes:
  - id: abc123
    type: fact
    name: fct_ventas
    x: 200
    y: 100
    fields:
      - id: def456
        name: id_venta
        dataType: dt-serial
        isKey: true
        isFk: false
        description: ''
relationships:
  - id: rel001
    fromNodeId: dim001
    toNodeId: fct001
    cardinality: 1:N
```

### Importar

El botón **Import YAML** reemplaza el contenido del modelo actual con el del archivo seleccionado. Los IDs del archivo se usan tal cual (se preservan referencias entre nodos y relaciones).

> Al importar, los nodos con `globalRef` no se restauran automáticamente como referencias vivas al modelo Global — son solo nodos normales en el YAML. Para trabajar con dimensiones globales, añadirlas desde el botón **"+ Dim. Global"**.
