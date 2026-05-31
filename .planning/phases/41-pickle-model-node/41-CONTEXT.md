# Phase 41: Pickle Model Node - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `pickle_model` node to integration flows that allows running scikit-learn model inference securely.

### Core Value
Allow users to integrate predictive models into their data flows without exposing the main backend process to Pickle RCE (Remote Code Execution) vulnerabilities.

### Success Criteria
- User can upload `.pkl` files (restricted to Admin/Designer).
- Backend extracts metadata (feature names, sklearn version) during upload.
- Pickle deserialization and `predict()` run in a separate subprocess.
- UI shows expected feature columns for the selected model.
- Warning if sklearn versions mismatch between training (upload time) and inference.

</domain>

<requirements>
## v1.9 Requirements (Traceability)

- **MODEL-01**: Upload `.pkl` files, list and delete them.
- **MODEL-02**: Subprocess-isolated inference.
- **MODEL-03**: Metadata extraction (feature columns).
- **MODEL-04**: Version mismatch warning.

</requirements>

<code_context>
## Relevant Files

- `backend/app/models/models.py`: Add `MLModel` table.
- `backend/app/api/endpoints/ml_models.py`: New endpoints for CRUD.
- `backend/app/services/ml_executor.py`: New service for isolated inference.
- `backend/app/services/source_executor.py`: Integrate into pre-execution.
- `backend/app/runtime/runner.ts`: Ensure pre-executed output is handled.

</code_context>

<deferred>
## Deferred Ideas

- Support for ONNX or TensorFlow models.
- Model performance monitoring.
- GPU acceleration.

</deferred>

---

*Phase: 41-pickle-model-node*
*Context gathered: 2026-05-31*
