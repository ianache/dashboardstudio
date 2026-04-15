# Project Roadmap: Visualizacion Design Improvements

## Phase 1: Setup & UI Scaffolding
**Goal:** Establish the foundation and layout for the new visualization configuration interface.
**Plans:** 2 plans
- [x] phase01-01-PLAN.md — Store & Routing setup
- [x] phase01-02-PLAN.md — Base UI Scaffolding (3-column layout)

**Requirements:** [FR-01, FR-02, NFR-Modern Refinement]

## Phase 2: Drag-and-Drop Core
**Goal:** Implement the drag-and-drop interface for configuring visualizations.
**Plans:** 2 plans
- [ ] phase02-01-PLAN.md — Source Panel & Draggable Items
- [ ] phase02-02-PLAN.md — Drop Zones & Validation

**Requirements:** [FR-01, NFR-Modern Refinement]

## Phase 3: Real-time Preview & Charting
- [ ] Integrate `useCubeQuery` for dynamic data fetching.
- [ ] Connect state to `vue-echarts` Preview component.
- [ ] Implement Chart Type Selector (Bar, Line, Pie, etc.).
- [ ] Add "Loading" and "No Data" states for the preview.

## Phase 4: Refinement & Integration
- [ ] Implement Collapsible Config Panel.
- [ ] Add Advanced Metric Configuration Modal (aliases, formatting).
- [ ] Add "Quick Filters" logic.
- [ ] Final UI Polish (spacing, shadows, 8px grid alignment).
- [ ] "Save to Dashboard" functionality.

## Phase 5: Testing & Deployment
- [ ] End-to-end testing of the configuration-to-save flow.
- [ ] Cross-browser validation.
- [ ] Final review against `diseÃ±o_visualizacion.jpeg`.
