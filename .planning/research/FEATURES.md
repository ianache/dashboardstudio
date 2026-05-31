# Feature Research — v2.0 Collapsible Table Panel

**Domain:** BI Dashboard Designer — Left-Side Schema / Table Browser Panel
**Researched:** 2026-05-31
**Confidence:** HIGH (codebase analysis) / MEDIUM (BI tool UX patterns from Tableau, Power BI docs)

---

## What the Domain Ecosystem Does

### Tableau — Data Pane (Reference Implementation)

Tableau's Data Pane is the canonical model for this kind of panel. Key behaviors, sourced from Tableau Desktop documentation:

- Positioned on the far left of the workspace, anchored below the field shelves.
- Lists all fields from the connected source in a single scrollable list.
- Fields are split into two sections by a thin horizontal separator line: **Dimensions** (blue icons, qualitative) appear above the line, **Measures** (green icons, quantitative) appear below.
- Within each section, fields are alphabetically sorted by default.
- Fields are **draggable** to any shelf (rows, columns, marks cards) on the canvas. The same field can be dragged multiple times to different shelves simultaneously.
- The entire pane has a **collapse arrow** in the toolbar that hides or reveals it without affecting the canvas layout.
- A **search box** at the top of the pane filters the field list in real time (substring match).
- When fields are organized by folder or table, each folder has a **disclosure triangle** that collapses/expands that group. The top-level grouping is always "Dimensions" and "Measures".
- When the pane is narrow (collapsed to icon width), Tableau hides field names and shows only the field type icon — drag still works from the icon.

**Confidence: MEDIUM** — sourced from Tableau help docs and search results; not verified against live product.

### Power BI — Fields Pane

Power BI's Fields pane is anchored on the right side, but the UX patterns apply equally to a left panel:

- Tables are listed with expand/collapse affordances (chevron per table).
- `Alt + Shift + 9` expands all tables; `Alt + Shift + 1` collapses all — implying keyboard support is expected.
- `Right arrow` / `Left arrow` navigate within a table's fields.
- Field search filters across all tables in real time.
- Drag from the pane to the visual canvas adds a field to the chart.
- No visual distinction between fact and dimension tables in the pane — tables appear alphabetically. Analysts use naming conventions ("dim_", "fact_") to identify them.

**Confidence: MEDIUM** — sourced from Microsoft Learn documentation.

### Metabase / Looker Studio

Both tools take a different approach (query builder or chart-first). Neither provides a persistent left-side schema browser panel. The drag-to-canvas model is Tableau/Power BI territory. Metabase does not surface table groups; Looker Studio places dimension/metric selectors in a right-side panel per selected object.

These tools are not useful reference implementations for the Dashboard Studio panel.

---

## Table Stakes

Features users expect from a BI schema panel. Missing any of these makes the panel feel broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Panel toggles open/closed with a single button | Every left panel in every BI tool does this — it is muscle memory for analysts | Low | Toggle button sits on the panel's right edge; `leftCollapsed` boolean. `FlowEditorCanvas.vue` uses this exact pattern (`fec-left--collapsed` class). |
| Smooth CSS transition for expand/collapse | Abrupt layout shifts feel like bugs | Low | `transition: width` with `overflow: hidden` on `.panel-inner`. Width toggles between ~240px expanded and ~40px collapsed icon rail. |
| Collapsed state shows icon-only rail | Allows drag even when collapsed (Tableau model). Does not waste screen space. | Low | In collapsed state, show only the `table_chart` icon per item (no text). Icon is still draggable. |
| Tables listed with clear Hechos / Dimensiones grouping | Analysts think in star schema terms. The distinction between fact and dimension is how they reason about queries. | Low | Two sections, each collapsible, with a section header (e.g., "HECHOS", "DIMENSIONES"). |
| Each section header is independently collapsible | A dashboard about sales may have 1 fact and 20 dimensions — analyst needs to hide the noise | Low | Disclosure chevron on section header. State persisted per browser session (localStorage). |
| Alphabetical order within each section | Predictable. Reduces scanning time. | Low | `Array.sort()` on the table name before render. |
| Real-time text filter | Analysts with 30+ tables cannot scroll to find one | Medium | `v-model` input; computed `filteredTables` derived from raw table list. Filter spans both sections simultaneously. |
| Filter clears with an X button | Standard input affordance; keyboard `Esc` also clears | Low | `v-if` on the X button, only shown when filter has content. |
| Drag table from panel to canvas | Core action — replaces the "Añadir tabla" button | Medium | HTML5 `draggable="true"` + `@dragstart` sets `dataTransfer.setData('application/json', JSON.stringify(table))`. Canvas `@drop` reads it. |
| Multiple instances of the same table allowed | Analysts often join a dimension to itself (e.g., date as "order date" and "ship date") or analyze the same fact from multiple angles | Low | On drop, generate a fresh `instanceId = uuid()`. The table identity is the name; the canvas node identity is the instanceId. Never deduplicate on drop. |
| Empty state message when filter has no matches | Without this, the panel looks broken | Low | `v-if="filteredTables.length === 0"` shows "Sin resultados para '...'". |
| Badge showing count of tables per group | Helps orientation — "HECHOS (3) / DIMENSIONES (18)" | Low | Computed from the unfiltered list, not the filtered list (so counts stay stable while typing). |

---

## Differentiators

Features that make this panel better than expected. Not required for launch, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Drag ghost shows table name | Prevents "where did I drop that?" confusion | Low | `dataTransfer.setDragImage()` with a custom ghost element showing the table name. Alternative: browser default ghost is acceptable for v2.0. |
| Hover tooltip on table item showing column list | Analysts can preview what columns a table has without opening it | Medium | `@mouseenter` popover with column names from CubeJS meta. Requires `cubeStore.getMeasuresForCube` + `getDimensionsForCube`. |
| Visual indicator on canvas-placed tables | Analyst knows which tables are already in use | Medium | Cross-reference `activeDashboard.widgets` against placed tables. Show a small dot or counter on the panel item. High coupling to canvas state — defer for first iteration. |
| Keyboard drag (Enter to add at default position) | Accessibility; power users | Medium | `@keydown.enter` on a table item triggers `addWidget()` with a default position. Requires knowing what "default position" means on the canvas. |
| Persist panel open/closed state | Analysts re-open the same dashboard; panel should be where they left it | Low | `localStorage.setItem('designer.panelOpen', ...)`. Simple. |

---

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Show field/column list inside the panel for each table | Each table expansion becomes a tree — Tableau does this but it turns the panel into a data explorer, not a table picker. Dashboard Studio's canvas concept is "place a table", not "place a field". Columns are configured per widget after placement. | Keep the panel a flat table picker only. Fields are configured in `ChartConfigModal`. |
| Search that filters within table columns | Only useful if columns are shown. Without columns visible, filtering below the table level is meaningless. | Filter only on table name. |
| Ability to reorder sections (Hechos above/below Dimensiones) | No BI tool does this. Hechos first is the correct star schema convention. | Always show Hechos first, then Dimensiones. |
| Right-click context menu on table items | Adds discoverability burden. At this scope there is only one action (drag to canvas). | Rely on drag. Add a "+"-on-hover button as a fallback for non-drag interactions. |
| Panel resize handle (draggable width) | The resizable sidebar pattern was already built for the properties sidebar. Doing it again for the table panel at 240px is premature. | Fixed width 240px expanded, 40px collapsed. Revisit if user feedback requests it. |
| Lazy loading / pagination of tables | CubeJS meta is loaded once on mount. Even large schemas have fewer than 200 cubes — all load in one `loadMeta()` call. | Load all and filter client-side. |
| Sorting options (alphabetical / by type / by usage) | Alphabetical-within-group is the standard. Custom sorting is complexity with no analyst value. | Alphabetical always. |

---

## Feature Dependencies on Existing Canvas

| Panel Feature | Depends On | Risk |
|---------------|-----------|------|
| Drag to canvas | `DashboardRuntime.vue` → `DashboardGrid.vue` must handle `@drop` events | MEDIUM — `DashboardGrid.vue` currently only handles drag/resize of existing widgets. It must learn to accept drops from outside. |
| Table list | `cubeStore.cubes` (array from `loadMeta()`) | LOW — already populated when the designer loads. |
| Hechos vs Dimensiones grouping | CubeJS cube metadata does not natively label a cube as "fact" or "dimension" | MEDIUM — see Pitfall #1 below. Requires a naming convention or a CubeJS `meta` annotation. |
| Multiple instances of same table | `dashboardStore.addWidget()` generates a new ID per call | LOW — current `addWidget` already creates a fresh ID. No change needed. |
| Panel layout | `DashboardDesignerView.vue` wraps `DashboardRuntime` — the panel must sit at the same level | MEDIUM — requires a layout change in `DashboardDesignerView.vue`: a new flex row that contains `[TablePanel][DashboardRuntime]`. The `DashboardRuntime` must receive a `paddingLeft` or the layout must use flex so the runtime shrinks when the panel opens. |

---

## Pitfall: Hechos vs Dimensiones Classification

**The core problem:** CubeJS does not natively mark a cube as "fact" or "dimension". Its `/meta` endpoint returns an array of cubes, each with measures and dimensions, but no `type: 'fact' | 'dimension'` field.

**What the dimensional model module uses:** `AddNodeToDiagramModal.vue` already has `.node-type-badge.fact` and `.node-type-badge.dimension` styling, which means the `DimenionalModel` entity stores `type: 'fact' | 'dimension'` on each node. But these are separate from the CubeJS cubes.

**Options, ranked by implementation cost:**

1. **Naming convention (LOW complexity):** Cubes whose name starts with a configurable prefix (e.g., `Fact`, `Hecho`, or configured via env) are treated as hechos; everything else is dimensiones. This is the approach used in practice by most CubeJS deployments. **Recommended for v2.0.**

2. **CubeJS `meta.annotations` field (MEDIUM complexity):** CubeJS cubes support a `description` and an `annotations` / `tags` map. You can add `{ type: 'fact' }` there and read it in the frontend. Requires touching CubeJS schema files.

3. **Backend config endpoint (MEDIUM complexity):** A new `/api/v1/cube-classification` endpoint lets an admin tag cubes as fact/dimension. Overkill for v2.0.

**Recommended:** Use naming convention for v2.0. Expose the prefix as a configurable setting later.

---

## MVP Feature Set (v2.0 Scope)

Build in this order:

1. **Panel layout wrapper** — Modify `DashboardDesignerView.vue` to add a flex row containing `[TablePanel][DashboardRuntime]` in design mode only. Panel defaults open.

2. **TablePanel component** — New `dashboard/TablePanel.vue` with:
   - Toggle button (expand/collapse)
   - Hechos and Dimensiones sections, each independently collapsible
   - Alphabetical sort within each section
   - Real-time filter input with clear button
   - Table items with drag enabled (`draggable="true"` + `@dragstart`)
   - Collapsed icon-rail mode (icon only, drag still works)

3. **Canvas drop target** — `DashboardGrid.vue` handles `@dragover.prevent` + `@drop` to call `addWidget()` with the dropped table's data.

4. **Classification convention** — Naming-prefix logic in `TablePanel.vue` computed property.

Defer to post-v2.0:
- Column hover tooltip
- Canvas-placed table indicators
- Keyboard-accessible add action
- Panel resize handle

---

## Sources

- Tableau Data Pane documentation: https://help.tableau.com/current/pro/desktop/en-us/datafields_understanddatawindow.htm
- Tableau workspace overview: https://help.tableau.com/current/pro/desktop/en-us/environment_workspace.htm
- Tableau dragging fields to the view: https://help.tableau.com/current/pro/desktop/en-us/buildmanual_dragging.htm
- Power BI keyboard shortcuts (Fields pane navigation): https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-keyboard-shortcuts
- Power BI interface explained: https://www.catchr.io/university/power-bi-lessons/power-bi-interface-explained
- MDN HTML Drag and Drop API: https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API
- Vue.js Transition built-in: https://vuejs.org/guide/built-ins/transition
- FlowEditorCanvas.vue (codebase) — existing collapsible left panel implementation (HIGH confidence)
- DashboardDesignerView.vue, DashboardGrid.vue, cubejs.js (codebase — HIGH confidence)
- AddNodeToDiagramModal.vue (codebase) — fact/dimension badge pattern (HIGH confidence)

---

*Feature research for: Dashboard Studio v2.0 BI Analyst — Collapsible Table Panel*
*Researched: 2026-05-31*
