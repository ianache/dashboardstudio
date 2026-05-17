# Project Roadmap: ODS PostgreSQL Upsert & Dynamic Discovery

## Milestones

- ✅ **v1.6 ODS Execution Engine** — Phases 29-31 (shipped 2026-05-17)
- 🚧 **v1.7 Email Node** — Phase 32 (complete, pending archive)
- 📋 **v2.0** — Future milestones (planned)

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-28. Core & Extensions | 28/28 | Completed | 2026-05-17 |
| 29. Metadata Inspection API | 2/2 | Complete   | 2026-05-16 |
| 30. ODS Node UI Enhancement | 1/1 | Complete | 2026-05-16 |
| 31. ODS Execution Engine | 3/3 | Complete    | 2026-05-17 |
| 32. Email Node Implementation | 3/3 | Complete    | 2026-05-17 |

---

## ✅ v1.6 ODS Execution Engine (Phases 29-31) — SHIPPED 2026-05-17

<details>
<summary>View v1.6 Details</summary>

### Phase 29: Metadata Inspection API
**Goal**: Implement backend services to inspect database schemas, tables, and columns.
**Requirements**: FR-01, FR-04, TR-01
**Status**: Complete
**Plans**: 2 plans
- [x] 29-01-PLAN.md — Implement MetadataService with PostgreSQL support.
- [x] 29-02-PLAN.md — Expose metadata inspection via FastAPI endpoints.

### Phase 30: ODS Node UI Enhancement
**Goal**: Update the ODS PostgreSQL node properties with dynamic selectors and conditional fields.
**Requirements**: FR-01, FR-02, FR-03, FR-04, TR-02, TR-03, UI
**Status**: Ready
**Plans**: 1 plan
- [x] 30-PLAN.md — Update ODS node UI with dynamic selectors, refresh buttons, and conditional identity fields.

### Phase 31: ODS Execution Engine
**Goal**: Implement the actual write/upsert logic in the backend with Deno delegation.
**Requirements**: FR-05, FR-06, TR-04, EXEC-01 through EXEC-21
**Status**: Planned
**Plans**: 3 plans in 3 waves

**Plan Structure:**
- [x] 31-01-PLAN.md — Core ODSExecutor Service (ods_executor.py with Append, Overwrite, Upsert)
- [x] 31-02-PLAN.md — Deno Integration & Signal Protocol (runner.ts, deno_service.py)
- [x] 31-03-PLAN.md — Validation, Testing & Hardening (validation, logging, tests, deprecation)

**Archive:** `.planning/milestones/v1.6-ROADMAP.md`

</details>

---

## 🚧 v1.7 Email Node with Dynamic Templates (Phase 32)

### Phase 32: Email Node Implementation
**Goal**: Implementar el nodo Email con soporte para plantillas dinámicas usando Jinja2, permitiendo el envío de correos con contenido generado dinámicamente desde el input del flujo.
**Requirements**: EMAIL-01 through EMAIL-24
**Status**: Complete
**Plans**: 3 plans in 3 waves

**Plan Structure:**
- [x] 32-01-PLAN.md — Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration)
- [x] 32-02-PLAN.md — Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [x] 32-03-PLAN.md — UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

---

*For detailed milestone history, see .planning/milestones/*
*Last updated: 2026-05-17*
