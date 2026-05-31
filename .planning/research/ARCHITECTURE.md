# Architecture: Collapsible Table Panel — Dashboard Designer Integration

**Project:** Dashboard Studio v2.0 — BI Analyst
**Researched:** 2026-05-31
**Scope:** Vue 3 SPA integration only — no backend changes required

---

## Current Designer Architecture (as-built)

The designer operates in two modes gated by the `activeDashboard` computed in `DashboardDesignerView.vue`:

```
DashboardDesignerView.vue
  └─ (activeDashboard != null)
       ├─ PageHeader (actions: settings, mode toggle, add widget, AI assist)
       └─ DashboardRuntime.vue
            ├─ DashboardFilterBar.vue
            └─ DashboardGrid.vue   ← canvas
                 └─ DashboardWidget.vue (N times)
```

The full-width layout today is a simple flex column (`designer-view { display: flex; flex-direction: column }`). When a dashboard is open the structure is:

```
designer-view (flex column)
  ├─ PageHeader (flex-shrink: 0)
  └─ DashboardRuntime (flex: 1, overflow: hidden)
       └─ grid-container (flex: 1, overflow: auto)
            └─ DashboardGrid (absolute-positioned canvas)
```

There is no left panel today. The full horizontal space belongs to `DashboardRuntime`.

---

## Where Table Metadata Comes From

**Use `cubeStore` (already in memory) — do not add a new data source or endpoint.**

`cubejs.js` already exposes exactly what the panel needs:

| Getter | Contains |
|--------|----------|
| `cubeStore.cubes` | Array of all cubes from CubeJS meta (`state.meta?.cubes \|\| []`) |
| `cubeStore.getMeasuresForCube(name)` | Measures for one cube (type, title, fullName) |
| `cubeStore.getDimensionsForCube(name)` | Dimensions for one cube (type, title, fullName) |
| `cubeStore.metaLoading` | Boolean — use to show skeleton state in panel |
| `cubeStore.connected` | Boolean — show empty/error state if false |

`loadMeta()` is not called on `DashboardDesignerView` mount today — only the AI Assist feature reads `cubeStore.allMeasures` lazily. The new panel must call `cubeStore.loadMeta()` from its own `onMounted` if `!cubeStore.connected`.

**Hechos vs Dimensiones grouping:** CubeJS schema does not reliably provide a fact/dimension distinction at the meta API level. Adopt a name-based convention:

- Cubes whose `name` contains `"Fact"` (case-insensitive) → "Hechos" group
- All other cubes → "Dimensiones" group

This is display logic only. Do not add it to the Pinia store. Place it as a computed inside `TableSidePanel.vue`.

---

## Recommended Architecture

### Layout Change in `DashboardDesignerView.vue`

The designer mode template must introduce one new wrapper div that creates a two-column layout:

```
designer-view (flex column)
  ├─ PageHeader
  └─ designer-body   ← NEW wrapper (display: flex; flex-direction: row; flex: 1; overflow: hidden)
       ├─ TableSidePanel.vue  ← NEW (collapsible, flex-shrink: 0)
       └─ DashboardRuntime    (flex: 1, unchanged internally)
```

The only change to the existing template is wrapping `<DashboardRuntime>` inside this new `designer-body` div and placing `<TableSidePanel>` before it. No changes to `DashboardRuntime`, `DashboardGrid`, or `DashboardWidget`.

### New Component: `TableSidePanel.vue`

**Location:** `dashboard-app/src/components/dashboard/TableSidePanel.vue`

**Responsibilities:**
- Render a collapse toggle button (always visible even when collapsed)
- Show a search input that filters `cubeStore.cubes` by name (case-insensitive)
- Render two collapsible groups: "Hechos" first, then "Dimensiones"
- Each table row is a draggable source (HTML5 `draggable` attribute)
- Show loading skeleton when `cubeStore.metaLoading` is true
- Show empty/error state when `!cubeStore.connected` after `loadMeta()`

**Props:**
```javascript
defineProps({
  isDesignMode: { type: Boolean, default: false }
})
```

The panel only renders its content (and calls `cubeStore.loadMeta()`) when `isDesignMode` is true — it is invisible in preview mode.

### No New Store Actions Required

`dashboard.js` `addWidget()` already handles widget creation. The drop completes in `DashboardDesignerView.vue`, which calls `dashboardStore.addWidget()` — the same path as the existing "+ Add Widget" button and AI Assist. The table panel adds zero store surface area.

---

## Drag & Drop Integration with Existing Canvas

### The Key Constraint

`DashboardGrid.vue` registers `mousemove` and `mouseup` listeners on `document` to handle existing widget drag/resize operations. These listeners are registered in `onMounted` and removed in `onBeforeUnmount`. A drag originating outside the canvas (from the side panel) must not conflict with this system.

**Use the HTML5 Drag and Drop API, not the existing mousedown/mousemove pattern.** Reasons:

1. The existing canvas drag uses raw mouse events to move *existing widgets within* the canvas. HTML5 DnD is for dragging *new items onto a target* — which is the panel's use case.
2. HTML5 DnD fires its own event sequence (`dragstart`, `dragover`, `dragenter`, `dragleave`, `drop`) and does NOT fire `mousemove` on most browsers during a drag. The two systems do not interact.
3. Vue handles `@dragstart`, `@dragover`, `@drop` natively without extra setup.

### Data Transfer Protocol

The side panel encodes the cube identifier on `dragstart`:

```javascript
// In TableSidePanel.vue
function onDragStart(e, cube) {
  e.dataTransfer.setData('application/x-cubetable', JSON.stringify({
    cubeName: cube.name,
    title: cube.title
  }))
  e.dataTransfer.effectAllowed = 'copy'
}
```

The canvas receives the drop. In `DashboardGrid.vue`, add a `@drop` handler on the `.grid-canvas` div:

```javascript
function onExternalDrop(e) {
  e.preventDefault()
  const raw = e.dataTransfer.getData('application/x-cubetable')
  if (!raw) return                          // ignore non-panel drops
  const { cubeName } = JSON.parse(raw)
  const pos = clientToCanvas(e.clientX, e.clientY)
  const x = Math.max(0, Math.min(COL_COUNT - 6, snapCol(pos.x)))
  const y = Math.max(0, snapRow(pos.y))
  emit('table-dropped', { cubeName, position: { x, y, w: 6, h: 3 } })
}
```

The `table-dropped` event propagates upward:

```
DashboardGrid.vue
  emit('table-dropped', { cubeName, position })
    ↓
DashboardRuntime.vue (add to defineEmits + forward)
  emit('table-dropped', $event)
    ↓
DashboardDesignerView.vue
  @table-dropped handler
    → dashboardStore.addWidget(activeDashboard.id, {
        title: cubeName,
        chartType: 'bar',          // or 'table' — project decision
        cubeQuery: {
          measures: [],
          dimensions: [],
          timeDimension: null,
          filters: [],
          limit: 100
        },
        position: { x, y, w: 6, h: 3 },
        useMockData: false
      })
```

The widget starts empty; the designer opens `ChartConfigModal` to configure it — consistent with the existing add-widget flow.

### `dragover` on the Canvas

`DashboardGrid.vue` needs `@dragover.prevent` on `.grid-canvas` to accept external drops. HTML5 DnD requires `preventDefault` on `dragover` for the `drop` event to fire. A visual drop indicator can be added via a boolean ref toggled by `@dragenter` / `@dragleave` on the canvas element.

---

## Component Boundary Summary

| Component | Change Type | What Changes |
|-----------|-------------|--------------|
| `DashboardDesignerView.vue` | **Modified** | Adds `designer-body` wrapper div in designer-mode template; imports `TableSidePanel`; adds `@table-dropped` handler calling `dashboardStore.addWidget()` |
| `DashboardRuntime.vue` | **Modified** | Adds `table-dropped` to `defineEmits`; forwards the event from `DashboardGrid` via template binding |
| `DashboardGrid.vue` | **Modified** | Adds `@dragover.prevent` and `@drop` handler on `.grid-canvas`; emits `table-dropped`; no changes to existing drag/resize logic |
| `TableSidePanel.vue` | **New** | Collapse toggle, search input, grouped cube list, HTML5 drag sources, loading/error states |

**No changes needed to:** `DashboardWidget.vue`, `ChartConfigModal.vue`, `ChartLayoutModal.vue`, `DashboardFilterBar.vue`, `dashboard.js` store, `cubejs.js` store, any backend file.

---

## Data Flow Diagram

```
TableSidePanel.vue
  cubeStore.cubes ──────────────► (read, display in grouped list)
  cubeStore.loadMeta() ─────────► (called once on mount if not connected)

  [user drags a table row]
    dragstart → dataTransfer.setData('application/x-cubetable', JSON)
                                          │
                            .grid-canvas @dragover.prevent
                                          │
                            .grid-canvas @drop
                                          │
                          DashboardGrid.vue
                            onExternalDrop() resolves x,y via clientToCanvas + snapCol/snapRow
                            emit('table-dropped', { cubeName, position })
                                          │
                        DashboardRuntime.vue (passthrough)
                            emit('table-dropped', $event)
                                          │
                      DashboardDesignerView.vue
                          @table-dropped handler
                                          │
                          dashboardStore.addWidget(dashboardId, widgetData)
                                          │
                               backend API call (POST /widgets)
                                          │
                          widget appears on canvas at drop position
```

---

## Panel Collapse Mechanics

The panel uses a local `ref(true)` for `isExpanded`. When collapsed it shows only an icon strip (40px wide). When expanded it shows at a fixed width (260px recommended — consistent with `--sidebar-width: 240px` already defined in `assets/main.css`).

**CSS approach — width transition on the panel container:**

```css
.table-side-panel {
  width: 260px;
  transition: width 0.25s ease;
  flex-shrink: 0;
  overflow: hidden;
  border-right: 1px solid var(--border);
}
.table-side-panel.collapsed {
  width: 40px;
}
```

This avoids JavaScript measurement and does not interfere with `DashboardGrid`'s `ResizeObserver`. That observer watches `canvasRef` (the `.grid-canvas` element), which naturally shrinks as the side panel expands. `updateColWidth()` is triggered automatically, keeping column grid math correct.

---

## Build Order

1. **`TableSidePanel.vue`** — Build as a standalone component. Mock cube data with a static array initially to develop collapse, search, and group toggle UI without needing a running CubeJS instance. Swap to `cubeStore.cubes` once layout is confirmed.

2. **`DashboardGrid.vue` DnD addition** — Add `@dragover.prevent` and `@drop` handler on `.grid-canvas`. Emit `table-dropped`. Verify drop recognition independently (console.log the event data). No canvas behavior changes.

3. **`DashboardRuntime.vue` passthrough** — Add `table-dropped` to `defineEmits` and forward from `DashboardGrid`. One line change.

4. **`DashboardDesignerView.vue` wiring** — Add `designer-body` wrapper, import and place `TableSidePanel`, wire `@table-dropped` to the `addWidget` call.

5. **End-to-end validation** — Drag table from panel, widget appears at drop position with correct empty state. Verify `ResizeObserver` recalculates column widths after panel collapse/expand.

---

## Pitfalls to Avoid

### Conflicting Drag Systems
The existing `document` mousemove/mouseup handlers in `DashboardGrid` operate on native mouse events. HTML5 DnD does NOT fire `mousemove` during a drag on most browsers. Keep the two drag systems completely separate — do not set `dragState.active` from `@dragenter` on the canvas if it is the same ref used by widget repositioning.

### `dragover` preventDefault Missing
Forgetting `@dragover.prevent` on the canvas element silently prevents `drop` from firing. This is the single most common HTML5 DnD bug. Add it directly on the `.grid-canvas` div, not on a child element.

### `ResizeObserver` and Panel Width
`DashboardGrid` has a `ResizeObserver` on `canvasRef` for `updateColWidth()`. The observer fires automatically when the panel collapses/expands and the canvas resizes. Do not manually call `updateColWidth()` from the panel toggle — the observer handles it.

### Same Table Multiple Times
The milestone requires adding the same table more than once. `dashboardStore.addWidget()` generates a new widget ID on every call. This already works — no special deduplication logic should be added.

### CubeJS Meta Not Loaded on Mount
The panel mounts before `loadMeta()` completes if a dashboard opens before the cube schema has been fetched. Show a skeleton/spinner when `cubeStore.metaLoading` is true and an empty state with a retry button when `!cubeStore.connected` after loading. The panel should call `cubeStore.loadMeta()` itself (guarded by `if (!cubeStore.connected)`) rather than relying on `DashboardDesignerView` to call it.

### Panel Visible in Preview Mode
The panel should only be visible in design mode (`isDesignMode === true`). In preview mode the panel adds no value and wastes horizontal space. Use `v-if="isDesignMode"` on the `TableSidePanel` in `DashboardDesignerView`.

---

## Sources

- `dashboard-app/src/components/dashboard/DashboardGrid.vue` — canvas event model: `document` mousemove/mouseup handlers, `dragState` ref, `clientToCanvas()`, `snapCol()`, `snapRow()`, `ResizeObserver` on `canvasRef` (direct codebase read)
- `dashboard-app/src/components/dashboard/DashboardRuntime.vue` — component boundary, emit passthrough pattern (direct codebase read)
- `dashboard-app/src/views/DashboardDesignerView.vue` — designer layout, `isDesignMode` ref, `addWidget()` call path, `cubeStore` already imported (direct codebase read)
- `dashboard-app/src/stores/cubejs.js` — available getters: `cubes`, `getMeasuresForCube`, `getDimensionsForCube`, `metaLoading`, `connected`, `loadMeta()` action (direct codebase read)
- `dashboard-app/src/stores/dashboard.js` — `addWidget(dashboardId, widgetData)` signature (direct codebase read)
- `.planning/PROJECT.md` — v2.0 milestone requirements: collapsible panel, drag & drop, same table multiple times, filter by name, alphabetical groups (direct codebase read)
- MDN HTML Drag and Drop API: https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API (dragover.prevent requirement for drop to fire)

---

*Architecture research for: v2.0 BI Analyst — Collapsible Table Panel*
*Researched: 2026-05-31*
