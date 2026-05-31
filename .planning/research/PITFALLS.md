# Domain Pitfalls: Collapsible Panel with DnD into an Existing Canvas

**Domain:** Adding a collapsible left-side table-browser panel with drag & drop to an existing Vue 3 dashboard canvas
**Project:** Dashboard Studio v2.0 — BI Analyst (Feat 04)
**Researched:** 2026-05-31

---

## Critical Pitfalls

Mistakes that cause rewrites or major behavior regressions.

---

### Pitfall 1: Mixing HTML5 DnD API with the Canvas Custom Mouse-Event System

**What goes wrong:**
`DashboardGrid.vue` uses a fully custom drag/resize system built on raw `mousedown`/`mousemove`/`mouseup` handlers registered on `document`. If the new panel uses the HTML5 DnD API (`draggable="true"`, `dragstart`, `dragover`, `drop`), two incompatible drag systems share the same document. The HTML5 DnD API fires an internal drag event loop that **suppresses normal pointer events during a drag operation** — `mousemove` does not fire between `dragstart` and `dragend`. When the user drags a table item from the panel and the cursor crosses the `DashboardGrid` area, the canvas's `onMouseMove` never fires, which means `dragState` never updates. If the user releases outside a valid drop target, the canvas is left in a permanently stuck drag state (`dragState.active = true`), making every subsequent pointer event attempt to move a widget.

**Why it happens:**
HTML5 DnD and synthetic-mousemove DnD are architecturally incompatible. The browser's DnD event loop takes exclusive pointer ownership during a drag. This is not a Vue limitation — it is a browser-level behavior.

**Consequences:**
- Canvas widgets become frozen or unmovable until page refresh.
- Resize handles stop responding.
- The drag-ghost overlay (`drag-ghost` div) renders in a frozen position.

**Prevention:**
Do NOT use `draggable="true"` / HTML5 DnD API for panel items. Use a custom `mousedown` → `mousemove` → `mouseup` approach that lives entirely in the same synthetic-mouse pipeline as the canvas. On `mousedown` on a table item, store a Pinia `panelDrag` state (`{ active, tableId, tableName, type }`). The canvas's existing `onMouseUp` checks `panelDrag.active` and treats the release as "drop new table" rather than "move existing widget." Both systems share `clientToCanvas()` coordinate math with no API conflict.

**Detection:**
After implementing panel drag: drag a table item and release it somewhere other than the canvas. Then try to drag an existing canvas widget. If the widget is stuck or moves without a fresh mousedown, this is the bug.

---

### Pitfall 2: `colWidth` Stale After Panel Collapse/Expand

**What goes wrong:**
`DashboardGrid.vue` computes `colWidth` via `updateColWidth()` driven by a `ResizeObserver` on `canvasRef`. When the side panel slides in or out, `DashboardRuntime`'s `grid-container` (which is `flex: 1`) shrinks or grows. However, `ResizeObserver` callbacks are asynchronous and batched. During a smooth CSS transition (e.g., 300ms panel collapse), `ResizeObserver` fires multiple times but the final value arrives late. During the transition frames, `colWidth` is stale. Any widget drag or resize that starts while the transition is in progress uses wrong column widths: `snapCol()` and `snapRow()` produce incorrect grid coordinates, and the committed widget position is off by a proportional amount.

**Why it happens:**
CSS flex layout recalculates child widths synchronously on each paint frame during a transition, but `ResizeObserver` callbacks are delivered asynchronously after painting. There is a window of several frames where `canvasRef.offsetWidth` has changed but `colWidth.value` has not yet been updated.

**Consequences:**
- Widget drag-drop commits to the wrong column after the panel opens or closes.
- Resize handles commit wrong widths.
- The ghost drop indicator appears shifted from the actual target.

**Prevention:**
1. The panel component must emit a Vue event after the CSS transition completes (`transitionend` listener → `$emit('panel-transition-end')`).
2. `DashboardRuntime` or `DashboardDesignerView` listens and calls an explicit `updateColWidth()` on `DashboardGrid` via a template ref exposed method (`defineExpose({ updateColWidth })`).
3. Also call `updateColWidth()` inside `nextTick` in the same toggle handler as a belt-and-suspenders measure.
4. Do not rely on `ResizeObserver` alone for this case.

**Detection:**
Collapse the panel, then immediately drag a widget. If it snaps to a column shifted by approximately `panelWidth / colWidth` columns to the left, this is the bug.

---

### Pitfall 3: Drop Coordinates Wrong During Panel CSS Transition

**What goes wrong:**
`clientToCanvas()` calls `canvasRef.getBoundingClientRect()` at the moment of `mouseup`. `getBoundingClientRect()` is always live — it reflects the element's current geometry at call time. The problem is that if `mouseup` fires during the panel CSS transition (before the panel has fully opened or closed), `getBoundingClientRect().left` returns an intermediate, in-flight value. The snap calculation uses this wrong `left` offset, placing the dropped widget 1–3 columns from the intended position. The user sees the widget land under the cursor during the drag ghost preview, but commit to a different location on drop.

**Why it happens:**
`getBoundingClientRect()` reads the layout as currently painted, which changes on every animation frame during a CSS width/margin transition.

**Prevention:**
Track `isPanelAnimating = ref(false)` in the parent component. Set it `true` on toggle initiation, `false` on `transitionend`. In the canvas's `onMouseUp` handler, if `isPanelAnimating.value` is `true`, defer the commit with `nextTick(() => commitDrop())` or skip it entirely (the user should not be dropping during animation — add visual feedback that the canvas is "settling").

---

## Moderate Pitfalls

---

### Pitfall 4: Stacking Context Conflicts Between Panel and Canvas Overlays

**What goes wrong:**
The canvas has a documented z-index hierarchy: grid items at `z-index: 10`, drag ghost at `z-index: 50`, maximize overlay at `z-index: 90`. `DashboardDesignerView` modals use `z-index: 50`, `1000`, and `2000`. If the side panel is given `overflow: hidden` (required for smooth collapse animation) on a `position: relative` element, it creates a **new stacking context**, isolating its children from the rest of the page's z-index ordering. The panel toggle button — which must remain visible when the panel is collapsed — may end up rendered beneath canvas grid items if placed inside the overflow-clipping container.

Additionally, if the panel is given `z-index: 5` (below grid items at `10`), users cannot interact with the panel's scrollbar or filter input when canvas widgets visually overlap the panel edge.

**Why it happens:**
`overflow: hidden` on a positioned element always creates a stacking context in Chromium (and most browsers). `transform`, `opacity < 1`, and `will-change` also do. Collapse animations almost always use one of these properties.

**Prevention:**
1. Place the panel toggle button **outside** the panel's overflow-hidden container, as a sibling rendered at the same flex level as the panel itself.
2. Assign the panel `z-index: 20` (above grid items at `10`, below drag ghost at `50`).
3. Document the project z-index ladder explicitly before implementation:
   - Panel: `20`
   - Canvas grid items: `10`
   - Canvas drag ghost: `50`
   - Canvas maximize overlay: `90`
   - Modals: `1000` and `2000`

---

### Pitfall 5: vuedraggable / SortableJS Global Listener Interference

**What goes wrong:**
If vuedraggable (vue.draggable.next, based on SortableJS) is introduced for the panel's table list (to provide sortability or grouped list behavior), SortableJS registers a global `pointerdown` listener on `document`. This listener runs before Vue component handlers and evaluates whether any `pointerdown` event matches one of its managed list items. Even when dragging a canvas widget (entirely unrelated to the panel), SortableJS inspects the event target. On lists with many items, this evaluation adds a measurable overhead per `mousedown`. More critically, SortableJS's `filter` option can silently suppress certain `pointerdown` events if misconfigured.

**Why it happens:**
SortableJS uses `document.addEventListener('pointerdown', ...)` for global drag detection. There is no way to scope SortableJS to only its own subtree at the event capture level.

**Prevention:**
Do not use vuedraggable for the panel's table list. The list does not need to be sortable — items only need to be draggable *out* to the canvas. A plain `@mousedown` on each table item, combined with a `panelDrag` Pinia state, achieves the required behavior without any library. This avoids the entire class of SortableJS global-listener conflicts and keeps the panel's drag implementation architecturally consistent with the canvas.

---

### Pitfall 6: Panel Collapse Animation Clips Item Drag Ghosts and Hover Shadows

**What goes wrong:**
A smooth collapse animation using `transition: width 0.3s ease` requires `overflow: hidden` on the panel. During the animation, any element that visually protrudes outside the panel's box (hover shadows with a wide spread, tooltips positioned with `position: absolute`, or custom drag ghost elements appended as children of the panel) gets clipped mid-animation, creating a visible pop or disappearing artifact. Conversely, if `overflow: hidden` is omitted to preserve hover shadows, list items "bleed" over the canvas area during the transition, intercepting click events on canvas widgets and preventing widget selection.

**Prevention:**
Use `max-width` transition instead of `width` to preserve `overflow: visible` on children during the animation:
```css
.panel { max-width: 280px; overflow: visible; transition: max-width 0.3s ease; }
.panel.collapsed { max-width: 0; overflow: hidden; }
```
This way, overflow is only clipped in the final collapsed state, not during the animation frames. The toggle button placed outside the panel as a sibling (see Pitfall 4) is not affected.

---

### Pitfall 7: Canvas Empty-State Copy Refers to the Wrong Action

**What goes wrong:**
`DashboardGrid.vue` renders the following copy in its empty state (design mode):
```
Haz clic en **+ Añadir widget** para comenzar
```
Once the panel ships, the canonical action for adding a table-based widget is dragging from the panel. The empty state copy will mislead users into looking for the `+` button. This is a small one-line change but is easy to defer and then forgotten, creating permanently wrong onboarding UX.

**Prevention:**
Update the empty-state copy in `DashboardGrid.vue` in the same phase that ships the panel, not in a follow-up polish phase. Suggested copy: `"Arrastra una tabla desde el panel izquierdo para comenzar"`.

---

### Pitfall 8: `document` Event Listeners Leaked on Panel Unmount

**What goes wrong:**
If the panel's drag initiation logic registers `mousemove` and `mouseup` on `document` (mirroring the canvas approach), and the component is unmounted while a drag is in progress (e.g., due to a route change or dashboard navigation), the handlers are never removed. The orphaned `mousemove` handler then fires on the next canvas drag and may corrupt the canvas's `dragState` (e.g., setting `panelDrag.active = true` unexpectedly, causing the canvas to interpret a widget drag as a table drop).

**Why it happens:**
The canvas correctly cleans up in `onBeforeUnmount`. A new panel component written without that awareness will omit cleanup, especially when the drag implementation is added incrementally.

**Prevention:**
Encapsulate all `document.addEventListener` calls in a `usePanelDrag()` composable that pairs each `onMounted` registration with its `onBeforeUnmount` removal using the exact same function reference. The composable pattern makes cleanup structurally inseparable from registration.

---

## Minor Pitfalls

---

### Pitfall 9: Filter Input Triggers Canvas Keyboard Shortcuts

**What goes wrong:**
If the dashboard canvas acquires keyboard shortcuts in a future phase (Delete to remove a selected widget, arrow keys to nudge position), and the panel's filter `<input>` is focused while a widget is selected, the keydown event will bubble up and trigger the canvas shortcut. A user typing in the filter box to search tables could inadvertently delete the selected widget.

**Prevention:**
Add `@keydown.stop` on the filter input element from day one. This is a one-attribute fix but trivially easy to miss. Do not defer to after keyboard shortcuts are added.

---

### Pitfall 10: Collapsible Group State Resets on Navigation

**What goes wrong:**
The feature spec requires Hechos and Dimensiones groups to be individually collapsible. If group-open state is held only in `ref()` values within the panel component, it resets to default every time the user navigates to the dashboard list and back. A user who collapses Dimensiones to reduce visual noise will find both groups expanded again when they re-enter the designer.

**Prevention:**
Persist the `openGroups` map in `localStorage` or the `useUIStore` Pinia store. Key: `panel.openGroups`. Default: both groups open. This is a 3-line persistence call — trivial at creation time, painful to retrofit after release.

---

### Pitfall 11: "Grabbing" Cursor State Stuck After Drop

**What goes wrong:**
When `mousedown` starts a drag, the implementation sets `document.body.style.cursor = 'grabbing'` and `document.body.style.userSelect = 'none'` to prevent text selection during the drag. If the `mouseup` cleanup path does not explicitly reset both of these, the grabbing cursor persists until the user moves the mouse over an element with an explicit `cursor` rule. `user-select: none` on `document.body` also prevents text selection in other views until the next page reload.

**Prevention:**
In `onMouseUp` cleanup (both the panel drag composable and the canvas's existing `onMouseUp` for symmetry), always reset:
```javascript
document.body.style.cursor = ''
document.body.style.userSelect = ''
```
Do this unconditionally, not only when a drop is accepted.

---

### Pitfall 12: Duplicate Table Instances Not Visually Distinguished

**What goes wrong:**
The feature spec explicitly requires allowing the same table to be added to the canvas more than once. If both instances render with the same `tableId` and the same display label, the designer cannot tell which instance they are configuring when they click on one. The configure panel or the table node's title will show the same name for both, making it impossible to set up different configurations (e.g., `Ventas 2023` vs `Ventas 2024`) without the user manually renaming them.

**Prevention:**
When a table is dropped onto the canvas for the second (or later) time, auto-append a numeric suffix to the instance title: `Ventas (2)`, `Ventas (3)`. The underlying `tableId` is the same, but the widget's `title` field is unique. Allow renaming in the properties panel.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Panel layout and collapse CSS | Pitfall 2 (stale colWidth), Pitfall 6 (overflow bleed) | Use `transitionend` → explicit `updateColWidth()`; use `max-width` transition |
| Panel item drag implementation | Pitfall 1 (HTML5 DnD vs mouse), Pitfall 5 (SortableJS) | Use mouse-event approach only; do not introduce vuedraggable |
| Drop coordinate calculation on canvas | Pitfall 3 (stale clientX), Pitfall 2 (stale colWidth) | Guard drop during animation with `isPanelAnimating`; call `updateColWidth()` explicitly after toggle |
| z-index and overlay coordination | Pitfall 4 (stacking context) | Document z-index ladder; place toggle button outside overflow container |
| Filter input and keyboard | Pitfall 9 (keyboard event bleed) | Add `@keydown.stop` on filter input at creation time |
| UX polish | Pitfall 7 (wrong empty-state copy), Pitfall 10 (group state), Pitfall 11 (stuck cursor), Pitfall 12 (duplicate names) | Address in same phase as panel, not deferred |
| Composable lifecycle | Pitfall 8 (leaked listeners) | Encapsulate in `usePanelDrag()` composable with paired `onBeforeUnmount` cleanup |

---

## Implementation Decision Summary: Native Mouse Events over HTML5 DnD

The recommended drag implementation for panel items uses the same `mousedown`/`mousemove`/`mouseup` pattern already proven in `DashboardGrid.vue`. The interface:

1. `@mousedown` on a table item: set `panelDragStore.start({ tableId, tableName, type })`. Apply `cursor: grabbing` on `document.body`.
2. The canvas `onMouseUp` handler (already registered on `document`): check `panelDragStore.active`. If true, compute the drop grid position using the existing `clientToCanvas()` + `snapCol()` / `snapRow()` math and call `dashboardStore.addWidget(...)` with the table's definition.
3. On `mouseup` anywhere: call `panelDragStore.cancel()` which clears `active` and resets cursor/userSelect.

**Why this is the right approach:**

- Shares the existing coordinate math already verified correct — no new coordinate system.
- Avoids the HTML5 DnD pointer ownership conflict (Pitfall 1).
- Avoids SortableJS global listener overhead (Pitfall 5).
- No DataTransfer / ghost image cross-browser quirks (Firefox requires ghost image elements to be in the DOM).
- The implementation is ~40 lines of vanilla event handling — far less surface area than a library dependency.
- Consistent with the project's no-external-CSS-framework, no-TypeScript conventions.

---

## Sources

- `DashboardGrid.vue` — direct code analysis: custom `dragState`, `resizeState`, `onMouseMove`/`onMouseUp` on `document`, `clientToCanvas()`, `ResizeObserver` on `canvasRef` — **HIGH confidence**
- `DashboardRuntime.vue` — direct code analysis: `flex: 1` `grid-container`, `z-index: 20` on `runtime-filters` — **HIGH confidence**
- `AppLayout.vue` — direct code analysis: `margin-left` transition on sidebar collapse — **HIGH confidence**
- [HTML5 DnD mousemove suppression — javascript.info](https://javascript.info/mouse-drag-and-drop) — **HIGH confidence**
- [HTML5 DnD limitations and API problems — sam.today](https://www.sam.today/blog/html5-dnd-the-api-that-is-gaslighting-you) — **MEDIUM confidence**
- [SortableJS global event registration — GitHub](https://github.com/SortableJS/Vue.Draggable) — **MEDIUM confidence**
- [ResizeObserver API async callback timing — MDN](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver) — **HIGH confidence**
- [CSS stacking contexts and overflow:hidden — web.dev](https://web.dev/learn/css/z-index) — **HIGH confidence**
- [CSS transitions and layout shift — corewebvitals.io](https://www.corewebvitals.io/pagespeed/layout-shift-caused-by-css-transitions) — **MEDIUM confidence**
- [DataTransfer setDragImage cross-browser quirks — MDN](https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer/setDragImage) — **HIGH confidence**
- [Canvas + collapsible panel resize interaction — Babylon.js forum](https://forum.babylonjs.com/t/babylonjs-canvas-in-a-horizontally-collapsible-panel-with-animation/11944) — **MEDIUM confidence** (confirms the ResizeObserver timing issue with panel animations)

---
*Pitfalls research for: v2.0 BI Analyst — Feat 04: Collapsible Panel with DnD*
*Researched: 2026-05-31*
