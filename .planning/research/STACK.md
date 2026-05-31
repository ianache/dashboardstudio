# Technology Stack: Collapsible Side Panel with Drag & Drop (v2.0 BI Analyst)

**Project:** Dashboard Studio — v2.0 BI Analyst (collapsible table panel)
**Researched:** 2026-05-31
**Confidence:** HIGH — all findings verified against installed packages and live source code in the repo

---

## Executive Finding

**No new dependencies are needed.** The project already has every capability required:

1. Native HTML5 Drag and Drop API — already implemented for this exact feature type in `DimensionalModelEditorView.vue`
2. `vuedraggable@4.1.0` — already installed (used in `VisualizationConfiguratorView.vue` for field reordering)
3. `@vueuse/core@10.9.0` — already installed, provides `useLocalStorage` if panel state persistence is desired
4. Vue 3 `ref()` + `v-show` + `computed()` — sufficient for collapsible groups and search filter

More importantly, `DimensionalModelEditorView.vue` is a **direct reference implementation** of the exact feature being built: a collapsible left panel listing Hechos/Dimensiones with grouped/collapsible sections, a search filter, and HTML5 DnD onto a free-canvas. The new dashboard panel component can adopt this pattern verbatim, adapting only the data source and drop handler.

---

## Recommended Stack

### Drag & Drop

| Technology | Version | Status | Why |
|------------|---------|--------|-----|
| Native HTML5 DnD API | browser built-in | Already proven in codebase | `draggable="true"` + `@dragstart` / `@dragover.prevent` / `@drop` is the complete API surface. Zero weight, no import, works cross-container (panel item to canvas). |
| `vuedraggable` | 4.1.0 | Already installed | Do NOT use for this feature — its role is list reordering (SortableJS wrapper), not cross-container transfers to a canvas. |

**Decision: native HTML5 DnD only.** The drag source is a panel list item; the drop target is the dashboard canvas. This is a cross-container transfer, not in-list reordering. `vuedraggable` adds complexity with no benefit here.

The reference implementation lives at `DimensionalModelEditorView.vue` lines 1872–1904:

```javascript
// Panel item: set node id in the transfer payload
function onPanelDragStart(node, e) {
  e.dataTransfer.effectAllowed = 'copyMove'
  e.dataTransfer.setData('text/plain', node.id)
  panelDragNodeId.value = node.id
}

// Canvas: read it and compute drop position
function onCanvasDrop(e) {
  e.preventDefault()
  const nodeId = e.dataTransfer.getData('text/plain')
  if (!nodeId || !canvasEl.value) return
  const pos = canvasPos(e.clientX, e.clientY)  // accounts for scroll
  // add table to canvas at pos
}
```

For the dashboard grid (no zoom transform, unlike the dimensional model canvas), coordinate math is simpler: `x = e.clientX - rect.left + el.scrollLeft`.

### Collapsible Groups and Panel Toggle

| Technology | Version | Status | Why |
|------------|---------|--------|-----|
| `ref()` + `v-show` | Vue 3 core | Already used in reference impl | A boolean ref per collapsible group plus one for the panel itself. No library needed. |
| `@vueuse/core` `useLocalStorage` | 10.9.0 | Installed, opt-in | Wrap the panel `open` ref in `useLocalStorage('bi-panel-open', true)` to survive page refresh. Zero cost — already available. |

**Decision: plain `ref()` for group collapse state; `useLocalStorage` for the panel open/closed state if persistence is desired.** The reference implementation uses `ref(leftPanelOpen)`, `ref(factsExpanded)`, `ref(dimsExpanded)` — this is the model to follow.

### Search / Filter

| Technology | Version | Status | Why |
|------------|---------|--------|-----|
| `computed()` + `String.includes()` | Vue 3 core | Already used in reference impl | A reactive `tableSearch` ref + two `computed` getters (`filteredFacts`, `filteredDims`) is all that is needed. |

```javascript
// Already implemented in DimensionalModelEditorView.vue lines 1531–1545
const filteredFacts = computed(() => {
  const q = tableSearch.value.trim().toLowerCase()
  return tables.value.filter(t => t.type === 'fact' && (!q || t.name.toLowerCase().includes(q)))
})
```

### Panel Layout and Collapse Animation

| Technology | Version | Status | Why |
|------------|---------|--------|-----|
| CSS `width` + `transition` | browser built-in | Already used in this codebase | `.left-panel { width: 220px; transition: width 0.2s }` + `.left-panel.collapsed { width: 40px }` is the same pattern DimensionalModelEditorView uses. |

**Decision: CSS only.** No resize library needed. A fixed collapsed width showing an icon strip (same pattern as `.panel-collapsed-strip` in the reference) is the proven approach.

---

## What NOT to Add

| Library | Why Not |
|---------|---------|
| `@vueuse/gesture` | Gesture library designed for pointer/touch gesture recognition. No drop-zone semantics. Overkill for desktop BI DnD. |
| `dnd-kit` | React-only. Incompatible. |
| `vue-draggable-plus` | Alternative to vuedraggable; unnecessary since native DnD is sufficient and simpler. |
| `interact.js` | Full drag+resize library. Overkill — the panel does not need resize, and the canvas already has its own drag logic. |
| Any virtual scroll library | BI models have tens of tables, not thousands. Virtualization adds complexity with no measurable benefit. |
| Any animation library | CSS `transition` on `width` and `opacity` covers all required collapse animation. |

---

## Integration Points with Existing Canvas

The drop target for the new feature is `DashboardGrid.vue`, which uses absolute pixel positioning (12-column grid, 90px row height, 10px gap). To add external drop support:

1. Add `@dragover.prevent` and `@drop="onExternalDrop"` to the grid root element.
2. In `onExternalDrop`, compute grid position: `x = e.clientX - rect.left + el.scrollLeft`, `y = e.clientY - rect.top + el.scrollTop`, then snap to nearest column/row.
3. The `dataTransfer` payload carries the table identifier (name or id). The drop handler calls the store action to create a new widget at the computed position.
4. Allow dropping the same table multiple times (the milestone requirement "same table more than once") — each drop creates a new widget with a unique id, not a reference to a shared one.

`DashboardGrid.vue` already has internal widget drag via `mousedown/mousemove/mouseup`. The external HTML5 DnD events (`dragover`, `drop`) are separate and do not conflict with internal drag logic.

---

## Version Inventory (Installed)

| Package | Installed Version | Source |
|---------|------------------|--------|
| `vue` | 3.4.21 | package-lock.json |
| `vuedraggable` | 4.1.0 | package-lock.json |
| `sortablejs` (vuedraggable dep) | 1.14.0 | package-lock.json |
| `@vueuse/core` | 10.9.0 | package-lock.json |
| `pinia` | 2.1.7 | package.json |

---

## Installation

No installation required. Confirm installed state:

```bash
# No new packages needed. All capabilities are already present.
# Verify from dashboard-app/:
# cat package.json | grep -E "vuedraggable|vueuse"
# -> "vuedraggable": "^4.1.0"
# -> "@vueuse/core": "^10.9.0"
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Panel-to-canvas DnD | Native HTML5 DnD | `vuedraggable` | vuedraggable is a list-sort primitive; it does not model "drag to a free canvas and drop at coordinates". Native DnD gives `clientX/Y` on drop which is exactly what coordinate calculation needs. |
| Panel-to-canvas DnD | Native HTML5 DnD | `@vueuse/gesture` | Gesture lib; no concept of drop target. Would need a complete custom DnD implementation on top anyway. |
| Group collapse state | `ref()` + `v-show` | Pinia store | Panel group state is local UI state — it belongs in the component, not global state. Pinia would be over-engineering. |
| Panel open/closed persistence | `useLocalStorage` (opt-in) | Manual `localStorage` calls | `useLocalStorage` from `@vueuse/core` is reactive (changes reflect instantly in the template) and is already available. |

---

## Reference Implementation

`DimensionalModelEditorView.vue` is a complete, working, production-ready implementation of the exact feature:

| Feature | Location in reference |
|---------|----------------------|
| Collapsible left panel with toggle button | Template lines 125–199, CSS at ~line 2200+ |
| Icon strip when panel is collapsed | `v-if="!leftPanelOpen"` block with `.panel-pip` items |
| Search input filtering both groups | `tableSearch` ref + `filteredFacts`/`filteredDims` computed |
| Hechos group, collapsible, with count badge | `panel-group` div with `factsExpanded` ref |
| Dimensiones group, collapsible, with count badge | `panel-group` div with `dimsExpanded` ref |
| `draggable="true"` items with type badge | `panel-node-item` divs with `@dragstart` |
| Canvas `@dragover.prevent` + `@drop` | Canvas div at line 220–221 |
| Coordinate calculation accounting for scroll | `canvasPos()` function |
| `panelDragNodeId` ref for visual feedback | Line 1654, cleared on dragend and on drop |

The new dashboard side panel component is approximately a subset of this implementation, with these differences:
- Data source is tables from the backend/CubeJS API instead of `model.nodes`
- Drop handler creates a new widget in `DashboardGrid` instead of repositioning a model node
- No zoom transform to account for in coordinate calculation

---

## Sources

- `dashboard-app/package.json` — declared dependencies (HIGH confidence, direct read)
- `dashboard-app/package-lock.json` lines 2059–2070 — installed vuedraggable@4.1.0, sortablejs@1.14.0 (HIGH confidence, direct read)
- `dashboard-app/package-lock.json` line 2065, @vueuse/core — installed 10.9.0 (HIGH confidence, direct read)
- `dashboard-app/src/views/DimensionalModelEditorView.vue` lines 123–199 (template), 1531–1545 (computed), 1654 (ref), 1872–1904 (DnD handlers) — reference implementation (HIGH confidence, direct source read)
- `dashboard-app/src/views/VisualizationConfiguratorView.vue` line 634 — `vuedraggable` import confirming existing usage for list reorder (HIGH confidence, direct source read)
