---
phase: 25-architecture-db-extension
plan: 01
subsystem: backend
tags: [database, schema, pydantic]
requirements: [FR-07, TR-04]
key-files: [backend/app/models/models.py, backend/app/schemas/schemas.py, backend/update_db_phase25.py]
---

# Phase 25 Plan 01: Backend Schema Extension Summary

Dedicated persistence for the notes layer in integration flows has been implemented by extending the database schema and Pydantic models.

## Key Changes

### Database Schema
- Added `flow_notes` column to `biportal.integration_flows` table using `JSONB` type.
- Column defaults to an empty list `[]` and is NOT NULL.

### Backend Models
- Updated `IntegrationFlow` SQLAlchemy model in `backend/app/models/models.py` to include the `flow_notes` column.

### Pydantic Schemas
- Updated `IntegrationFlowCreate`, `IntegrationFlowUpdate`, and `IntegrationFlowResponse` in `backend/app/schemas/schemas.py` to include `flow_notes: List[dict]`.

## Deviations from Plan
- None. The migration script was executed successfully after adjusting the execution directory to ensure the `.env` file was loaded correctly.

## Self-Check: PASSED
- [x] IntegrationFlow model contains flow_notes.
- [x] IntegrationFlow schemas contain flow_notes.
- [x] IntegrationFlow table in DB contains flow_notes column.
