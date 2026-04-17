# Project Roadmap: Visualizacion Design Improvements

## Phase 1: Setup & UI Scaffolding
**Goal:** Establish the foundation and layout for the new visualization configuration interface.
- [x] phase01-01-PLAN.md — Store & Routing setup
- [x] phase01-02-PLAN.md — Base UI Scaffolding (3-column layout)

## Phase 2: Drag-and-Drop Core
**Goal:** Implement the drag-and-drop interface for configuring visualizations.
- [x] phase02-01-PLAN.md — Source Panel & Draggable Items
- [x] phase02-02-PLAN.md — Drop Zones & Validation

## Phase 3: Real-time Preview & Charting
**Goal:** Integrate live data and dynamic preview.
- [x] phase03-01 — Integrate `useCubeQuery` for dynamic data fetching.
- [x] phase03-02 — Connect state to `vue-echarts` Preview component.
- [x] phase03-03 — Implement Chart Type Selector.
- [x] phase03-04 — Add "Loading" and "No Data" states for the preview.

## Phase 4: Refinement & Integration
**Goal:** Finalize the user experience and ensure persistence.
- [x] phase04-01-PLAN.md — Save to Dashboard & UI Polish
- [x] phase04-02-PLAN.md — Advanced Metric Configuration (aliases, formatting)
- [x] phase04-03-PLAN.md — Final Polish & Quick Filters

## Phase 5: Testing & Deployment
- [ ] phase05-01-PLAN.md — End-to-end testing & Validation
- [ ] phase05-02-PLAN.md — Cross-browser & Final Review

### Phase 6: Multi-diagram Dimensional Model

**Goal:** Extend the Dimensional Model editor so each model can have one permanent main diagram plus N user-managed sub-diagrams showing node subsets, with shared canonical node data and Markdown-enabled diagram descriptions.
**Requirements**: MD-01, MD-02, MD-03, MD-04, MD-05, MD-06, MD-07
**Depends on:** Phase 5
**Plans:** 6 plans

Plans:
- [ ] 06-01-PLAN.md — Backend diagrams column + Pydantic schemas
- [ ] 06-02-PLAN.md — Store diagram CRUD actions + migration logic
- [ ] 06-03-PLAN.md — DiagramTabBar + EditorView canvas refactor
- [ ] 06-04-PLAN.md — Install marked/DOMPurify + DiagramPropsPanel component
- [ ] 06-05-PLAN.md — Wire DiagramPropsPanel + AddNodeToDiagramModal into EditorView
- [ ] 06-06-PLAN.md — Automated smoke checks + end-to-end human verification
