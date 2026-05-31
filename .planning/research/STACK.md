# Stack Research

**Domain:** Advanced node types for an existing visual flow editor (ETL + AI + ML)
**Researched:** 2026-05-31
**Confidence:** HIGH

---

## Context: What is NOT changing

The core stack is validated and shipped. This document covers only the **additions** needed for v1.9.

- FastAPI + Python 3.11, existing `pyproject.toml`, managed via `uv`
- Deno TypeScript runner (`backend/app/runtime/runner.ts`) — signal protocol with `EXEC_*` stdout lines + `*_PAYLOAD` lines
- Vue 3 + Vite + Pinia (no TypeScript, no external CSS framework)
- `python-multipart>=0.0.6` already in deps (FastAPI file upload is already unlocked)
- `httpx>=0.26.0` already in deps

---

## New Python Dependencies (Backend)

### Core New Libraries

| Library | Pin | Purpose | Why This Choice |
|---------|-----|---------|-----------------|
| `openai` | `>=2.38.0,<3.0` | LLM node — OpenAI-compatible HTTP calls | `AsyncOpenAI(base_url=..., api_key=...)` pattern lets it talk to Anthropic, Groq, Moonshot, Gemini-compatible endpoints without per-provider code. Already has httpx under the hood. v2.x is stable as of May 2026. |
| `scikit-learn` | `>=1.8.0,<2.0` | Pickle Model node — `model.predict()` | Standard ML inference library. v1.8.0 is current stable (May 2026), supports Python 3.11-3.14. Brings joblib transitively. |
| `numpy` | `>=2.0.0,<3.0` | Array coercion for sklearn predict input | scikit-learn 1.8 requires numpy >=1.24.1; numpy 2.4.6 is latest stable (May 2026). Pin >=2.0 to avoid silent dtype changes from the 1.x to 2.x boundary. |
| `joblib` | `>=1.3.0` | Pickle model deserialization | Comes as scikit-learn transitive dep. Listing explicitly to pin minimum and make the dependency intention clear. `joblib.load()` is the standard way to load `.pkl` sklearn models. |

### What httpx Already Gives You

`httpx>=0.26.0` is already in `pyproject.toml`. The openai SDK wraps httpx internally. Do NOT add a separate httpx call for LLM — use the `openai` SDK so you get retry logic, timeout handling, and streaming for free.

### Installation (uv)

```bash
# From backend/ directory
uv add "openai>=2.38.0,<3.0"
uv add "scikit-learn>=1.8.0,<2.0"
uv add "numpy>=2.0.0,<3.0"
uv add "joblib>=1.3.0"
```

---

## Node Implementation Strategy

### 1. Conditional/Branch Node — Pure Deno, No New Python Deps

**How:** Evaluate a JS boolean expression inside `runner.ts` using the existing `executeScriptNode` pattern. The key is in the routing: the runner must support **labeled output handles** (`true` and `false`), and the `FlowConnection` model needs a new optional `handle` field to carry the branch label.

**Signal protocol change:** None needed for existing signals. Branching is resolved entirely in Deno by tracking which downstream nodes belong to the `true` vs `false` branch based on connection `handle` labels. Nodes on the non-taken branch get a `NODE_STATUS:<id>:skipped` signal emitted.

**runner.ts change:** Add a `conditional` toolType handler that:
1. Runs expression against `context.payload` using `new Function('payload', 'ctx', 'return (' + expr + ')')`
2. Determines `taken = true|false`
3. Finds connections out of this node filtered by `conn.handle === String(taken)`
4. Adds all nodes reachable exclusively via the non-taken handle to `skippedNodes`

**Expression evaluation:** Use `new Function('payload', 'ctx', 'return (' + expr + ')')` — safer than raw `eval` because it scopes variables. Since Deno already runs user JS via `executeScriptNode` with dynamic `import()`, this is no added risk; the Deno process already has `--allow-net` for the full flow.

**FlowConnection model change:** Add optional `handle?: string` field to the TypeScript `FlowConnection` interface. Python's flow JSON schema stores connections as JSON blobs — no DB migration needed if this field is nullable.

### 2. Data Transform Node — Pure Deno, No New Python Deps

**How:** Identical to the existing `js_script` toolType handler in `runner.ts`. The only difference is semantics: the user writes a function body that receives `payload` and returns a transformed value. Reuse `executeScriptNode` directly — add a `data_transform` toolType alias that delegates to the same function.

**Canvas:** Single input port, single output port. No handle labeling needed. Standard node.

### 3. Templating Node — Pure Deno, No New Python Deps

**How:** The existing `resolveString()` function in `runner.ts` already handles `{{path.to.val}}` replacement using dot-path traversal. The Templating node is a thin wrapper: take `node.props.template` string, call `resolveString(template, context)`, set `context.payload` to the resulting string.

**Why not Python/Jinja2:** The existing Email node delegates to Python's Jinja2 `SandboxedEnvironment` because it needs SMTP credentials from the DB. A Templating node's output is just a string that flows to the next node — no DB access needed. Keeping it in Deno avoids a round-trip signal. Reserve the `EXEC_TEMPLATE` Python pattern only if you later need Jinja2 filters (date formatting, i18n).

**Canvas:** Single input, single output. No special handle needs.

### 4. LLM Node — New Python Executor (EXEC_LLM signal)

**How:** Follow the exact `EXEC_EMAIL` two-line pattern:
- Deno emits `EXEC_LLM:<node_id>:<batch_id>` followed by `EXEC_LLM_PAYLOAD:<json>`
- `deno_service.py` intercepts, calls a new `LLMExecutor`
- `LLMExecutor` resolves the LLM Connection from DataSource, decrypts the api_key, calls `AsyncOpenAI(base_url=..., api_key=...)` with the user-configured model and prompt

**Why Python not Deno for LLM:** The API key lives in the encrypted DataSource table, accessible only from Python. Deno has no DB access. This is the same reasoning as Email/ODS.

**LLM Connection storage:** Add `llm_api` as a new connection type in the existing DataSource model. It stores `{ base_url, api_key, model }` as JSON, encrypted the same way SMTP credentials are. This reuses the Connections UI already built. Avoids adding a separate LlmConfig lookup path in the executor.

**`AsyncOpenAI` call pattern:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=connection_config["base_url"],  # e.g. https://api.anthropic.com/v1
    api_key=connection_config["api_key"],
)
response = await client.chat.completions.create(
    model=node_props["model"],
    messages=[{"role": "user", "content": resolved_prompt}],
    max_tokens=node_props.get("max_tokens", 2048),
)
result_text = response.choices[0].message.content
```

This works for OpenAI, Groq, Moonshot, and any OpenAI-compatible endpoint. Anthropic requires `extra_headers={"anthropic-version": "2023-06-01"}` — document this constraint in the node's connection config UI.

**Prompt resolution:** Before emitting `EXEC_LLM`, Deno resolves `{{expr}}` markers in the system_prompt and user_prompt props using `resolveString()`, then sends the resolved text in the payload. Python receives fully-resolved strings.

### 5. Pickle Model Node — New Python Executor (EXEC_PICKLE signal)

**How:** Same two-line signal pattern. Deno emits `EXEC_PICKLE:<node_id>:<batch_id>` followed by `EXEC_PICKLE_PAYLOAD:<json>`. Python's `PickleExecutor` loads the model file and calls `model.predict()`.

**File upload strategy:**
- FastAPI endpoint: `POST /api/v1/ml-models/upload` accepting `UploadFile`
- Storage: local filesystem at `backend/storage/ml_models/{uuid}.pkl`
- DB record: new `MLModel` table with `id`, `name`, `filename`, `created_by`, `created_at`
- `python-multipart` already in deps; `UploadFile` works out of the box — no new package needed

**Security — highest-risk item in v1.9:**
Pickle deserialization is a known RCE vector (CVE-2025-1716, malicious Hugging Face models found early 2025). Required mitigations:
1. **Auth gate:** Only accept uploads from `admin` or `designer` roles via `require_role(["admin", "designer"])`
2. **Extension + magic bytes check:** Reject non-`.pkl` files; validate first 2 bytes are `\x80\x04` or `\x80\x05` (pickle protocol markers)
3. **Subprocess isolation:** Run `model.predict()` in a child subprocess with a 30s timeout — if the pickle is malicious, it cannot access the FastAPI process memory or env vars
4. **Only `joblib.load()`:** Never use `dill`, `torch.load()`, or `cloudpickle` — strictly sklearn-serialized models

**Subprocess isolation pattern:**
```python
# Spawn child process; pass model path as arg and input data via stdin
result = subprocess.run(
    ["python", "-c",
     "import joblib, json, sys, numpy as np; "
     "m = joblib.load(sys.argv[1]); "
     "data = json.load(sys.stdin); "
     "arr = np.array(data); "
     "print(json.dumps(m.predict(arr).tolist()))"],
    stdin=...,  # pipe input_data JSON
    capture_output=True, timeout=30
)
```

**Input format:** Deno sends `context.payload` (list of dicts or 2D array) in `EXEC_PICKLE_PAYLOAD`. Python coerces via `numpy.array()` before calling `predict()`.

---

## Frontend: Vue 3 Canvas — Conditional Node Dual-Handle

**Decision: Do NOT add @vue-flow/core.**

The current `FlowEditorCanvas.vue` is a fully custom SVG + absolute-positioned div canvas with custom pan/zoom, custom port dragging, and custom connection drawing. It is not built on `@vue-flow/core`. Migrating would be a complete rewrite — out of scope for v1.9.

**What needs to change instead:**

The existing port system uses two fixed ports per node:
- `.fec-port--in` (top-center) — hidden for `source` category nodes
- `.fec-port--out` (bottom-center) — hidden for `destination` and `notification` category nodes

For the Conditional node, replace the single `fec-port--out` with two labeled output ports: `true` (green-tinted, bottom-left) and `false` (red-tinted, bottom-right). This is purely CSS + template logic in `FlowEditorCanvas.vue`.

**Connection model extension:**
```javascript
// Add optional handle field to connection objects
{ id, from, to, handle: 'true' | 'false' | null }
```

The `connPath()` function already receives the connection object — use the `handle` field to pick the correct source port position (`true` = bottom-left offset, `false` = bottom-right offset).

**Port mousedown tracking:** `onPortMousedown` already receives `(event, node, 'out')` — extend the third arg to include an optional fourth `handleLabel` param for nodes that have multiple out-handles. Store the active handle label in the temp connection state.

**Node type check:** In the node template `v-for`, check `node.toolType === 'conditional'` to render the dual-port layout instead of the single-port layout.

**No new npm package needed.** Dual handles are approximately 50-70 lines of CSS + template changes.

---

## File Upload: Storage Path Strategy

```
backend/
  storage/
    ml_models/          # .pkl files stored here (gitignored)
      {uuid}.pkl
  app/
    api/endpoints/
      ml_models.py      # New: POST /upload, GET /list, DELETE /{id}
    services/
      pickle_executor.py   # New
    models/models.py    # Extend: add MLModel table
```

**Configuration:** `STORAGE_DIR` env var, defaulting to `./storage` relative to the backend working directory. Add to `backend/app/core/config.py` as a `Settings` field.

**Docker:** Add `volumes: ["./storage:/app/storage"]` in `docker-compose.yml` so `.pkl` files persist across container restarts.

---

## Version Compatibility Matrix

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| `openai` | `>=2.38.0,<3.0` | Python 3.11, httpx 0.26+ | openai SDK uses httpx internally; no version conflict with existing dep |
| `scikit-learn` | `>=1.8.0,<2.0` | Python 3.11-3.14, numpy >=1.24.1 | v1.8.0 released May 2026 |
| `numpy` | `>=2.0.0,<3.0` | scikit-learn 1.8, Python 3.11 | numpy 2.4.6 latest stable (May 2026); pin >=2.0 to skip 1.x to 2.x dtype surprises |
| `joblib` | `>=1.3.0` | scikit-learn 1.8 (transitive) | Explicit pin for documentation clarity |
| `python-multipart` | already `>=0.0.6` | FastAPI UploadFile | No change needed |

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `openai` SDK for LLM node | `httpx` direct calls per-provider | The openai SDK handles retries, timeouts, and streaming, and the `base_url` pattern covers most OpenAI-compatible endpoints. Direct httpx would mean reimplementing retry logic and per-provider response parsing for every LLM provider. |
| `joblib.load()` for pkl models | `pickle.load()` directly | joblib handles numpy memmapping and is the sklearn-blessed serialization format; `pickle.load` works but offers no benefit over joblib for sklearn models. |
| Subprocess isolation for pkl inference | In-process `model.predict()` | Pickle RCE risk is real and actively exploited (CVE-2025-1716). Subprocess isolation is a non-negotiable safety layer for user-uploaded `.pkl` files. |
| Custom dual-handle CSS for Conditional | `@vue-flow/core` migration | vue-flow 1.48.x is excellent but the canvas is 100% bespoke; adopting it requires a complete rewrite unrelated to v1.9 scope. |
| `resolveString()` for Templating node | Python Jinja2 via EXEC_TEMPLATE signal | The runner already has `resolveString()` with `{{expr}}` syntax. A round-trip signal to Python adds IPC overhead for a feature that needs no DB access. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `anthropic` Python SDK | Adds a second LLM client for one provider only; Groq/Moonshot also have their own SDKs | `openai` SDK with `base_url` — Anthropic's chat completions endpoint is OpenAI-compatible |
| `torch` or `tensorflow` | Multi-GB deps not needed for sklearn inference | `joblib` + `scikit-learn` only |
| `dill` for deserialization | Extends pickle attack surface (supports lambdas, closures) with same RCE risk and no benefit for sklearn models | `joblib.load()` only |
| `@vue-flow/core` | Not compatible with the bespoke canvas without a full rewrite | CSS-only dual-port extension on existing `FlowEditorCanvas.vue` |
| Raw `eval()` in Deno for Conditional expression | No variable scope isolation | `new Function('payload', 'ctx', 'return (' + expr + ')')` — scoped variables |

---

## Sources

- [openai PyPI — v2.38.0 latest (May 2026)](https://pypi.org/project/openai/)
- [openai/openai-python GitHub — AsyncOpenAI base_url pattern](https://github.com/openai/openai-python)
- [scikit-learn 1.8.0 install docs](https://scikit-learn.org/stable/install.html)
- [scikit-learn model persistence docs](https://scikit-learn.org/stable/model_persistence.html)
- [numpy 2.4.6 PyPI (May 2026)](https://pypi.org/project/numpy/)
- [FastAPI UploadFile docs](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Pickle RCE risks — Fortra 2025](https://www.fortra.com/blog/supply-chain-vulnerability)
- [CVE-2025-1716 — picklescan bypass (Sonatype 2025)](https://www.sonatype.com/blog/bypassing-picklescan-sonatype-discovers-four-vulnerabilities)
- [@vue-flow/core v1.48.2 npm](https://www.npmjs.com/package/@vue-flow/core)
- [Deno security model — permission flags](https://docs.deno.com/runtime/fundamentals/security/)

---

*Stack research for: v1.9 Advanced Node Types — Dashboard Studio*
*Researched: 2026-05-31*
