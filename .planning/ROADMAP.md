# Project Roadmap: Integration Flow Execution Visualizer

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-14. Core & Integration Flows | 24/24 | Completed | 2026-05-14 |
| 15-17. Connection Management | 3/3 | Completed | 2026-05-15 |
| 18. Execution Visualizer Popup | 0/1 | Planned | |

---

## Milestone: Integration Flow Execution Visualizer (Popup)

### Phase 18: Frontend - Execution Visualizer Popup
**Goal**: Implement the reusable popup component and the node badges/hovers.
**Requirements**: FR-02, FR-03, FR-04, TR-01, TR-03
**Plans**: 1
- [ ] 18-01-PLAN.md — Create visualizer popup and adapt canvas for read-only visualization.

### Phase 19: Integration & Data Wiring
**Goal**: Add the "lupa" icon to the integrations table and wire it to fetch historical data.
**Requirements**: FR-01, FR-05, TR-02, TR-04
**Plans**: 19-01-PLAN.md

---

## Phase Details

### Phase 18: Frontend - Execution Visualizer Popup
- [ ] Create `FlowExecutionPopup.vue` as a modal wrapper.
- [ ] Adapt `FlowEditorCanvas.vue` to support a `readOnly` mode that hides toolbars/side panels.
- [ ] Implement `fec-node-badge--left` for execution time.
- [ ] Implement `fec-node-tooltip` for hover start/end times.
- [ ] Ensure SVG connections also reflect the execution state (already partially implemented).

### Phase 19: Integration & Data Wiring
- [ ] Update `IntegrationsView.vue` to include the "ACCIONES" column and "lupa" icon.
- [ ] Implement logic to fetch the latest execution ID for a given flow.
- [ ] Pass the execution data (node statuses, times) to the visualizer popup.
- [ ] Final end-to-end testing of the visualization flow.
