# Project Roadmap: Visualizacion Design Improvements

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-6. Core Viz & Multi-Diagram | 16/17 | Completed | 2026-05-13 |
| 7-11. Integration Flows (Deno) | 5/5 | Completed | 2026-05-14 |
| 12. Backend Status Reporting | 1/1 | Completed | 2026-05-14 |
| 13. UI Execution State & Nodos | 1/1 | Completed | 2026-05-14 |
| 14. UI Connection Highlighting | 1/1 | Completed | 2026-05-14 |
| 15. Backend - Connection Data Model | 0/1 | Planned | |
| 16. Backend - Connection Testing | 0/1 | Planned | |
| 17. Frontend - Connections UI | 0/2 | Planned | |

## Milestone: Flow Execution Visualization

### Phase 12: Backend Status Reporting
**Goal**: Update the runner and backend service to emit structured node-level status events.
**Requirements**: FR-01, TR-01
**Plans**: 12-01-PLAN.md

### Phase 13: UI Execution State & Nodos
**Goal**: Implement the execution state in the frontend and show visual feedback on nodes (borders and badges).
**Requirements**: FR-02, FR-03, FR-05, TR-02, TR-03
**Plans**: 13-01-PLAN.md

### Phase 14: UI Connection Highlighting
**Goal**: Visualize the execution sequence by coloring connections as they are activated.
**Requirements**: FR-04, TR-02
**Plans**: 14-01-PLAN.md

---

## Phase Details

### Phase 12: Backend Status Reporting
- [ ] Update `runner.ts` to emit `NODE_STATUS:<id>:<status>`.
- [ ] Update `deno_service.py` to parse these tokens and yield `type: node_status` events.
- [ ] Verify using the diagnostic scripts.

### Phase 13: UI Execution State & Nodos
- [ ] Add `nodeExecutionStatus` reactive map to `FlowEditorCanvas.vue`.
- [ ] Update WebSocket listener to populate this map.
- [ ] Add dynamic classes to node elements for `executing`, `success`, `error`.
- [ ] Implement badge elements in node header/body.

### Phase 14: UI Connection Highlighting
- [ ] Calculate which connections are "active" based on source node status.
- [ ] Add `is-active` class to connection SVG paths.
- [ ] Final polish of animations and transitions.

---

## Milestone: Connection Management & Centralized Credentials

### Phase 15: Backend - Connection Data Model
- [ ] Add `connection_config` JSON column to `DataSource` model.
- [ ] Implement Pydantic Discriminated Unions for connection types.
- [ ] Create recursive encryption/decryption helper for sensitive fields.
- [ ] Update `DataSource` API endpoints to handle `connection_config`.

### Phase 16: Backend - Connection Testing Logic
- [ ] Implement `ConnectionStrategy` base class.
- [ ] Implement concrete strategies for SMTP, SQL (Postgres/MySQL), FTP/SFTP, HTTP.
- [ ] Create `/api/v1/data-sources/{id}/test` endpoint.

### Phase 17: Frontend - Connections UI & Navigation
- [ ] Add "Conexiones" to `SideMenu.vue`.
- [ ] Create `ConnectionsView.vue` with list and search.
- [ ] Implement `ConnectionEditModal.vue` with dynamic forms for each type.
