---
phase: 41-pickle-model-node
plan: 02
subsystem: ui
tags: [vue3, ml-models, scikit-learn, pickle, flow-editor, settings]

# Dependency graph
requires:
  - phase: 41-01-pickle-model-node
    provides: ML model registry backend (upload, list, delete, inspect endpoints)
provides:
  - mlModelsApi frontend service (getAll, getById, upload, delete)
  - Modelos ML section in SettingsView with upload and delete UI
  - Pickle Model node property panel with dynamic model dropdown and feature column hints
  - Migration 039 fixing fetch_endpoint key in existing DB records
affects: [flow-editor, settings-view, ml-inference]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "dynamic_select prop_def with value_field/label_field for ID-based selects"
    - "Watcher pattern: fetch detail record when model_id selected in node panel"

key-files:
  created:
    - backend/alembic/versions/039_fix_pickle_model_prop_defs.py
  modified:
    - dashboard-app/src/services/api.js
    - dashboard-app/src/views/SettingsView.vue
    - dashboard-app/src/components/editor/FlowEditorCanvas.vue
    - backend/alembic/versions/036_add_ml_model_tool.py

key-decisions:
  - "dynamic_select value_field/label_field: use opt.id as stored value (not opt.name) to correctly map to backend primary key"
  - "Migration 039 created to fix existing DB records where endpoint key was used instead of fetch_endpoint"

patterns-established:
  - "dynamic_select prop_def: always specify value_field and label_field when API returns objects with id != name"

requirements-completed: [MODEL-01, MODEL-03]

# Metrics
duration: 5min
completed: 2026-06-01
---

# Phase 41 Plan 02: ML Model Management UI Summary

**Pickle Model node dropdown backed by /api/v1/ml-models/ with feature column metadata display, plus full Settings UI for upload/delete lifecycle**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-01T03:37:50Z
- **Completed:** 2026-06-01T03:43:29Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- ML model management UI in Settings: lists models with sklearn version and creation date, upload .pkl form, delete with confirm dialog
- Pickle Model node property panel: dynamic dropdown for model selection, Columnas requeridas feature tag block, sklearn version display
- Bug fix: `dynamic_select` now correctly stores `id` (UUID) as value using `value_field`/`label_field` prop_def fields, preventing mismatched lookups in `execute_ml_node`
- Migration 039 corrects existing DB records (endpoint → fetch_endpoint) in `editor_tools` table for the pickle_model tool

## Task Commits

Each task was committed atomically:

1. **Task 1: API Service for ML Models** - `db79f2b` (feat — pre-existing from prior session)
2. **Task 2: Model Management UI** - `98fffe4` (feat)
3. **Task 3: Pickle Model Node Property Panel** - `5f17467` (feat — includes auto-fixes)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `dashboard-app/src/services/api.js` - mlModelsApi with getAll, getById, upload (FormData), delete
- `dashboard-app/src/views/SettingsView.vue` - Modelos ML panel with list, upload form, delete; fixed expandedSections.ml init
- `dashboard-app/src/components/editor/FlowEditorCanvas.vue` - dynamic_select value_field/label_field support; pickle_model info block with feature tags
- `backend/alembic/versions/036_add_ml_model_tool.py` - corrected source prop_defs (fetch_endpoint, value_field, label_field)
- `backend/alembic/versions/039_fix_pickle_model_prop_defs.py` - migration to update existing DB records

## Decisions Made
- Used `value_field`/`label_field` in `dynamic_select` prop_def rather than hardcoding id/name extraction in FlowEditorCanvas, keeping the pattern extensible for future selects with non-standard field names.
- Created migration 039 rather than modifying 036 alone, since 036 was already applied to the running DB.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing `ml` key in expandedSections initialization**
- **Found during:** Task 2 (Model Management UI)
- **Issue:** `expandedSections.ml` was used in template but not initialized in the ref object, causing undefined initial state
- **Fix:** Added `ml: false` to the expandedSections ref
- **Files modified:** dashboard-app/src/views/SettingsView.vue
- **Verification:** Grep confirms `ml: false` present in expandedSections
- **Committed in:** 98fffe4

**2. [Rule 1 - Bug] `dynamic_select` stored model name instead of model ID**
- **Found during:** Task 3 (Pickle Model Node Property Panel)
- **Issue:** `getOptionsForDef` rendered `opt.name` as both key and value for non-string options; `execute_ml_node` queries DB by `models.MLModel.id == model_id`, so storing a display name would cause "model not found" errors at runtime
- **Fix:** Updated option rendering to use `opt[def.value_field || 'id'] ?? opt.name` as value and `opt[def.label_field || 'name']` as label; updated prop_def in migration 036 and created migration 039 to fix existing DB
- **Files modified:** dashboard-app/src/components/editor/FlowEditorCanvas.vue, backend/alembic/versions/036_add_ml_model_tool.py, backend/alembic/versions/039_fix_pickle_model_prop_defs.py
- **Verification:** grep confirms value_field/label_field pattern in FlowEditorCanvas.vue; migration 039 created
- **Committed in:** 5f17467

**3. [Rule 1 - Bug] `endpoint` key instead of `fetch_endpoint` in pickle_model prop_defs**
- **Found during:** Task 3 (Pickle Model Node Property Panel)
- **Issue:** Migration 036 defined `"endpoint": "/api/v1/ml-models"` but `buildEndpoint()` in FlowEditorCanvas reads `def.fetch_endpoint`; the dropdown would never populate
- **Fix:** Fixed migration 036 source and created migration 039 to UPDATE existing DB record with correct key
- **Files modified:** (same as above)
- **Committed in:** 5f17467

---

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs)
**Impact on plan:** All fixes necessary for correctness. Without them: panel state broken, dropdown empty, model execution failing with "not found" errors.

## Issues Encountered
- Task 1 code (mlModelsApi in api.js) was already committed in a prior session's bulk commit (`db79f2b`). Verified correct implementation exists, no re-commit needed.

## User Setup Required
Run the new migration to fix existing DB records:
```bash
cd backend
uv run alembic upgrade head
```

## Next Phase Readiness
- ML model upload/delete fully operational from Settings UI
- Pickle Model node dropdown will populate from `/api/v1/ml-models/` and correctly store the model UUID
- Feature column hints display in node property panel after model selection
- Ready for end-to-end flow execution testing

---
*Phase: 41-pickle-model-node*
*Completed: 2026-06-01*
