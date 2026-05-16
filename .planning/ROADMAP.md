# Project Roadmap: Resizable Properties Sidebar

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-21. Core & Early Milestones | 21/21 | Completed | 2026-05-16 |
| 22. Sidebar Resizability Implementation | 0/2 | Pending | - |

---

## Milestone: Resizable Properties Sidebar

### Phase 22: Sidebar Resizability Implementation
**Goal**: Implement drag-to-resize functionality for the right properties panel in `FlowEditorCanvas.vue`.
**Requirements**: FR-01, FR-02, FR-03, FR-04, FR-05, TR-01, TR-02, UI
**Status**: Pending

**Plans:**
- [ ] 22-01-PLAN.md — Core Resizing Logic (UI Handle + Mouse Events)
- [ ] 22-02-PLAN.md — Constraints, Persistence & Compatibility

---

## Phase Details

### Phase 22: Sidebar Resizability Implementation
- [x] Add state variables for `rightWidth` and `isResizingRight` in `FlowEditorCanvas.vue`.
- [x] Add the resize handle element in the template.
- [x] Implement `onResizeMousedown` to start tracking.
- [x] Update `onGlobalMousemove` to calculate the new width based on cursor position.
- [x] Update `onGlobalMouseup` to clean up the resizing state.
- [x] Apply the dynamic width to the `.fec-right` element.
- [x] Ensure compatibility with the collapsed state and different node types (JS Script wide mode).
