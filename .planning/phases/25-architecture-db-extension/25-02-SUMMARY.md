---
phase: 25-architecture-db-extension
plan: 02
subsystem: integration
tags: [api, integration, frontend, pinia]
requirements: [FR-07]
key-files: [backend/app/api/endpoints/integration_flows.py, dashboard-app/src/stores/integrations.js]
---

# Phase 25 Plan 02: API & Integration Summary

The API and frontend store have been updated to support the new separate notes layer, ensuring correct persistence and state management.

## Key Changes

### API Endpoints
- Updated `save_flow_diagram` in `backend/app/api/endpoints/integration_flows.py` to handle the `notes` key in the request body.
- The `notes` field from the frontend is now mapped to the `flow_notes` column in the database.

### Frontend Store
- Verified `dashboard-app/src/stores/integrations.js`.
- The `integrations` Pinia store automatically maps the `flow_notes` field from the API response to the `currentFlow` state during `loadById`, `updateFlow`, and `saveDiagram` actions.

## Deviations from Plan
- None.

## Self-Check: PASSED
- [x] PUT /api/v1/integration-flows/{id}/diagram accepts "notes" in body.
- [x] "notes" are stored in "flow_notes" DB column.
- [x] Frontend store reflects flow_notes in state.
