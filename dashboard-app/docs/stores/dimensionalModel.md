# Store: dimensionalModel

**Archivo:** `src/stores/dimensionalModel.js`

Gestiona los modelos dimensionales (star schema / snowflake): sus tablas de hechos, dimensiones, campos y relaciones. Incluye soporte para un **modelo Global** con dimensiones compartidas.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `models` | `array` | Lista de modelos dimensionales (cargada desde localStorage) |

## Modelo de datos

### Model

```javascript
{
  id: string,
  name: string,
  description: string,
  isGlobal: boolean,          // true → modelo Global (único, compartido)
  createdBy: string,
  createdAt: ISO string,
  updatedAt: ISO string,
  nodes: Node[],
  relationships: Relationship[]
}
```

### Node (tabla de hecho o dimensión)

```javascript
{
  id: string,
  type: 'fact' | 'dimension',
  name: string,
  x: number,                  // posición en canvas (px)
  y: number,
  globalRef: null | {         // si es una referencia a dim global
    modelId: string,
    nodeId: string
  },
  fields: Field[]
}
```

### Field (campo de una tabla)

```javascript
{
  id: string,
  name: string,
  description: string,
  dataType: string,           // ID de un tipo en dataTypes store
  isKey: boolean,             // llave primaria
  isFk: boolean               // llave foránea
}
```

### Relationship (relación entre tablas)

```javascript
{
  id: string,
  fromNodeId: string,
  toNodeId: string,
  cardinality: '1:1' | '1:N' | 'N:N'
}
```

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `allModels` | `array` | Todos los modelos |
| `getModel(id)` | `object \| null` | Modelo por ID |
| `globalModel` | `object \| null` | El modelo marcado como Global |

## Acciones — Modelos

### `ensureGlobalModel()`

Garantiza que siempre exista exactamente un modelo marcado como `isGlobal: true`. Si no existe, lo crea automáticamente con el nombre **"Global"** al inicio de la lista.

> Se llama en `onMounted` de `DimensionalModelListView`.

### `setGlobal(modelId)`

Marca un modelo como global y quita la marca a todos los demás.

### `createModel({ name, description, createdBy })`

Crea un nuevo modelo (no global). Retorna el objeto creado.

### `updateModel(id, patch)`

Actualiza campos del modelo (nombre, descripción, etc.).

### `deleteModel(id)`

Elimina un modelo. **Ignora la operación si el modelo es Global** (`isGlobal: true`).

## Acciones — Nodos

### `addNode(modelId, { type, name, x, y })`

Añade una nueva tabla al modelo. Retorna el nodo creado con `globalRef: null` y `fields: []`.

### `addGlobalDimRef(modelId, globalNodeId, position)`

Añade una **referencia de solo lectura** a una dimensión del modelo Global:

1. Busca el nodo en el modelo Global
2. Crea un nuevo nodo local con los mismos `type`/`name` pero:
   - `globalRef: { modelId: globalModelId, nodeId: globalNodeId }`
   - `fields: []` (se resuelven en runtime desde el modelo Global)
3. Añade el nodo al modelo indicado

```javascript
modelStore.addGlobalDimRef(modelId, globalNodeId, { x: 60, y: 60 })
```

### `updateNode(modelId, nodeId, patch)`

Actualiza propiedades de un nodo (nombre, posición, etc.).

### `deleteNode(modelId, nodeId)`

Elimina un nodo y todas las relaciones que lo involucran.

## Acciones — Campos

### `addField(modelId, nodeId, { name, description, dataType, isKey, isFk })`

Añade un campo al nodo. Retorna el campo creado.

### `updateField(modelId, nodeId, fieldId, patch)`

Actualiza un campo existente.

### `deleteField(modelId, nodeId, fieldId)`

Elimina un campo.

### `setKeyField(modelId, nodeId, fieldId)`

Marca un campo como llave primaria y desmarca todos los demás en el mismo nodo.

## Acciones — Relaciones

### `addRelationship(modelId, { fromNodeId, toNodeId, cardinality })`

Añade una relación. Retorna el objeto creado.

### `updateRelationship(modelId, relId, patch)`

Actualiza la cardinalidad u otras propiedades.

### `deleteRelationship(modelId, relId)`

Elimina una relación.

## Modelo Global — Concepto

El modelo Global actúa como una **biblioteca de dimensiones compartidas**:

```
Modelo Global
├── dim_cliente (dimension)    ← compartida
├── dim_tiempo (dimension)     ← compartida
└── dim_producto (dimension)   ← compartida

Modelo Ventas
├── fct_ventas (fact)
├── dim_cliente [globalRef] → Global.dim_cliente  ← solo lectura
└── dim_tiempo  [globalRef] → Global.dim_tiempo   ← solo lectura

Modelo Compras
├── fct_compras (fact)
└── dim_cliente [globalRef] → Global.dim_cliente  ← misma dimensión
```

### Resolución en runtime

En `DimensionalModelEditorView`, `resolveNode(node)` resuelve los nodos con `globalRef`:

```javascript
function resolveNode(node) {
  if (!node.globalRef) return node
  const gNode = modelStore.globalModel?.nodes.find(n => n.id === node.globalRef.nodeId)
  if (!gNode) return node
  // Mantiene id/posición local, pero usa name/fields del nodo global
  return { ...gNode, id: node.id, x: node.x, y: node.y, globalRef: node.globalRef }
}
```

`resolvedNodes` es un computed que aplica esto a todos los nodos del modelo.

## Persistencia

`localStorage['dimensionalModels']` — array de modelos completos.

`persist()` es un helper privado del store llamado al final de cada acción mutante.
