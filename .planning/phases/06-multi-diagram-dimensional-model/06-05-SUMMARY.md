---
phase: 06-multi-diagram-dimensional-model
plan: "05"
subsystem: ui
tags: [vue, dimensional-model, diagrams, modal, props-panel, multi-diagram]

# Dependency graph
requires:
  - phase: 06-multi-diagram-dimensional-model
    plan: "03"
    provides: DiagramTabBar, activeDiagramId ref, activeDiagramNodes computed in EditorView
  - phase: 06-multi-diagram-dimensional-model
    plan: "04"
    provides: DiagramPropsPanel component (rename + description emits)
  - phase: 06-multi-diagram-dimensional-model
    plan: "02"
    provides: addNodeToDiagram, removeNodeFromDiagram, renameDiagram, updateDiagramDescription store actions

provides:
  - DiagramPropsPanel wired into EditorView right panel via canvas-click selectedDiagram ref
  - AddNodeToDiagramModal.vue — multi-select checklist of canonical nodes not yet in the active sub-diagram
  - removeNodeFromActiveDiagram handler — removes node from sub-diagram only, preserves canonical node
  - handleAddNodesToDiagram handler — iterates selected nodeIds and calls store action for each
  - Remove-from-diagram button on canvas nodes (visible only in sub-diagram mode, reveals on hover)
  - Empty sub-diagram hint with inline "Añadir tabla" button
  - Toolbar "Añadir tabla" button for sub-diagrams
  - watch(activeDiagramId) that clears all selections (node, rel, diagram) on tab switch

affects:
  - 06-06 — smoke checks and human verification will exercise all wiring added here

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "selectedDiagram ref as third selection state alongside selectedNode and selectedRel — right panel shows whichever is non-null"
    - "Canvas background click sets selectedDiagram = activeDiagram; node/rel clicks clear it"
    - "Modal computes availableNodes as model.nodes filtered by those not in activeDiagram.diagramNodes"
    - "Add-nodes flow: modal emits add-nodes(nodeIds[]), parent calls store.addNodeToDiagram per id"

key-files:
  created:
    - dashboard-app/src/components/dimensional-model/AddNodeToDiagramModal.vue
  modified:
    - dashboard-app/src/views/DimensionalModelEditorView.vue

key-decisions:
  - "selectedDiagram cleared on node/rel click to keep right panel exclusive — avoids ambiguous selection state"
  - "Add-nodes confirmed in modal then iterated in parent (not modal) to keep modal stateless after emit"
  - "Remove button opacity:0 by default, opacity:1 on canvas-node:hover — avoids UI clutter in dense diagrams"

patterns-established:
  - "Three-state right panel: selectedNode | selectedRel | selectedDiagram — first non-null wins via v-if chain"
  - "Modal pattern: backdrop click closes, footer cancel/confirm, confirm disabled when nothing selected"

requirements-completed: [MD-03, MD-05, MD-07]

# Metrics
duration: n/a (finalization pass — code already committed)
completed: 2026-04-17
---

# Phase 06 Plan 05: Wire DiagramPropsPanel + AddNodeToDiagramModal into EditorView Summary

**DiagramPropsPanel wired to canvas-click selection and AddNodeToDiagramModal added for sub-diagram node management, completing the multi-diagram editor UX in DimensionalModelEditorView.vue**

## Performance

- **Duration:** n/a (finalization pass — all code committed prior to summary)
- **Completed:** 2026-04-17
- **Tasks:** 3 (Task 1a, Task 1b, Task 2)
- **Files modified:** 2

## Accomplishments

- Added `selectedDiagram` ref and wired canvas-background click to set it, enabling DiagramPropsPanel to appear in the right panel without touching node/relationship selection
- Integrated DiagramPropsPanel as a third v-else-if branch in the right panel alongside existing node and relationship panels
- Created AddNodeToDiagramModal.vue with multi-select checklist that computes available nodes by diffing model.nodes against activeDiagram.diagramNodes
- Added hover-reveal "−" remove button on canvas nodes (sub-diagram mode only) wired to removeNodeFromActiveDiagram
- Added "Añadir tabla" toolbar button and empty sub-diagram hint both triggering showAddNodeModal
- Added watch(activeDiagramId) to clear all three selection refs on tab switch, preventing stale panel content

## Task Commits

Each task was committed atomically:

1. **Task 1a: Add selectedDiagram logic, handlers, and imports to EditorView script** - `a98a9d9` (feat)
2. **Task 1b: Apply template additions — DiagramPropsPanel branch, remove button, modal insertion** - `9c1b07d` (feat)
3. **Task 2: Create AddNodeToDiagramModal component** - `fa60d1e` (feat)

## Files Created/Modified

- `dashboard-app/src/views/DimensionalModelEditorView.vue` — Added selectedDiagram + showAddNodeModal refs, imports for DiagramPropsPanel and AddNodeToDiagramModal, onCanvasClick extension, watch(activeDiagramId), handleDiagramRename, handleDiagramDescription, removeNodeFromActiveDiagram, handleAddNodesToDiagram handlers; template: right panel v-if extended, DiagramPropsPanel branch, remove button on nodes, AddNodeToDiagramModal insertion, empty sub-diagram hint, toolbar button, CSS for node-btn-remove-diagram and sub-diagram-hint
- `dashboard-app/src/components/dimensional-model/AddNodeToDiagramModal.vue` — New modal component: availableNodes computed (canonical minus already-in-diagram), multi-select checklist with type badges, confirm emits add-nodes(nodeIds[]), cancel/backdrop close

## Decisions Made

- `selectedDiagram` is cleared whenever a node or relationship is clicked, keeping the right panel exclusive to one selection type at a time — avoids ambiguous multi-panel state
- The modal emits `add-nodes` with selected nodeIds and the parent (`EditorView`) iterates them calling `addNodeToDiagram` per id — modal remains stateless after emit
- Remove button uses `opacity: 0` default with `opacity: 1` on `.canvas-node:hover` to reduce visual noise in diagrams with many nodes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All multi-diagram UX is now wired end-to-end: tabs (Plan 03), diagram props panel (Plan 04), node add/remove modal (Plan 05)
- Plan 06-06 can proceed immediately: automated smoke checks and human verification of the complete flow
- No blockers or concerns

---
*Phase: 06-multi-diagram-dimensional-model*
*Completed: 2026-04-17*
