---
phase: 06-multi-diagram-dimensional-model
plan: 02
subsystem: ui
tags: [pinia, vue3, dimensional-model, diagrams, store]

# Dependency graph
requires:
  - phase: 06-multi-diagram-dimensional-model
    provides: "06-01 backend diagrams column — store now reads/writes diagrams field"
provides:
  - "Backward-compatible migration: old models without diagrams auto-generate a default 'Principal' main diagram"
  - "Seven diagram CRUD actions on useDimensionalModelStore: createDiagram, renameDiagram, updateDiagramDescription, deleteDiagram, addNodeToDiagram, removeNodeFromDiagram, updateDiagramNodePosition"
  - "addNode() keeps main diagram diagramNodes in sync"
  - "deleteNode() sweeps dangling nodeId refs from all diagrams"
  - "diagrams[] included in PUT payload via _transformModelFrontendToBackend"
affects: [06-03-PLAN, 06-04-PLAN, 06-05-PLAN, 06-06-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-diagram diagramNodes array holds {nodeId, x, y} entries — canonical node data stays in model.nodes"
    - "isMain flag on diagram object guards main diagram from deletion and removeNodeFromDiagram"
    - "Migration pattern: check Array.isArray(m.diagrams) && m.diagrams.length in transform, fall back to synthetic default"

key-files:
  created: []
  modified:
    - dashboard-app/src/stores/dimensionalModel.js

key-decisions:
  - "MD-05 (move nodes between diagrams) satisfied by addNodeToDiagram/removeNodeFromDiagram modal flow, not drag-and-drop (per 06-RESEARCH.md recommendation)"
  - "Main diagram protected: deleteDiagram and removeNodeFromDiagram both no-op when isMain=true"
  - "addGlobalDimRef does NOT sync to main diagram — only the plain addNode path does (global refs tracked separately)"

patterns-established:
  - "Diagram sync pattern: after m.nodes.push(), find mainDiagram by isMain flag and push matching diagramNode entry"
  - "Sweep pattern: deleteNode sweeps all diagrams with filter(dn => dn.nodeId !== nodeId) to avoid orphan refs"

requirements-completed: [MD-01, MD-02, MD-03, MD-05, MD-06]

# Metrics
duration: ~30min
completed: 2026-04-17
---

# Phase 06 Plan 02: Store Diagram CRUD Actions + Migration Logic Summary

**Pinia store extended with backward-compatible diagram migration and 7 CRUD actions, making diagrams[] the single source of truth for multi-diagram layout without UI changes**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-04-17
- **Completed:** 2026-04-17
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `_transformBackendToFrontend` now extracts `const nodes` before the return so migration logic can reference it; old models (no diagrams field) auto-generate a single `'Principal'` main diagram from existing nodes
- `_transformModelFrontendToBackend` includes `diagrams: model.diagrams || []` in every PUT payload so diagram state persists to backend
- `addNode()` pushes a matching `{ nodeId, x, y }` entry to the main diagram after adding the canonical node; `deleteNode()` sweeps all diagrams removing dangling nodeId entries
- Seven new store actions give Wave 2 UI components a complete diagram management API

## Task Commits

Each task was committed atomically:

1. **Task 1: Add migration logic and diagrams to transform functions** - `f9f4e28` (feat)
2. **Task 2: Add diagram CRUD actions to the store** - `64e1b1a` (feat)

## Files Created/Modified

- `dashboard-app/src/stores/dimensionalModel.js` — Extended with diagrams migration in transform functions, addNode/deleteNode sync hooks, and 7 new diagram CRUD actions

## Decisions Made

- MD-05 (moving nodes between diagrams) is satisfied by `addNodeToDiagram` / `removeNodeFromDiagram` rather than drag-and-drop, as recommended in 06-RESEARCH.md. This avoids cross-tab D&D complexity with minimal UX trade-off.
- Main diagram is protected by `isMain` flag: `deleteDiagram` and `removeNodeFromDiagram` both silently return when called against a main diagram.
- `addGlobalDimRef` was intentionally left without main-diagram sync — global dim refs have their own positional tracking path and are not treated as standard node adds.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Store is complete and contracts are stable: DiagramTabBar (06-03) and DiagramCanvas can bind directly to `model.diagrams[]` and call CRUD actions
- `diagrams[]` will be persisted on every manual Save (existing "Save" button triggers `saveModelToBackend` which calls `updateModel` → `_transformModelFrontendToBackend`)
- No blockers for Wave 2 UI plans (06-03 through 06-06)

---
*Phase: 06-multi-diagram-dimensional-model*
*Completed: 2026-04-17*
