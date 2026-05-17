# Project Roadmap: ODS PostgreSQL Upsert & Dynamic Discovery

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-28. Core & Extensions | 28/28 | Completed | 2026-05-17 |
| 29. Metadata Inspection API | 2/2 | Complete   | 2026-05-16 |
| 30. ODS Node UI Enhancement | 1/1 | Complete | 2026-05-16 |
| 31. ODS Execution Engine | 3/3 | Complete    | 2026-05-17 |
| 32. Email Node Implementation | 1/3 | In Progress | 2026-05-16 |

---

## Milestone: ODS PostgreSQL Upsert & Dynamic Discovery

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

**Wave Structure:**
- Wave 1: 31-01 — Core executor (no dependencies)
- Wave 2: 31-02 — Deno integration (depends on 31-01)
- Wave 3: 31-03 — Validation & testing (depends on 31-02)

---

## Phase Details

### Phase 29: Metadata Inspection API
- [x] Create `metadata_service.py` to handle database metadata fetching (PostgreSQL focus).
- [x] Add endpoints to `data_sources.py` for listing tables/columns.
- [x] Test API responses with mocked connection credentials.

### Phase 30: ODS Node UI Enhancement
- [x] Plan: `.planning/phases/30-ods-node-ui-enhancement/PLAN.md`
- [x] Migration: `backend/alembic/versions/030_update_ods_pg_tool.py` — Updated `ods_pg` tool with `connection_id`, `identity_fields`, and dynamic `table` selector.
- [x] UI: `dashboard-app/src/components/editor/FlowEditorCanvas.vue` — Extended property renderer with:
  - `dynamic_select` type with refresh button
  - `multi_select` type with checkbox list for identity fields
  - `show_if` conditional visibility logic
  - Cascading dependency clearing (connection_id → table → identity_fields)
  - Auto-fetch options when dependencies are met

### Phase 31: ODS Execution Engine
**Goal**: Implement the actual write/upsert logic in the backend with Deno delegation.
**Requirements**: FR-05, FR-06, TR-04, EXEC-01 through EXEC-21
**Status**: In Progress (2/3 plans complete)
**Plans**: 3 plans

**Phase 31 Plan Details:**

**Plan 31-01: Core ODSExecutor Service (Wave 1)**
Requirements: EXEC-01, EXEC-02, EXEC-03, EXEC-04, EXEC-05, EXEC-10, EXEC-11, EXEC-12, EXEC-13, EXEC-14, EXEC-15, EXEC-16
Files: `backend/app/services/ods_executor.py`
- Create ODSExecutor class with data models (ODSConfig, ODSResult, ODSError, WriteMode)
- Implement Append operation (INSERT without conflict checking)
- Implement Overwrite operation (TRUNCATE + INSERT)
- Implement Upsert operation (INSERT ON CONFLICT DO UPDATE with composite keys)
- Batch processing with per-batch transaction isolation (default 1000 rows)
- Connection pooling via asyncpg
- Retry logic with exponential backoff (3 attempts) for deadlocks, timeouts, connection errors
- Error classification: Connection, UniqueViolation, FKViolation, TypeMismatch, Timeout, Deadlock
- Row counts tracking (affected, inserted, updated)
- Execution duration tracking per batch and total

**Plan 31-02: Deno Integration & Signal Protocol (Wave 2)**
Requirements: EXEC-06, EXEC-07, EXEC-08, EXEC-09, TR-04
Depends: 31-01
Files: `backend/app/runtime/runner.ts`, `backend/app/services/deno_service.py`
- Modify runner.ts to emit EXEC_ODS signal when encountering ods_pg nodes
- EXEC_ODS payload includes: node_id, operation, connection_id, data, identity_fields
- NaN/Infinity validation in Deno before payload emission (Pitfall 3 prevention)
- BigInt conversion to strings in Deno
- Modify deno_service.py to intercept EXEC_ODS signals
- Parse EXEC_ODS header and EXEC_ODS_PAYLOAD JSON
- Resolve connection credentials via DataSource service
- Delegate execution to ODSExecutor
- Stream results back through WebSocket (type: "ods_result")
- Update API endpoint to pass db session to run_flow_stream

**Plan 31-03: Validation, Testing & Hardening (Wave 3)**
Requirements: EXEC-17, EXEC-18, EXEC-19, EXEC-20, EXEC-21, FR-05, FR-06
Depends: 31-02
Files: `backend/app/services/ods_executor.py`, `backend/app/services/destination_executor.py`, `backend/tests/test_ods_executor.py`
- Schema and table existence validation before execution
- Upsert unique constraint validation (prevent ON CONFLICT failures - Pitfall 6)
- Strict JSON payload validation (no NaN/Infinity - Pitfall 3)
- Configurable statement timeouts per operation type (5min/30min/10min - Pitfall 7)
- Error logging to NodeExecutionLogs with batch context
- Deprecate legacy destination_executor.py with warnings
- Create test_ods_executor.py with comprehensive unit tests:
  - Data model tests
  - Validation tests (config, records, NaN/Infinity rejection)
  - Query building tests (INSERT, UPSERT with composite keys)
  - Operation tests (Append, Overwrite, Upsert)
  - Batch processing tests
  - Error handling and retry tests

**Success Criteria:**
1. User can execute flows with ODS PostgreSQL nodes and data is written to database
2. All write modes work: Append, Overwrite, Upsert (Merge deferred to v2)
3. Upsert correctly handles single and composite identity fields
4. Batch processing works with configurable sizes (1-10000 rows)
5. Deadlock prevention: records sorted by identity_fields before upsert
6. Errors are properly classified and logged with batch context
7. Schema/table existence validated before execution
8. Unique constraints validated for upsert operations
9. Execution results visible in UI with row counts via WebSocket
10. Legacy destination_executor.py deprecated
11. Unit tests pass with >80% coverage of ODSExecutor

## Milestone: v1.7 Email Node with Dynamic Templates

### Phase 32: Email Node Implementation
**Goal**: Implementar el nodo Email con soporte para plantillas dinámicas usando Jinja2, permitiendo el envío de correos con contenido generado dinámicamente desde el input del flujo.
**Requirements**: EMAIL-01 through EMAIL-24
**Status**: In Progress (1/3 plans complete)
**Plans**: 3 plans in 3 waves

**Phase 32 Details:**
- [x] 32-01-PLAN.md — Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration) - **COMPLETE**
- [ ] 32-02-PLAN.md — Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [ ] 32-03-PLAN.md — UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

**Plan Structure:**

**Plan 32-01: Core Email Service (Wave 1)** - **COMPLETE**
Requirements: EMAIL-01, EMAIL-02, EMAIL-03, EMAIL-04, EMAIL-05, EMAIL-06, EMAIL-07, EMAIL-08, EMAIL-09, EMAIL-15, EMAIL-16, EMAIL-17, EMAIL-18, EMAIL-19, EMAIL-20
Completed: 2026-05-16
Files: `backend/app/services/email_schemas.py`, `backend/app/services/email_executor.py`, `backend/pyproject.toml`
- ✅ Create EmailSchemas with Pydantic models (EmailPayload, EmailResult, EmailConfig, EmailContent)
- ✅ Create EmailExecutor class with Jinja2 SandboxedEnvironment for secure templating
- ✅ Implement template rendering with {{expression}}, {% for %}, {% if %} syntax
- ✅ Implement HTML sanitization using nh3 library
- ✅ Implement SMTP sending via DataSource connections
- ✅ Auto-escaping for XSS prevention
- ✅ Support for undefined variables (render as empty string via UndefinedSilently)
- ✅ Clear error messages for template syntax errors
- ✅ Comprehensive unit tests (44 tests passing)

**Plan 32-02: Deno Integration (Wave 2)**
Requirements: EMAIL-10, EMAIL-11, EMAIL-12, EMAIL-13, EMAIL-14
Depends: 32-01
Files: `backend/app/runtime/runner.ts`, `backend/app/services/deno_service.py`
- Modify runner.ts to emit EXEC_EMAIL signal when encountering email nodes
- EXEC_EMAIL payload includes: connection_id, recipients, subject_template, body_template, template_context
- Modify deno_service.py to intercept EXEC_EMAIL signals
- Parse EXEC_EMAIL header and EXEC_EMAIL_PAYLOAD JSON
- Resolve SMTP credentials via DataSource service
- Delegate execution to EmailExecutor
- Stream results back through WebSocket (type: "email_result")
- Template context from upstream nodes passed to executor

**Plan 32-03: UI & Testing (Wave 3)**
Requirements: EMAIL-21, EMAIL-22, EMAIL-23, EMAIL-24
Depends: 32-02
Files: `backend/alembic/versions/032_add_email_tool.py`, `dashboard-app/src/components/editor/FlowEditorCanvas.vue`, `backend/tests/test_email_executor.py`
- Create database migration for email node tool definition
- Add connection selector for SMTP DataSource
- Subject field with template support indicator
- Body field supporting HTML and text modes
- Recipients, CC, BCC fields with comma-separated email lists
- Template syntax hints in UI
- Comprehensive unit tests for template rendering, sanitization, and validation

**Wave Structure:**
- Wave 1: 32-01 — Core email service (no dependencies)
- Wave 2: 32-02 — Deno integration (depends on 32-01)
- Wave 3: 32-03 — UI & testing (depends on 32-02)

**Implementation Steps:**

**Step 1: Core Email Service**
- Create `backend/app/services/email_schemas.py` with Pydantic models
- Create `backend/app/services/email_executor.py` with Jinja2 templating
- Implement SMTP sending via DataSource connections
- Add template validation and error handling

**Step 2: Deno Integration**
- Modify `backend/app/runtime/runner.ts` to emit EXEC_EMAIL signal
- Modify `backend/app/services/deno_service.py` to intercept EXEC_EMAIL
- Implement template rendering context from upstream data
- Stream results back to UI via WebSocket

**Step 3: UI Implementation**
- Update database tool definition for email node with template fields
- Add email node properties panel in FlowEditorCanvas.vue
- Support for subject/body templates with syntax highlighting
- HTML sanitization with nh3 library

**Success Criteria:**
1. User can configure email node with SMTP connection
2. Subject supports {{expression}} template markers
3. Body supports {{expression}} and {% for %} loops for tables
4. HTML emails are sanitized before sending
5. Templates can access input data from upstream nodes
6. Error messages are clear for template syntax errors
7. Unit tests cover template rendering and email validation
