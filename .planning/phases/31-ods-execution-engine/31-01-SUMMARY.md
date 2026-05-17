---
phase: 31-ods-execution-engine
plan: 01
subsystem: database

# Dependency graph
requires:
  - phase: 29-metadata-inspection-api
    provides: PostgreSQL metadata inspection patterns (asyncpg connection handling)
  - phase: 30-ods-node-ui-enhancement
    provides: ODS node configuration structure (connection_id, schema, table, identity_fields)
provides:
  - ODSExecutor class with Append, Overwrite, and Upsert operations
  - Per-batch transaction isolation
  - Retry logic with exponential backoff
  - Error classification for PostgreSQL SQLSTATE codes
  - Deadlock prevention via record sorting
affects:
  - 31-02-deno-integration
  - 31-03-validation-testing

# Tech tracking
tech-stack:
  added: [asyncpg]
  patterns:
    - Per-batch transaction isolation with asyncpg
    - Exponential backoff retry pattern for database operations
    - SQL injection prevention via identifier validation
    - SQLSTATE-based error classification

key-files:
  created:
    - backend/app/services/ods_executor.py
  modified: []

key-decisions:
  - "Records sorted by identity_fields before upsert to prevent deadlocks (Pitfall 1 from research)"
  - "Per-batch transaction isolation rather than global transaction (Pitfall 2 from research)"
  - "Connection managed by caller (DenoService) rather than executor to match existing patterns"
  - "SQLSTATE-based error classification maps PostgreSQL codes to typed errors"
  - "Statement timeouts configurable per operation type (5min append, 30min overwrite, 10min upsert)"
  - "Retry only on DEADLOCK, TIMEOUT, CONNECTION_ERROR with exponential backoff (1s, 2s, 4s)"

patterns-established:
  - "ODS Operations: Append (INSERT), Overwrite (TRUNCATE+INSERT), Upsert (INSERT ON CONFLICT DO UPDATE)"
  - "Error Classification: Map asyncpg exceptions to typed ODSError with SQLSTATE codes"
  - "Batch Processing: Split large datasets into configurable batches (default 1000, max 10000)"
  - "SQL Injection Prevention: Validate identifiers match ^[a-zA-Z_][a-zA-Z0-9_]*$ pattern"

requirements-completed:
  - EXEC-01
  - EXEC-02
  - EXEC-03
  - EXEC-04
  - EXEC-05
  - EXEC-10
  - EXEC-11
  - EXEC-12
  - EXEC-13
  - EXEC-14
  - EXEC-15
  - EXEC-16

# Metrics
duration: 12min
completed: 2026-05-17T01:35:00Z
---

# Phase 31 Plan 01: Core ODS Execution Engine Summary

**ODSExecutor service implementing Append, Overwrite, and Upsert operations with per-batch transaction isolation, retry logic, and comprehensive PostgreSQL error classification using asyncpg**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-17T01:23:31Z
- **Completed:** 2026-05-17T01:35:00Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Created complete ODSExecutor class with all three write modes (Append, Overwrite, Upsert)
- Implemented per-batch transaction isolation using `async with conn.transaction()`
- Added exponential backoff retry logic (1s, 2s, 4s) for deadlock, timeout, and connection errors
- Implemented PostgreSQL SQLSTATE error classification mapping 6 error types
- Added deadlock prevention via automatic record sorting by identity_fields before upsert
- Configured operation-specific statement timeouts (5min append, 30min overwrite, 10min upsert)
- Implemented SQL injection prevention with identifier validation
- Added comprehensive docstrings and type hints throughout

## Task Commits

All tasks were committed atomically:

1. **Task 1-3: Create ODSExecutor with data models, core operations, and utilities** - `2affa4d` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `backend/app/services/ods_executor.py` - Core ODS execution engine with 759 lines implementing:
  - WriteMode enum (APPEND, OVERWRITE, UPSERT)
  - ODSConfig, ODSResult, ODSError dataclasses
  - ODSExecutor class with execute(), retry logic, and error handling
  - Query builders for INSERT and UPSERT operations
  - Utility methods for validation, sorting, and error classification
  - Singleton instance `ods_executor` for convenience

## Decisions Made

1. **Per-batch transaction isolation**: Each batch runs in its own transaction, preventing cascade failures. A failed batch rolls back without affecting other batches.

2. **Record sorting for deadlock prevention**: UPSERT operations sort records by identity_fields before execution to ensure consistent lock ordering and prevent deadlocks in concurrent scenarios (addresses Pitfall 1 from research).

3. **Caller-managed connections**: The executor receives an existing asyncpg.Connection rather than managing its own connections/pools. This matches the pattern used in metadata_service.py and allows the caller (DenoService) to manage connection lifecycle.

4. **SQLSTATE-based error classification**: PostgreSQL SQLSTATE codes are mapped to typed errors (DEADLOCK, UNIQUE_VIOLATION, FK_VIOLATION, TIMEOUT, CONNECTION_ERROR) for programmatic handling.

5. **Operation-specific timeouts**: Different operations get different timeouts based on expected duration:
   - Append: 5min (simple inserts)
   - Overwrite: 30min (TRUNCATE + full reload)
   - Upsert: 10min (conflict checking adds overhead)

6. **Retry on specific errors only**: Only DEADLOCK, TIMEOUT, and CONNECTION_ERROR trigger retry. Data errors (UNIQUE_VIOLATION, FK_VIOLATION) fail immediately since retry won't help.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

1. **asyncpg not installed**: Initially the import failed because asyncpg wasn't in the environment. Installed it via pip and imports worked correctly.

2. **Existing LSP errors**: The project has pre-existing TypeScript/SQLAlchemy typing errors in other files (data_sources.py, scheduler.py, etc.) that are unrelated to this implementation.

## Next Phase Readiness

- Core executor is complete and ready for integration
- Plan 31-02 (Deno Integration & Signal Protocol) can proceed with:
  - Deno runner.ts modification to emit EXEC_ODS signal
  - DenoService modification to intercept signals and delegate to ODSExecutor
  - WebSocket result streaming
- No blockers for next phase

## Self-Check: PASSED

- [x] `backend/app/services/ods_executor.py` exists (759 lines)
- [x] `31-01-SUMMARY.md` created
- [x] STATE.md updated with progress
- [x] ROADMAP.md updated
- [x] REQUIREMENTS.md updated (12 requirements marked complete)
- [x] Commits verified:
  - `2affa4d`: feat(31-01): implement ODS execution engine
  - `43fcfe7`: docs(31-01): complete plan summary and state updates

---
*Phase: 31-ods-execution-engine*
*Plan: 01*
*Completed: 2026-05-17*
