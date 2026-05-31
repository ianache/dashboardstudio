# Phase 41: Pickle Model Node - Research

**Researched:** 2026-05-31
**Domain:** Machine Learning + Security (Subprocess Isolation)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `toolType`: `pickle_model`, `category`: `source` (pre-executed).
- Format: `.pkl` files (scikit-learn).
- Security: MUST use subprocess-isolated inference.
- Metadata: MUST extract feature columns at upload time.
- Roles: Upload restricted to admin/designer.

### Claude's Discretion
- Storage: `backend/storage/models/`.
- Isolation: Use a standalone Python script called via `subprocess.run`.
- Metadata Extraction: Attempt to read `feature_names_in_` or `n_features_in_`.

</user_constraints>

---

## Summary

The main challenge of this phase is security. `pickle.load()` is notoriously insecure as it can execute arbitrary code. By moving this operation to a separate subprocess, we prevent a malicious model from compromising the main FastAPI process.

### Isolation Pattern
The backend will spawn a separate Python process to handle the actual `pickle.load()` and `model.predict()`.
1. **Host (FastAPI)**: Receives JSON data, writes to temp file or pipe.
2. **Worker (Subprocess)**: Loads pickle, processes data, writes JSON result to stdout.
3. **Host**: Reads stdout, cleans up.

### Metadata Extraction
When a user uploads a `.pkl` file, the backend will:
1. Save the file.
2. Run the isolated worker in "inspect" mode.
3. The worker loads the model and looks for:
   - `sklearn.__version__`
   - `model.feature_names_in_` (if available)
   - `model.n_features_in_`
4. Store these in the `machine_learning_models` table.

---

## Technical Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `scikit-learn` | latest | Model inference |
| `pandas` | latest | Data handling for `predict()` |
| `joblib` | latest | Alternative to pickle (often better for sklearn) |

I will add these to `pyproject.toml`.

---

## Architecture Patterns

### Pattern 1: Isolated Worker Script (`ml_worker.py`)
```python
import sys
import json
import pickle
import pandas as pd

def main():
    mode = sys.argv[1] # 'inspect' or 'predict'
    model_path = sys.argv[2]
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    if mode == 'inspect':
        res = {
            "sklearn_version": sklearn.__version__,
            "features": list(getattr(model, 'feature_names_in_', []))
        }
        print(json.dumps(res))
    elif mode == 'predict':
        input_data = json.load(sys.stdin)
        df = pd.DataFrame(input_data)
        preds = model.predict(df)
        print(json.dumps(preds.tolist()))

if __name__ == "__main__":
    main()
```

### Pattern 2: Pre-execution Integration
Similar to the LLM node, the `source_executor.py` will call `execute_ml_node`.
It will find the model file, call the worker, and store results in `prefetched_outputs`.

### Pattern 3: Frontend Model Management
A new view or modal is needed to list and upload models.
Location: `SettingsView.vue` or a new `ModelsView.vue`.
The `pickle_model` tool property panel will use a `dynamic_select` to fetch models from `GET /api/v1/ml-models`.

### Pattern 4: Metadata Display
The property panel for `pickle_model` should display the `features` list from the selected model as a read-only hint.
This requires `FlowEditorCanvas.vue` to fetch model details when `model_id` changes.

---

## Common Pitfalls

### Pitfall 1: Pickle Version Compatibility
**Risk:** Pickle files created with Python 3.12 might not load in 3.11.
**Mitigation:** Ensure the worker runs on the same Python version as the host.

### Pitfall 2: Scikit-learn Version Mismatch
**Risk:** Model behaves differently or fails to load if versions differ.
**Mitigation:** `MODEL-04` requires a warning. We will compare stored `sklearn_version` with current `sklearn.__version__`.

### Pitfall 3: Memory Exhaustion
**Risk:** Large input payloads or large models.
**Mitigation:** Impose a timeout and memory limit on the subprocess.

---

## Sources
- [Python Pickle Security](https://docs.python.org/3/library/pickle.html#security)
- [Scikit-learn model persistence](https://scikit-learn.org/stable/modules/model_persistence.html)
- `subprocess` documentation for pipes.
