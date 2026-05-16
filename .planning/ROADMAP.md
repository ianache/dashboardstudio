# Project Roadmap: Graphical Visualization in Execution History

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-19. Core & Early Milestones | 19/19 | Completed | 2026-05-16 |
| 20. Execution History UI Refactor | 1/1 | In Progress | - |
| 21. History to Graph Integration | 0/1 | Pending | - |

---

## Milestone: Graphical Visualization in Execution History

### Phase 20: Execution History UI Refactor
**Goal**: Refactor `ExecutionHistoryModal.vue` to use icons for actions and prepare the UI for graphical triggers.
**Requirements**: FR-01, FR-03, UI
**Status**: In Progress

Plans:
- [ ] 20-01-PLAN.md — Update `ExecutionHistoryModal.vue` template, styles, and add placeholder logic for graph view.

### Phase 21: History to Graph Integration
**Goal**: Integrate `FlowExecutionPopup.vue` trigger from the history table and ensure data consistency.
**Requirements**: FR-02, FR-04, TR-01, TR-02
**Status**: Pending

---

## Phase Details

### Phase 20: Execution History UI Refactor
- [x] Update table header and rows in `ExecutionHistoryModal.vue`.
- [x] Replace "Ver" button with `description` icon.
- [x] Add `search` (lupa) icon button.
- [x] Style the action buttons for better UX.

### Phase 21: History to Graph Integration
- [ ] Implement `showGraph(execId)` logic in `ExecutionHistoryModal.vue`.
- [ ] Ensure `FlowExecutionPopup.vue` is globally accessible or properly imported.
- [ ] Pass `flowId` and `flowName` along with `executionId` to the popup.
- [ ] Verify that historical data is correctly rendered in the canvas.
