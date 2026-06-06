---
name: panel-ejecucion-por-nodo-context
description: Decisiones de diseño para el panel de inspección por nodo en Integration Flows — basado en diseño Stitch "Data Inspector Panel"
metadata:
  type: project
---

# Phase 53: Panel de Ejecución por Nodo — Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** Stitch Design "Data Inspector Panel" (screen: 30f843a8c9a04e6297e63d11c8ec37bb) + análisis de codebase

---

<domain>
## Phase Boundary

Agregar un panel de inspección por nodo en el Flow Editor que muestre el ctx (entrada, salida) y los logs de ejecución de cada nodo individual. El panel se activa al hacer clic sobre un nodo que haya sido ejecutado, y muestra los datos que el backend ya captura y envía (el campo `node_log` ya existe en el WebSocket y en la BD).

**Lo que cambia:**
- Frontend: nuevo componente `NodeInspectorPanel.vue` dentro del FlowEditorCanvas
- Frontend: el FlowEditorCanvas captura y almacena `node_log` events por `node_id`
- Frontend: clic en nodo ejecutado abre el panel inspector en lugar (o además) de las props
- Backend: sin cambios de lógica de negocio — los datos `input`, `output` ya llegan vía WebSocket `node_log` y ya están en la BD en `NodeExecutionLogs`
- Backend: el endpoint de logs históricos ya devuelve `input_data` y `output_data`

**Lo que NO está en scope:**
- Cambiar la lógica de ejecución del backend
- Añadir variables ctx adicionales al runner
- Modificar el `ExecutionConsole` (consola global — sigue igual)
- Vista mobile
</domain>

<decisions>
## Implementation Decisions

### 1. Layout del panel — Drawer lateral derecho
- El inspector aparece como un panel deslizable en el lado DERECHO del canvas
- Mismo patrón que el panel de propiedades de nodo existente (`fec-right`)
- Se activa con un tab o botón independiente: `rightTab = 'inspector'`
- El panel de propiedades (`props`) y el inspector (`inspector`) comparten el mismo `fec-right` usando el sistema de tabs existente (`rightTab` ref)
- Ancho: usa el ancho del panel derecho existente (el sistema fec-right)
- Solo se muestra contenido si el nodo seleccionado tiene datos de ejecución

### 2. Estructura de tabs del inspector — 3 tabs
El panel inspector tiene 3 tabs:
1. **Entrada** — ctx.data_object al entrar al nodo (input)
2. **Salida** — ctx.data_object al salir del nodo (output)
3. **Logs** — mensajes de log del nodo (info, error, warnings)

Tab activo por defecto: **Salida** (lo más relevante para el usuario)

### 3. Sección "ctx.data_object" — JSON expandible
- Título de sección: `data_object`
- Botón "Expandir todo" / "Contraer todo" en el header de sección
- Renderizar el JSON con indentación (similar al `<pre>` existente en ExecutionConsole)
- Si el payload > 2000 chars o es truncado: mostrar aviso "Payload truncado (demasiado grande)"
- Color scheme: usar el mismo dark theme del ExecutionConsole (`#0f172a` bg, `#e2e8f0` text)
- Si no hay data_object (null/vacío): mostrar `{}` o mensaje "Sin datos"

### 4. Sección "ctx.variables" — Tabla Name/Value/Type
- Tabla con 3 columnas: **Nombre** | **Valor** | **Tipo**
- Tipo inferido en frontend: `typeof value` → String, Number, Boolean, Object, Array, Null
- Solo mostrar si hay variables definidas; si no: "Sin variables"
- El valor se muestra como string; si es objeto/array, mostrarlo serializado en 1 línea

### 5. Tab "Logs" — Lista de mensajes por nodo
- Mensajes del `execLogs` filtrados por `node_id` (correlación via `node_id` que ya viene en WebSocket)
- Formato: `[timestamp] [SEVERITY] mensaje`
- Severidades con colores: info (gris), error (rojo `#f87171`), result (azul `#38bdf8`)
- Botón "Exportar" → descarga los logs del nodo como `.txt`
- Si no hay logs: "Sin actividad registrada"

### 6. Indicador de estado en header del panel
- Chip de estado: `success` (verde, ✓ check_circle) / `error` (rojo, ✗ cancel) / `running` (azul pulsante, sync)
- Duración de ejecución del nodo junto al chip (ej: `245ms`)
- Timestamps: "Inicio: HH:MM:SS" y "Fin: HH:MM:SS"

### 7. Cómo se abre el inspector
**Durante ejecución en vivo (WebSocket):**
- Al hacer clic en un nodo que tiene `nodeExecStatus[node.id]` !== undefined → abre inspector y muestra tab `rightTab = 'inspector'`
- Los datos `input` y `output` se almacenan en un `nodeInspectorData` ref: `{ [node_id]: { input, output, status, duration, start_time, end_time, logs[] } }`
- El evento `node_log` del WebSocket (ya enviado por backend) se captura en `ws.onmessage` y popula `nodeInspectorData`

**En modo lectura (executionData histórica):**
- Los `executionData.logs` ya contienen `input_data` y `output_data` (vienen del endpoint de historial)
- Al hacer clic en nodo con `nodeLogsMap[node.id]` → mostrar inspector con datos históricos

### 8. Trigger de apertura — doble funcionalidad del clic en nodo
- **Clic simple en nodo sin ejecución** → comportamiento actual (seleccionar, mostrar props)
- **Clic simple en nodo con datos de ejecución** → abrir inspector (tab `inspector` en fec-right)
- El panel de props sigue accesible vía tab switcher en fec-right
- En `readOnly` mode (historial): clic en nodo siempre abre inspector si hay `nodeLogsMap[node.id]`

### 9. Botón de exportar
- Botón "Exportar" en el header del inspector
- Descarga un JSON con `{ node_id, node_name, status, duration, input, output, logs }`
- Nombre de archivo: `node-{node_id}-execution.json`

### 10. Vacío / sin ejecución
- Si se hace clic en nodo sin datos de ejecución: mostrar el panel de props normalmente (comportamiento actual)
- El tab "Inspector" solo aparece en el switcher si hay datos de ejecución para ese nodo

### 11. Estilo visual — dark theme del inspector
Igual que `ExecutionConsole.vue`:
- Background: `#0f172a` (body del inspector)
- Header del panel: `#1e293b`
- Border separadores: `#334155`
- Texto principal: `#e2e8f0`
- Timestamps/labels: `#64748b`
- Font: monospace para JSON/datos, sans-serif para labels

### 12. Componente nuevo vs inline
- Crear componente separado: `dashboard-app/src/components/editor/NodeInspectorPanel.vue`
- FlowEditorCanvas lo importa y lo renderiza dentro del `fec-right`
- Props: `nodeId`, `nodeName`, `nodeData` (objeto con input/output/status/duration/logs/timestamps)
- El componente es "dumb" — solo recibe datos y renderiza

</decisions>

<specifics>
## Specific Ideas

### Diseño Stitch — Data Inspector Panel (screen 30f843a8c9a04e6297e63d11c8ec37bb)
El diseño de referencia muestra exactamente este layout dentro del panel derecho:
- Header con título del nodo + chip de estado (✓ success)
- Tabs: "View Input" / "View Output" (adaptamos a ES: "Entrada" / "Salida" / "Logs")
- Sección `data_object` con botón "Expand All" y JSON colapsable
- Sección `variables` con tabla Name/Value/Type
- Sección "System Logs" con timestamps y severity tags: [SOURCE], [DB_LOAD], [SUCCESS], [OUTPUT]

### Datos ya disponibles en backend
El WebSocket ya emite `{ type: "node_log", node_id, status, input, output, duration, start_time, end_time }` — **no se necesita cambiar el backend**.

El endpoint de logs históricos en `/integration-flows/executions/{exec_id}/logs` ya devuelve `input_data` y `output_data` en cada `NodeExecutionLog`.

### Correlación de logs del nodo
Los `execLogs` globales no están asociados a `node_id`. Para los logs del tab "Logs" del inspector:
- Solo usar los datos de `nodeInspectorData[node_id]` que llegan en el `node_log` event
- No intentar correlacionar `execLogs` (info/error genéricos) con nodos individuales
- Si el backend en el futuro emite logs con `node_id` en `info` events, se puede correlacionar

### Formato de tipos en tabla variables
```javascript
function inferType(val) {
  if (val === null) return 'Null'
  if (Array.isArray(val)) return 'Array'
  const t = typeof val
  return t.charAt(0).toUpperCase() + t.slice(1) // String, Number, Boolean, Object
}
```

</specifics>

<deferred>
## Deferred Ideas

- Diff entre input y output para mostrar qué cambió el nodo
- Búsqueda/filtro dentro del JSON inspector
- Inspección anidada interactiva (expandir/colapsar nodos del árbol JSON) — por ahora: `JSON.stringify` con indent + botón "Expandir todo"
- Stream en tiempo real de logs por nodo (actualmente logs genéricos no tienen node_id)
- Ventana flotante/detachable del inspector

</deferred>

---

*Phase: 53-panel-de-ejecucion-por-nodo-en-integration-flows-con-ctx-entrada-salida-y-logs*
*Context gathered: 2026-06-06 — Stitch design + codebase analysis*
