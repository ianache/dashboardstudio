# Project Roadmap: Execution Console Improvements

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-22. Core & Early Milestones | 23/23 | Completed | 2026-05-16 |
| 23. Global Icon Styling & Icon Fix | 1/1 | Completed | 2026-05-16 |
| 24. Console Vertical Resizability | 0/1 | In Progress | - |

---

## Milestone: Execution Console Improvements

### Phase 23: Global Icon Styling & Icon Fix
**Goal**: Ensure icons in `ExecutionConsole.vue` are rendered correctly by making `.msi` global.
**Requirements**: FR-01, FR-05, TR-01
**Status**: Completed (2026-05-16)

Plans:
- [x] 23-01-PLAN.md — Move .msi to global CSS and fix icons in ExecutionConsole

### Phase 24: Console Vertical Resizability
**Goal**: Implement drag-to-resize functionality for the bottom console panel in `FlowEditorCanvas.vue`.
**Requirements**: FR-02, FR-03, FR-04, TR-02, TR-03, UI
**Status**: In Progress

Plans:
- [ ] 24-01-PLAN.md — Implement vertical resizing for the bottom console panel

---

## Phase Details

### Phase 23: Global Icon Styling & Icon Fix
- [x] Move `.msi` class definition from `FlowEditorCanvas.vue` to `dashboard-app/src/assets/main.css`.
- [x] Verify `ExecutionConsole.vue` renders icons instead of text.
- [x] Clean up redundant `.msi` definitions in other components if they exist.

### Phase 24: Console Vertical Resizability
- [ ] Add `bottomHeight` and `isResizingBottom` refs to `FlowEditorCanvas.vue`.
- [ ] Implement `onResizeBottomMousedown` handler.
- [ ] Update `onGlobalMousemove` and `onGlobalMouseup` to handle bottom resizing.
- [ ] Apply dynamic height and styling to `.fec-bottom`.
- [ ] Add a resizer handle element at the top of the bottom panel.
