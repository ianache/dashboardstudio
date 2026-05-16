---
phase: 29
plan: 29-02
subsystem: backend
tags: [api, metadata, inspection]
requires: [29-01]
provides: [inspection-api]
tech-stack: [FastAPI, SQLAlchemy, asyncpg]
key-files: [backend/app/api/endpoints/data_sources.py, backend/test_metadata_api.py]
metrics:
  duration: 15m
---

# Phase 29 Plan 02: Metadata Inspection API Summary

Exposed the `MetadataService` through new FastAPI endpoints in the `data-sources` controller, allowing dynamic discovery of database schemas.

## Key Changes

### API Endpoints
- **GET `/api/v1/data-sources/{id}/tables`**: Returns a list of table names for a given data source.
- **GET `/api/v1/data-sources/{id}/tables/{table_name}/columns`**: Returns a list of columns (name and type) for a specific table.
- Both endpoints support an optional `schema` query parameter (defaults to `public`).

### Implementation Details
- Used `_decode_config` helper in `data_sources.py` to ensure credentials (host, user, password, etc.) are decrypted before being passed to the `MetadataService`.
- Injected `config["type"] = ds.type` to allow the service to select the correct inspection strategy.
- Implemented error handling returning 404 for missing data sources and 500 for connection/inspection failures.

## Verification Results

### Automated Tests
Created and ran `backend/test_metadata_api.py` which:
- Mocks authentication and database access.
- Patches `MetadataService` to verify that endpoints correctly decode configuration and call the service with expected arguments.
- Confirmed that both endpoints return expected JSON structures and 200 OK status.

```bash
$env:PYTHONPATH="backend"; backend/.venv/Scripts/python.exe backend/test_metadata_api.py
--- Testing Metadata API ---
INFO:httpx:HTTP Request: GET http://testserver/api/v1/data-sources/ds-123/tables "HTTP/1.1 200 OK"
GET /tables status: 200
GET /tables body: ['table1', 'table2']
INFO:httpx:HTTP Request: GET http://testserver/api/v1/data-sources/ds-123/tables/table1/columns "HTTP/1.1 200 OK"
GET /columns status: 200
GET /columns body: [{'name': 'col1', 'type': 'integer'}]
--- All tests passed! ---
```

## Deviations from Plan
None. The implementation followed the tasks exactly as described.

## Self-Check: PASSED
- [x] Endpoints added to `data_sources.py`.
- [x] Correct routing verified.
- [x] Credential decryption verified.
- [x] Verification script created and successful.
- [x] Commits made.
