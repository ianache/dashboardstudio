# Phase 53: Panel de Ejecución por Nodo — Research

**Researched:** 2026-06-06
**Domain:** Vue 3 component authoring inside FlowEditorCanvas — reading live WebSocket events and historical execution data to render a per-node inspection panel
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

1. **Layout:** Inspector aparece dentro del `fec-right` panel existente usando `rightTab = 'inspector'` — mismo sistema de tabs que `props`/`variables`/`history`.
2. **Tabs del inspector:** 3 tabs — Entrada / Salida / Logs. Tab activo por defecto: **Salida**.
3. **JSON rendering:** `JSON.stringify` con indent 2 + botón "Expandir todo" / "Contraer todo". No se implementa árbol interactivo (deferred).
4. **Sección data_object:** título `data_object`, botón Expand/Collapse, aviso de truncado si > 2000 chars.
5. **Sección variables:** tabla 3 columnas Nombre/Valor/Tipo con `inferType()` helper en frontend.
6. **Tab Logs:** usar solo datos de `nodeInspectorData[node_id]` — NOT correlacionar `execLogs` globales por node_id.
7. **Estado en header:** chip success/error/running + duración + timestamps Inicio/Fin.
8. **Trigger de apertura — clic en nodo con datos de ejecución** → `rightTab = 'inspector'`. Clic en nodo sin datos → comportamiento actual (props).
9. **readOnly mode:** clic en nodo con `nodeLogsMap[node.id]` siempre abre inspector.
10. **Botón Exportar:** descarga JSON `{ node_id, node_name, status, duration, input, output, logs }` como `node-{node_id}-execution.json`.
11. **Componente separado:** `dashboard-app/src/components/editor/NodeInspectorPanel.vue` — "dumb", recibe prop `nodeData`.
12. **Dark theme:** idéntico a `ExecutionConsole.vue` — `#0f172a` bg, `#1e293b` header, `#334155` borders, `#e2e8f0` text, `#64748b` labels.
13. **Backend sin cambios:** todos los datos ya existen en WebSocket y BD.

### Claude's Discretion

- Ninguna area de libre discreción — todas las decisiones de diseño están bloqueadas.

### Deferred Ideas (OUT OF SCOPE)

- Diff entre input y output
- Búsqueda/filtro dentro del JSON inspector
- Inspección anidada interactiva (expandir/colapsar árbol JSON)
- Stream en tiempo real de logs por nodo (logs genéricos no tienen node_id)
- Ventana flotante/detachable del inspector
</user_constraints>

---

## Summary

Phase 53 adds a per-node execution inspector panel inside the existing `fec-right` sidebar of `FlowEditorCanvas.vue`. The backend already captures and emits everything needed: the `NODE_LOG_JSON:` Deno signal produces a `{ type: "node_log", node_id, status, input, output, duration, start_time, end_time }` WebSocket event, and the historical `/integration-flows/executions/{exec_id}/logs` endpoint returns the same shape with fields named `input`/`output`. No backend changes are required.

The current `ws.onmessage` handler has a critical gap: `node_log` events fall through to the `else` branch and land in `execLogs` as generic log lines — the `input` and `output` payloads are silently thrown away. The fix is to intercept `data.type === 'node_log'` before the `else` and populate a new `nodeInspectorData` ref. In readOnly mode, `nodeLogsMap` already has the historical data but it uses field names `input`/`output` (from the API response's `nl_dicts`), not `input_data`/`output_data` (the model column names).

The `fec-right` panel is currently `v-if="!readOnly"` — it does not render at all in readOnly mode. The inspector for historical viewing requires either: (a) removing the `!readOnly` guard and showing a read-only inspector-only panel, or (b) keeping the guard and showing the inspector as a different overlay. The CONTEXT.md decision states clic in readOnly mode opens the inspector — this requires the right panel to be rendered in readOnly mode too.

**Primary recommendation:** Add `nodeInspectorData` ref, intercept `node_log` in `ws.onmessage`, extend `selectNode()` with inspector logic, make `fec-right` available in readOnly mode (inspector-only), and create the `NodeInspectorPanel.vue` dumb component.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vue 3 Composition API | ^3.4 (project) | `ref`, `computed`, `watch` for reactive state | Already the project standard — all components use `<script setup>` |
| Material Symbols Outlined | (CDN, project) | Icons: `check_circle`, `cancel`, `sync`, `download`, `expand_more`, `expand_less` | All icons in this project use `msi` class + MSO font |
| Vanilla JS `JSON.stringify` | built-in | JSON rendering with indent | Agreed in CONTEXT.md — no library |
| Vanilla JS `Blob` + `URL.createObjectURL` | built-in | File export/download | Standard browser API for blob downloads |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `<style scoped>` | Vue 3 | Component-scoped CSS | Always — project convention |
| CSS custom properties | project `assets/main.css` | Theme-aware tokens | For any colors that should follow light/dark theme; dark panel hardcodes `#0f172a` etc. per ExecutionConsole pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `JSON.stringify(v, null, 2)` + `<pre>` | `vue-json-pretty`, `json-tree-view` | External libs add bundle weight; per CONTEXT.md decision the simple `<pre>` approach is locked |

**Installation:** No new packages needed. This phase is pure Vue component work.

---

## Architecture Patterns

### Recommended Project Structure
```
dashboard-app/src/components/editor/
├── FlowEditorCanvas.vue        # Modified: ws.onmessage, selectNode(), fec-right guard, nodeInspectorData ref
├── ExecutionConsole.vue        # Unchanged
└── NodeInspectorPanel.vue      # NEW: dumb component, receives nodeData prop
```

### Pattern 1: Capturing `node_log` in ws.onmessage

**What:** The `else` branch in `ws.onmessage` currently catches all unknown event types including `node_log`. `node_log` must be intercepted explicitly to capture `input`/`output`.

**Current code (lines 1741-1759 of FlowEditorCanvas.vue):**
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'node_status') {
    nodeExecStatus.value[data.node_id] = data.status
  } else if (data.type === 'status') {
    // ...
  } else {
    execLogs.value.push({ ...data, timestamp: new Date() })  // node_log lands here, input/output lost
  }
}
```

**Fix — add explicit branch before `else`:**
```javascript
} else if (data.type === 'node_log') {
  // Capture per-node execution data for inspector
  nodeInspectorData.value[data.node_id] = {
    input:      data.input,
    output:     data.output,
    status:     data.status,
    duration:   data.duration,
    start_time: data.start_time,
    end_time:   data.end_time,
    logs:       []   // reserved — node_log doesn't carry per-node logs array
  }
  // Also push a summary line to the global console
  execLogs.value.push({
    type: data.status === 'error' ? 'error' : 'info',
    message: `[${data.node_id}] ${data.status} (${data.duration}ms)`,
    timestamp: new Date()
  })
}
```

**Source:** Direct codebase read of `deno_service.py` lines 328-351 — confirmed WebSocket shape.

### Pattern 2: `nodeInspectorData` ref (live execution)

```javascript
// In FlowEditorCanvas.vue <script setup>
const nodeInspectorData = ref({}) // { [node_id]: { input, output, status, duration, start_time, end_time, logs } }
const inspectedNodeId   = ref(null)
```

Reset on new execution (`runFlow()`):
```javascript
nodeInspectorData.value = {}
inspectedNodeId.value   = null
```

### Pattern 3: Inspector data source — live vs historical

The planner must reconcile two data shapes:

| Mode | Data source | Field names | How to access |
|------|-------------|-------------|---------------|
| Live (WebSocket) | `nodeInspectorData.value[node_id]` | `input`, `output` | Set in ws.onmessage `node_log` branch |
| Historical (readOnly) | `nodeLogsMap` computed | `input`, `output` (confirmed: API endpoint `/executions/{exec_id}/logs` returns `"input": nl.input_data, "output": nl.output_data`) | `props.executionData.logs` → keyed by `node_id` |

Both modes use the same field names `input` / `output` — the API aliases `input_data` → `input` and `output_data` → `output` in the response dict. The `nodeLogsMap` computed already does `log.node_id → log` mapping, so `nodeLogsMap[node_id].input` and `.output` are valid.

**Computed to unify both sources:**
```javascript
const activeInspectorData = computed(() => {
  if (!inspectedNodeId.value) return null
  const id = inspectedNodeId.value
  // Live execution takes priority
  if (nodeInspectorData.value[id]) return nodeInspectorData.value[id]
  // Historical fallback
  if (nodeLogsMap.value[id]) return nodeLogsMap.value[id]
  return null
})
```

### Pattern 4: selectNode() modification — inspector trigger

**Current `selectNode()` (line 1988):**
```javascript
function selectNode(node) {
  if (props.readOnly) return
  if (!hasDragged) { 
    selectedNode.value = node
    // ...
    rightCollapsed.value = false 
  }
  hasDragged = false
}
```

**Modified — open inspector when execution data exists:**
```javascript
function selectNode(node) {
  // In readOnly mode, still allow node selection for inspector
  const isReadOnly = props.readOnly
  if (!hasDragged) {
    const hasExecData = isReadOnly
      ? !!nodeLogsMap.value[node.id]
      : !!nodeInspectorData.value[node.id]
    
    if (hasExecData) {
      inspectedNodeId.value = node.id
      rightTab.value = 'inspector'
      rightCollapsed.value = false
    } else if (!isReadOnly) {
      selectedNode.value = node
      selectedNote.value = null
      selectedConn.value = null
      rightCollapsed.value = false
    }
  }
  hasDragged = false
}
```

Note: In readOnly mode, `onNodeMousedown` currently returns early, so `hasDragged` is never set. The `@click.stop="selectNode(node)"` on the node div still fires in readOnly mode because `@click` is not guarded by readOnly. The modification needs to remove the early return for inspection purposes OR handle it via a separate `@click` in the template for readOnly nodes.

**Cleaner approach:** Add `@click.stop` handler directly for readOnly inspection without modifying `onNodeMousedown`:

In the template node div, add:
```html
@click.stop="readOnly ? openInspector(node) : selectNode(node)"
```

With:
```javascript
function openInspector(node) {
  if (!nodeLogsMap.value[node.id]) return
  inspectedNodeId.value = node.id
  rightTab.value = 'inspector'
  // fec-right is v-if="!readOnly" — see Pitfall #1 below
}
```

### Pattern 5: `fec-right` visibility in readOnly mode

**Current template (line 344):**
```html
<aside v-if="!readOnly" class="fec-right" ...>
```

The right panel is entirely hidden in readOnly mode. To show the inspector in readOnly mode, change to:
```html
<aside v-if="!readOnly || inspectedNodeId" class="fec-right" ...>
```

And inside, guard all edit-mode content with `v-if="!readOnly"` (already done for most sections via the existing tab structure — tabs are only shown when `!selectedNode`, but node props template uses `v-else-if="selectedNode"`). The inspector tab `v-if="rightTab === 'inspector'"` will be the only content in readOnly mode.

Also: the tab switcher in the right panel (`div.fec-tabs`) is shown `v-if="!selectedNode"`. In readOnly mode with an inspected node, there is no `selectedNode`, so the tab bar would show. Guard the inspector tab button to appear only when `inspectedNodeId` is set:
```html
<button v-if="inspectedNodeId" class="fec-tab" :class="{ active: rightTab === 'inspector' }" @click="rightTab = 'inspector'">
  <span class="msi" style="font-size:16px">analytics</span>Inspector
</button>
```

### Pattern 6: NodeInspectorPanel.vue — dumb component interface

```javascript
// Props
defineProps({
  nodeId:   { type: String, required: true },
  nodeName: { type: String, default: '' },
  nodeData: {
    type: Object,
    default: null
    // shape: { input, output, status, duration, start_time, end_time, logs: [] }
  }
})
```

The component renders 3 inner tabs (Entrada/Salida/Logs), the header chip, and the export button. It emits nothing — pure display.

### Pattern 7: JSON rendering with expand/collapse

CONTEXT.md decision: simple `<pre>` with `JSON.stringify(data, null, 2)`, plus a button that toggles between full JSON and collapsed `{}`.

```javascript
const jsonExpanded = ref(true)

function displayJson(data) {
  if (!data) return '{}'
  const str = JSON.stringify(data, null, 2)
  if (!jsonExpanded.value) return '{...}'
  if (str.length > 2000) {
    // Show truncation notice separately; still render full string
  }
  return str
}
```

CONTEXT.md also specifies: if payload > 2000 chars, show "Payload truncado (demasiado grande)" warning. This is a notice, not a hard cut — show the warning alongside the full pre (or truncate at discretion).

### Pattern 8: inferType helper (from CONTEXT.md)

```javascript
function inferType(val) {
  if (val === null) return 'Null'
  if (Array.isArray(val)) return 'Array'
  const t = typeof val
  return t.charAt(0).toUpperCase() + t.slice(1) // String, Number, Boolean, Object
}
```

### Pattern 9: Export button

```javascript
function exportNodeData(nodeId, nodeName, nodeData) {
  const payload = {
    node_id:   nodeId,
    node_name: nodeName,
    status:    nodeData.status,
    duration:  nodeData.duration,
    input:     nodeData.input,
    output:    nodeData.output,
    logs:      nodeData.logs || []
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `node-${nodeId}-execution.json`
  a.click()
  URL.revokeObjectURL(url)
}
```

### Anti-Patterns to Avoid

- **Correlating `execLogs` with `node_id`:** The global `execLogs` array contains `info`/`error` messages from runner output — these are NOT associated with a specific node. CONTEXT.md locks this: use only `nodeInspectorData[node_id].logs` (which is an empty array for now since the backend doesn't send per-node log messages in the `node_log` event). Do NOT attempt to filter `execLogs` by `node_id`.
- **Modifying the `ExecutionConsole`:** Out of scope. The global console stays unchanged.
- **Triggering a new API call for historical inspection:** All historical data is already in `props.executionData.logs` → `nodeLogsMap`. Do NOT fetch `/executions/{exec_id}/logs` again on node click.
- **Using `v-model` on props in NodeInspectorPanel:** The component is "dumb" — never mutates parent state.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON syntax highlighting | Custom tokenizer | `<pre>{{ JSON.stringify(v, null, 2) }}</pre>` | Per CONTEXT.md decision; project uses `<pre>` in ExecutionConsole already |
| File download | Native file dialog / server endpoint | `Blob` + `URL.createObjectURL` | Standard, no deps, works in all modern browsers |
| Tab state machine | Complex state store | Single `ref` switching between 'entrada'/'salida'/'logs' | Three states, no history needed |

**Key insight:** This phase is a pure frontend rendering problem. All the hard parts (data capture, persistence, streaming) are already done by the backend. The only new logic is: intercept a WebSocket event type, store it in a ref, and render it as formatted JSON + a table.

---

## Common Pitfalls

### Pitfall 1: fec-right is hidden in readOnly mode
**What goes wrong:** The `<aside v-if="!readOnly" class="fec-right">` guard means clicking a node in historical view (readOnly=true) triggers `openInspector()` but nothing renders.
**Why it happens:** The right panel was designed for editing only; readOnly flows show a full-canvas read-only view.
**How to avoid:** Change the v-if to `v-if="!readOnly || inspectedNodeId"`. Ensure all edit-only content inside (delete button, connection selectors, etc.) is wrapped in its own `v-if="!readOnly"` guard — most already are via `v-else-if="selectedNode"` template blocks.
**Warning signs:** Inspector tab is set, `inspectedNodeId` has a value, but the panel doesn't appear.

### Pitfall 2: node_log currently falls to the else branch — silent data loss
**What goes wrong:** If the `node_log` intercept is not added, `input` and `output` are swallowed by `execLogs.push({...data})` and never surface in the inspector.
**Why it happens:** The current `ws.onmessage` has no `node_log` case — it predates this feature.
**How to avoid:** Add `} else if (data.type === 'node_log') {` branch BEFORE the final `} else {` in `ws.onmessage`. Confirmed by reading lines 1741-1759 of FlowEditorCanvas.vue.
**Warning signs:** `nodeInspectorData` stays empty after execution even though nodes complete successfully.

### Pitfall 3: Historical nodeLogsMap field name is `input`/`output`, not `input_data`/`output_data`
**What goes wrong:** The SQLAlchemy model uses `input_data`/`output_data` column names. If the planner reads the model and assumes the API returns the same names, accessing `nodeLogsMap[id].input_data` will be `undefined`.
**Why it happens:** The API endpoint (`integration_flows.py` line 214) explicitly remaps: `"input": nl.input_data, "output": nl.output_data`.
**How to avoid:** Always access `nodeLogsMap[id].input` and `nodeLogsMap[id].output`. Confirmed by direct read of both the endpoint and the `nodeLogsMap` computed that maps `props.executionData.logs` entries directly.
**Warning signs:** Inspector shows "Sin datos" for input/output on historical executions even when logs exist.

### Pitfall 4: `selectNode()` returns early in readOnly — click never fires selection
**What goes wrong:** `function selectNode(node)` has `if (props.readOnly) return` as the first line. In readOnly mode, clicking a node does nothing.
**Why it happens:** readOnly mode was designed to prevent any editing.
**How to avoid:** Either remove the early readOnly guard entirely from `selectNode()` (safe since all mutations inside are already individually guarded), or use a separate template handler for readOnly node clicks. The template already uses `@click.stop="selectNode(node)"` — so modifying the function is the cleanest path.
**Warning signs:** `inspectedNodeId` never gets set when clicking nodes in readOnly mode.

### Pitfall 5: `hasDragged` is never reset in readOnly (onNodeMousedown returns early)
**What goes wrong:** `onNodeMousedown` returns early if `readOnly` is true, so `hasDragged` is never set to `true`. But `selectNode()` checks `if (!hasDragged)` — this means the guard works correctly for readOnly (hasDragged is always false → inspector opens). This is NOT a bug, just an interaction to be aware of.
**How to avoid:** No action needed. The existing `hasDragged` logic works correctly in readOnly because mousedown never fires the drag path.

### Pitfall 6: `rightTab` is a single ref shared between live and readOnly modes
**What goes wrong:** If the user is in live execution mode, selects a node (inspector opens with `rightTab = 'inspector'`), then navigates to a historical execution (readOnly), `rightTab` may still be 'inspector' pointing to stale data.
**How to avoid:** Reset `inspectedNodeId.value = null` and `rightTab.value = 'props'` in `runFlow()` (which already resets `nodeInspectorData`). Also reset on flow load/change.

### Pitfall 7: Tab switcher hides when selectedNode is set; inspector conflicts
**What goes wrong:** The tab switcher div uses `v-if="!selectedNode"`. If `selectedNode` is set AND `inspectedNodeId` is set, the tab switcher disappears, but the inspector content needs to show.
**Why it happens:** The design expects inspector to replace the node props panel, not coexist.
**How to avoid:** When opening the inspector, set `selectedNode.value = null` (to preserve the tab switcher visibility) and only use `inspectedNodeId` as the inspector trigger. The inspector tab button in the switcher is hidden until `inspectedNodeId` is truthy.

---

## Code Examples

### WebSocket message handler — complete modified version

```javascript
// Source: FlowEditorCanvas.vue ws.onmessage, lines 1741-1759 (current) + new node_log branch
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  if (data.type === 'node_status') {
    nodeExecStatus.value[data.node_id] = data.status
    
  } else if (data.type === 'node_log') {
    // NEW: capture per-node input/output for inspector
    nodeInspectorData.value[data.node_id] = {
      input:      data.input,
      output:     data.output,
      status:     data.status,
      duration:   data.duration,
      start_time: data.start_time,
      end_time:   data.end_time,
      logs:       []
    }
    execLogs.value.push({
      type: data.status === 'error' ? 'error' : 'info',
      message: `[${data.node_id}] completado en ${data.duration}ms`,
      timestamp: new Date()
    })
    
  } else if (data.type === 'status') {
    execStatus.value = data.success ? 'success' : 'error'
    execLogs.value.push({ 
      type: data.success ? 'info' : 'error', 
      message: `Fin de ejecución (Código: ${data.exit_code})`, 
      timestamp: new Date() 
    })
  } else {
    execLogs.value.push({ ...data, timestamp: new Date() })
  }
}
```

### NodeInspectorPanel.vue — skeleton structure

```vue
<template>
  <div class="nip-root">
    <!-- Header -->
    <div class="nip-header">
      <div class="nip-node-name">{{ nodeName }}</div>
      <div class="nip-status-row">
        <span class="nip-chip" :class="`nip-chip--${nodeData.status}`">
          <span class="msi">{{ statusIcon }}</span>
          {{ nodeData.status }}
        </span>
        <span class="nip-duration">{{ formatDuration(nodeData.duration) }}</span>
        <button class="nip-export-btn" @click="exportData" title="Exportar">
          <span class="msi">download</span>
        </button>
      </div>
      <div class="nip-timestamps">
        <span>Inicio: {{ formatTime(nodeData.start_time) }}</span>
        <span>Fin: {{ formatTime(nodeData.end_time) }}</span>
      </div>
    </div>
    
    <!-- Inner tabs -->
    <div class="nip-tabs">
      <button :class="['nip-tab', { active: innerTab === 'output' }]" @click="innerTab = 'output'">Salida</button>
      <button :class="['nip-tab', { active: innerTab === 'input' }]"  @click="innerTab = 'input'">Entrada</button>
      <button :class="['nip-tab', { active: innerTab === 'logs' }]"   @click="innerTab = 'logs'">Logs</button>
    </div>
    
    <!-- Tab content -->
    <div class="nip-body">
      <template v-if="innerTab === 'input' || innerTab === 'output'">
        <!-- data_object section -->
        <div class="nip-section-hdr">
          <span class="nip-section-title">data_object</span>
          <button class="nip-expand-btn" @click="jsonExpanded = !jsonExpanded">
            {{ jsonExpanded ? 'Contraer todo' : 'Expandir todo' }}
          </button>
        </div>
        <div v-if="isTruncated" class="nip-truncated-warn">
          Payload truncado (demasiado grande)
        </div>
        <pre class="nip-json">{{ displayJson(activePayload) }}</pre>
        
        <!-- variables section -->
        <div class="nip-section-hdr" style="margin-top:16px">
          <span class="nip-section-title">variables</span>
        </div>
        <table v-if="hasVariables" class="nip-vars-table">
          <thead><tr><th>Nombre</th><th>Valor</th><th>Tipo</th></tr></thead>
          <tbody>
            <tr v-for="(val, key) in activePayload?.variables" :key="key">
              <td>{{ key }}</td>
              <td>{{ formatVarValue(val) }}</td>
              <td>{{ inferType(val) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="nip-empty">Sin variables</div>
      </template>
      
      <template v-else-if="innerTab === 'logs'">
        <div v-if="!nodeData.logs?.length" class="nip-empty">Sin actividad registrada</div>
        <div v-for="(log, i) in nodeData.logs" :key="i" class="nip-log-line" :class="`nip-log--${log.severity}`">
          <span class="nip-log-ts">{{ log.timestamp }}</span>
          <span class="nip-log-msg">{{ log.message }}</span>
        </div>
      </template>
    </div>
  </div>
</template>
```

### Historical data flow — where executionData.logs comes from

```javascript
// FlowEditorCanvas.vue (readOnly mode consumer)
// props.executionData is passed from the parent view (FlowEditorView/IntegrationsView)
// It is set when user clicks "Ver detalles" in ExecutionHistoryPanel

// nodeLogsMap computed (line 1655):
const nodeLogsMap = computed(() => {
  if (!props.executionData?.logs) return {}
  // Each log: { node_id, status, input, output, duration, start_time, end_time }
  return Object.fromEntries(props.executionData.logs.map(log => [log.node_id, log]))
})

// Access in inspector:
// nodeLogsMap.value['node-uuid'].input   → input payload (already decoded JSON from backend)
// nodeLogsMap.value['node-uuid'].output  → output payload
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No per-node data in WebSocket | `NODE_LOG_JSON:` signal with full input/output | Already in deno_service.py | Backend is ready; frontend just hasn't consumed it |
| No per-node inspector | Per-node tooltip on hover (readOnly only) | Already exists | Tooltip shows status + timestamps; inspector adds input/output JSON |
| No right panel in readOnly | Right panel hidden (`v-if="!readOnly"`) | Existing | Must change to support readOnly inspector |

---

## Open Questions

1. **`node_log` vs `node_status` — which fires for ODS/Email nodes?**
   - What we know: ODS and Email nodes emit `node_status` (success/error) signals, NOT `NODE_LOG_JSON:`. They emit `node_log` with `{ type, node_id, status, message }` — no `input`/`output`. The `NODE_LOG_JSON:` signal is only emitted by Deno-side script/transform/LLM nodes via `runner.ts`.
   - What's unclear: Do ODS/Email nodes save `input_data`/`output_data` to `NodeExecutionLogs`? Yes — confirmed in `ods_executor.py` lines 571-578 and `integration_flows.py` lines 144-145. So historical data has input/output for all nodes, but live WebSocket only carries input/output for Deno-executed nodes.
   - Recommendation: Live inspector for ODS/Email nodes will show status/duration (from `node_status` event) but empty input/output (not sent via WebSocket). Historical inspector will show full data. This asymmetry is acceptable — document it in the component with a "Datos disponibles en historial" placeholder.

2. **What does `activePayload` look like? Is `variables` always a sub-key?**
   - What we know: `input` and `output` in `node_log` are whatever `ctx` looked like entering/exiting the node. The Deno runner passes `ctx` which has `{ data_object: {...}, variables: {...} }` shape based on the integration flow runner design.
   - What's unclear: Is `ctx.variables` always present? Is `ctx.data_object` the root or is the entire `ctx` the payload?
   - Recommendation: Treat the entire `input`/`output` value as the displayable payload. Render it as-is in the JSON `<pre>`. For the variables table: look for `input?.variables` — show table only if it exists, otherwise show "Sin variables". Do NOT assume a fixed shape.

3. **Tab switcher shows when `!selectedNode` — how to show inspector tab without a selectedNode?**
   - What we know: The tab bar `div.fec-tabs` has `v-if="!selectedNode"`. The inspector opens with `selectedNode.value = null` (per Pattern 7 above), so the tab bar IS visible.
   - What's unclear: Should the "Inspector" tab be always present in the switcher, or only when `inspectedNodeId` is set?
   - Recommendation: Only show the Inspector tab when `inspectedNodeId` is truthy. This prevents a confusing empty inspector tab when no node has been executed yet.

---

## Sources

### Primary (HIGH confidence)
- Direct read of `FlowEditorCanvas.vue` (lines 1-2138) — confirmed right panel structure, `rightTab` ref, `nodeExecStatus`, `nodeLogsMap`, `execLogs`, `ws.onmessage` handler, `selectNode()` function
- Direct read of `ExecutionConsole.vue` — confirmed dark theme colors, `#0f172a`/`#1e293b`/`#334155`/`#e2e8f0`/`#64748b`
- Direct read of `deno_service.py` lines 328-351 — confirmed `NODE_LOG_JSON:` → `node_log` event shape with `input`/`output`/`duration`/`start_time`/`end_time`
- Direct read of `integration_flows.py` lines 197-230 — confirmed historical endpoint returns `"input": nl.input_data, "output": nl.output_data`
- Direct read of `models/models.py` lines 270-285 — confirmed `NodeExecutionLogs` DB schema with `input_data`, `output_data`, `error_message` columns
- Direct read of `53-CONTEXT.md` — all design decisions locked

### Secondary (MEDIUM confidence)
- `ExecutionHistoryPanel.vue` — confirmed historical `node_logs` uses `log.input_data` field (the panel reads from the full execution detail endpoint, which returns `input_data`/`output_data` directly from the model — different from the `logs` sub-array which uses `input`/`output`). **Note:** `nodeLogsMap` in FlowEditorCanvas uses `props.executionData.logs` which comes from `loadExecutionLogs()` → the logs response → `{ "input": ..., "output": ... }`. Field is `input`/`output`, not `input_data`/`output_data`.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pure Vue 3 Composition API, no new dependencies
- Architecture: HIGH — all code paths confirmed by direct codebase reads
- Pitfalls: HIGH — all pitfalls found by reading actual code, not speculation
- Data shapes: HIGH — confirmed from both backend source and frontend computed

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (stable codebase, no external dependencies)
