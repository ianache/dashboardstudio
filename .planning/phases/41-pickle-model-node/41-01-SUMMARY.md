---
phase: 41-pickle-model-node
plan: 01
subsystem: api
tags: [scikit-learn, joblib, pandas, ml, pickle, fastapi, alembic, subprocess]

# Dependency graph
requires:
  - phase: backend-foundation
    provides: FastAPI router pattern, SQLAlchemy models, Alembic migrations, RBAC security

provides:
  - MLModel SQLAlchemy model and Pydantic schemas
  - ml_models table (machine_learning_models) with migration 036
  - pickle_model editor tool registered in editor_tools
  - backend/app/api/endpoints/ml_models.py with CRUD endpoints (RBAC)
  - backend/app/runtime/ml_worker.py subprocess-isolated metadata extractor
  - backend/storage/models/ directory for .pkl file storage

affects:
  - 41-02-PLAN.md (uses ml-models API for model selector UI)
  - 41-03-PLAN.md (uses ml_worker.py predict mode and MLModel table)

# Tech tracking
tech-stack:
  added:
    - scikit-learn>=1.4.0
    - pandas>=2.2.0
    - joblib>=1.3.0
  patterns:
    - Subprocess isolation for Pickle deserialization (RCE protection)
    - ml_worker.py as dual-mode CLI (--mode inspect/predict) called via subprocess.run
    - RBAC via require_role(["admin","designer"]) for upload/delete; get_current_user for reads

key-files:
  created:
    - backend/app/api/endpoints/ml_models.py
    - backend/app/runtime/ml_worker.py
    - backend/alembic/versions/036_add_ml_model_tool.py
    - backend/storage/models/.gitkeep
  modified:
    - backend/pyproject.toml
    - backend/app/models/models.py
    - backend/app/schemas/schemas.py
    - backend/app/api/router.py

key-decisions:
  - "Subprocess isolation: pickle deserialization runs in ml_worker.py subprocess to prevent Pickle RCE in main FastAPI process"
  - "ml_worker uses argparse --mode flag (inspect/predict) for dual-mode operation from a single script"
  - "feature_names_in_ extracted if present; falls back to feature_0..N index names if only n_features_in_ available"
  - "MLModel primary key uses 8-char UUID prefix (ml-XXXXXXXX) matching existing ID conventions"
  - "Storage directory backend/storage/models/ served as local filesystem — no object storage for MVP"

patterns-established:
  - "Subprocess worker pattern: CLI script called via subprocess.run with capture_output=True; exit code 1 on error with JSON error body"
  - "Upload-inspect-save pattern: save to disk first, run worker, save metadata to DB, cleanup disk on failure"

requirements-completed:
  - MODEL-01
  - MODEL-03

# Metrics
duration: 15min
completed: 2026-05-31
---

# Phase 41 Plan 01: ML Registry + Migration + Metadata Worker + RBAC API Summary

**scikit-learn .pkl model registry with subprocess-isolated metadata extraction, CRUD API with RBAC, and migration 036 registering the pickle_model flow editor tool**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-31T00:00:00Z
- **Completed:** 2026-05-31T03:00:00Z
- **Tasks:** 4
- **Files modified:** 8

## Accomplishments
- ML dependencies (scikit-learn, pandas, joblib) added to pyproject.toml and synced
- MLModel SQLAlchemy model and Pydantic schemas (Base/Create/Response) created
- Alembic migration 036 adds `machine_learning_models` table and registers `pickle_model` editor tool with `model_id` dynamic_select prop_def
- `ml_worker.py` subprocess-isolated inspector extracts sklearn version and feature names from .pkl files safely (Pickle RCE mitigation)
- REST API `/api/v1/ml-models` (POST/GET/GET/{id}/DELETE) with RBAC: upload/delete admin+designer only, reads all authenticated users

## Task Commits

All tasks were implemented prior to this summary session, committed in the existing codebase:

1. **Task 1: Project Dependencies & Model Storage** - `db79f2b` (chore) — scikit-learn/pandas/joblib in pyproject.toml; storage/models/ directory created
2. **Task 2: Database Model & Migration** - `db79f2b` (feat) — MLModel SQLAlchemy class, schemas, migration 036
3. **Task 3: Isolated ML Metadata Extractor** - `db79f2b` (feat) — ml_worker.py with inspect/predict modes
4. **Task 4: ML Models API with RBAC** - `db79f2b` (feat) — ml_models.py endpoints, router.py mount
5. **storage/.gitkeep** - `117c081` (chore) — ensures git tracks the models directory

**Plan metadata:** _(this summary commit)_

## Files Created/Modified
- `backend/pyproject.toml` — added scikit-learn>=1.4.0, pandas>=2.2.0, joblib>=1.3.0
- `backend/app/models/models.py` — added MLModel class (id, name, filename, sklearn_version, features JSON, created_by, timestamps)
- `backend/app/schemas/schemas.py` — added MLModelBase, MLModelCreate, MLModelResponse Pydantic schemas
- `backend/alembic/versions/036_add_ml_model_tool.py` — creates machine_learning_models table, inserts pickle_model tool record
- `backend/app/runtime/ml_worker.py` — dual-mode CLI: inspect (extracts metadata) + predict placeholder; uses joblib.load, subprocess-safe
- `backend/app/api/endpoints/ml_models.py` — POST upload, GET list, GET /{id}, DELETE /{id} with RBAC
- `backend/app/api/router.py` — ml_models router mounted at /ml-models
- `backend/storage/models/.gitkeep` — tracks model storage directory in git

## Decisions Made
- Subprocess isolation chosen over in-process loading to prevent Pickle RCE (malicious .pkl can execute arbitrary code on joblib.load)
- `ml_worker.py` uses argparse dual-mode (inspect/predict) to keep a single reusable worker script rather than two scripts
- If a model lacks `feature_names_in_` but has `n_features_in_`, feature indices are returned as `feature_0..N` to avoid returning an empty list when count is known
- Local filesystem storage (`backend/storage/models/`) chosen for MVP — no object storage dependency

## Deviations from Plan

None - plan executed exactly as written. All files were already implemented and committed correctly.

## Issues Encountered

None - all dependencies, migrations, and code were already in place when this plan was executed for SUMMARY generation.

## User Setup Required

None - no external service configuration required. ML model storage uses local filesystem.

## Next Phase Readiness
- `GET /api/v1/ml-models` returns model list for UI model selector (41-02)
- `ml_worker.py --mode predict` placeholder ready for 41-03 full implementation
- Migration 036 applied; `machine_learning_models` table and `pickle_model` tool exist in DB

---
*Phase: 41-pickle-model-node*
*Completed: 2026-05-31*
