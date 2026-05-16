# Project Roadmap: ODS PostgreSQL Upsert & Dynamic Discovery

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-28. Core & Extensions | 28/28 | Completed | 2026-05-17 |
| 29. Metadata Inspection API | 1/2 | In Progress|  |
| 30. ODS Node UI Enhancement | 0/1 | Pending | - |
| 31. ODS Execution Engine | 0/1 | Pending | - |

---

## Milestone: ODS PostgreSQL Upsert & Dynamic Discovery

### Phase 29: Metadata Inspection API
**Goal**: Implement backend services to inspect database schemas, tables, and columns.
**Requirements**: FR-01, FR-04, TR-01
**Status**: In Progress
**Plans**: 2 plans
- [ ] 29-01-PLAN.md — Implement MetadataService with PostgreSQL support.
- [ ] 29-02-PLAN.md — Expose metadata inspection via FastAPI endpoints.

### Phase 30: ODS Node UI Enhancement
**Goal**: Update the ODS PostgreSQL node properties with dynamic selectors and conditional fields.
**Requirements**: FR-01, FR-02, FR-03, FR-04, TR-02, TR-03, UI
**Status**: Pending

### Phase 31: ODS Execution Engine
**Goal**: Implement the actual write/upsert logic in the backend with Deno delegation.
**Requirements**: FR-05, FR-06, TR-04
**Status**: Pending

---

## Phase Details

### Phase 29: Metadata Inspection API
- [x] Create `metadata_service.py` to handle database metadata fetching (PostgreSQL focus).
- [x] Add endpoints to `data_sources.py` for listing tables/columns.
- [ ] Test API responses with real connection credentials.

### Phase 30: ODS Node UI Enhancement
- [ ] Update `ods_pg` tool definition in DB: Add `connection_id`, `identity_fields`, and change `table` to dynamic.
- [ ] Refactor `FlowEditorCanvas.vue` properties renderer to handle dynamic data fetching and "Refresh" buttons.
- [ ] Implement conditional visibility logic in the properties panel (show/hide identity fields).

### Phase 31: ODS Execution Engine
- [ ] Create `ods_executor.py` with support for Append, Overwrite, and Upsert (with conflict resolution).
- [ ] Update Deno runner to emit `EXEC_ODS` signal.
- [ ] Update Python flow runner to intercept `EXEC_ODS` and call `ods_executor.py`.
- [ ] Final end-to-end testing of data loading with upserts.
