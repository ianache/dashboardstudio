# Architecture Research — v1.9 Advanced Node Types

**Domain:** Visual Flow Editor — Extending the Deno/Python Signal Architecture
**Researched:** 2026-05-31
**Confidence:** HIGH (based on direct codebase analysis)

---

## Standard Architecture

### Current System Overview

```
Browser (Vue 3 SPA)
  └─ FlowEditorCanvas.vue
       ├─ nodes: [{ id, toolType, category, label, props, x, y }]
       └─ connections: [{ id, from, to }]   ← ONE output handle per node today
            │
            │  WebSocket (ws://bff/integration-flows/{id}/logs)
            ▼
BFF (Node.js + Express)
  └─ proxy → FastAPI:8000
            │
            ▼
FastAPI /integration-flows/{id}/logs (WebSocket)
  └─ pre_execute_flow_nodes()   ← source nodes resolved in Python before Deno
  └─ deno_service.run_flow_stream()
            │
            │  stdin: flow JSON (nodes + connections + metadata + prefetched_outputs)
            ▼
Deno runner.ts (subprocess)
  ├─ getTopologicalOrder()      ← Kahn's BFS over { from, to } edges
  ├─ runNodeExecution()         ← switch on node.toolType
  │    ├─ js_script → executeScriptNode() (data URI module trick)
  │    ├─ http_rest / graphql  → fetch()
  │    ├─ join                 → in-process join
  │    ├─ ods_pg               → emits EXEC_ODS: signal + EXEC_ODS_PAYLOAD: JSON
  │    └─ email                → emits EXEC_EMAIL: signal + EXEC_EMAIL_PAYLOAD: JSON
  │
  │  stdout: signal lines, parsed by deno_service.py
  ▼
deno_service.py (stdout parser + Python executor dispatcher)
  ├─ NODE_STATUS:id:status       → WebSocket → browser canvas update
  ├─ NODE_LOG_JSON:{json}        → execution history log
  ├─ EXEC_ODS: + EXEC_ODS_PAYLOAD: → _handle_ods_execution() → asyncpg → PostgreSQL
  ├─ EXEC_EMAIL: + EXEC_EMAIL_PAYLOAD: → _handle_email_execution() → smtplib
  └─ FINAL_RESULT:{json}         → final payload forwarded to client
```

---

## Component Responsibilities

| Component | Responsibility | Where Defined |
|-----------|---------------|---------------|
| `FlowEditorCanvas.vue` | Drag/drop canvas, port rendering, connection drawing, property panel | `dashboard-app/src/components/editor/` |
| `runner.ts` | Topological sort + node execution in Deno sandbox | `backend/app/runtime/runner.ts` |
| `deno_service.py` | Subprocess management, stdout signal parsing, Python executor dispatch | `backend/app/services/deno_service.py` |
| `email_executor.py` | Jinja2 SandboxedEnvironment + smtplib SMTP send | `backend/app/services/email_executor.py` |
| `ods_executor.py` | asyncpg batch write (Append/Overwrite/Upsert) to PostgreSQL | `backend/app/services/ods_executor.py` |
| `source_executor.py` | Pre-execution of source nodes (SQL/HTTP) before Deno starts | `backend/app/services/source_executor.py` |
| `DataSource` (model) | Encrypted connection credentials (SMTP, DB, HTTP, FTP) | `backend/app/models/models.py` |
| `LlmConfig` (model) | Encrypted API keys per provider (Anthropic, Gemini, Groq, Moonshot) | `backend/app/models/models.py` |
| `EditorTool` (model) | Tool catalog: type, category, prop_defs, icon stored in DB | `backend/app/models/models.py` |

---

## Integration Design per New Node Type

### Node 1: Conditional / Branch

**Core problem:** `FlowConnection` currently has `{ id, from, to }` with no handle discriminator. The topological sort and payload routing use only `from`/`to`. A branch node requires two output connections, one taken (`true`) and one not taken (`false`).

**Canvas changes required (one-way door):**

The `FlowConnection` interface must gain an optional `fromHandle` field:

```typescript
interface FlowConnection {
  id: string;
  from: string;
  to: string;
  fromHandle?: 'true' | 'false' | 'out';  // 'out' = default for all existing nodes
}
```

All existing connections without `fromHandle` are treated as `'out'` by the runner — no migration of existing flows needed.

In `FlowEditorCanvas.vue`, the branch node renders two output ports instead of one. The single `fec-port--out` div (currently shown for all non-destination/non-notification nodes at line 314) must be replaced with a conditional block:

```html
<!-- Single output port for normal nodes (existing) -->
<div v-if="!readOnly && node.category !== 'destination'
           && node.category !== 'notification'
           && node.toolType !== 'branch'"
  class="fec-port fec-port--out"
  @mousedown.stop="onPortMousedown($event, node, 'out', 'out')"
  @mouseup="onPortMouseup($event, node, 'in')">
</div>

<!-- Dual output ports for branch node -->
<template v-if="!readOnly && node.toolType === 'branch'">
  <div class="fec-port fec-port--out fec-port--true"
    @mousedown.stop="onPortMousedown($event, node, 'out', 'true')"
    @mouseup="onPortMouseup($event, node, 'in')">
    <span class="fec-port-label">T</span>
  </div>
  <div class="fec-port fec-port--out fec-port--false"
    @mousedown.stop="onPortMousedown($event, node, 'out', 'false')"
    @mouseup="onPortMouseup($event, node, 'in')">
    <span class="fec-port-label">F</span>
  </div>
</template>
```

`onPortMousedown` receives a fourth argument `handleId` stored in the pending connection state and written into `fromHandle` when the connection completes in `onPortMouseup`.

**Runner changes (Deno side):**

The topological sort (`getTopologicalOrder`) is unaffected — it walks all edges regardless of `fromHandle`. The change is in two places inside `main()`:

1. The payload routing section (lines ~801-807) must use `fromHandle` to select keyed outputs:

```typescript
// Extended: resolve incoming payload via handle key if present
const incoming = flow.connections.filter(c => c.to === node.id);
if (incoming.length === 1) {
  const c = incoming[0];
  const handleKey = c.fromHandle && c.fromHandle !== 'out'
    ? `${c.from}#${c.fromHandle}`
    : c.from;
  currentPayload = nodeOutputs.get(handleKey) ?? nodeOutputs.get(c.from) ?? [];
}
```

2. A new branch node handler writes two keyed outputs and emits success:

```typescript
} else if (node.toolType === 'branch') {
  const expr = node.props?.condition || 'false';
  let result: boolean;
  try {
    result = Boolean(await executeScriptNode(`return Boolean(${expr})`, '', context));
  } catch {
    result = false;
  }
  nodeOutputs.set(`${node.id}#true`,  result ? context.payload : undefined);
  nodeOutputs.set(`${node.id}#false`, result ? undefined : context.payload);
  nodeOutputs.set(node.id, context.payload); // fallback for handle-unaware consumers
  emitStatus(node.id, 'success');
  // Standard nodeOutputs.set at end of loop is redundant here but harmless
}
```

3. Branch pruning: downstream nodes with all `undefined` incoming payloads must be skipped:

```typescript
// Before emitStatus(node.id, 'running'):
const allInputsUndefined = incoming.length > 0 && incoming.every(c => {
  const handleKey = c.fromHandle && c.fromHandle !== 'out'
    ? `${c.from}#${c.fromHandle}`
    : c.from;
  return nodeOutputs.get(handleKey) === undefined && nodeOutputs.get(c.from) === undefined;
});
if (allInputsUndefined) {
  skippedNodes.add(node.id);
  continue;
}
```

**What does NOT change:** `deno_service.py` signal parsing, `FlowConnection` database column (JSON blob — new field is backward-compatible), `getTopologicalOrder`, all existing node types.

**Confidence:** HIGH — design derived from existing `dsplit/djoin` pattern in `runner.ts` which already uses keyed outputs (`branchOutputs.set(node.id, item)`).

---

### Node 2: Data Transform

**Architecture fit:** Pure Deno execution. No Python signal needed.

This node is structurally identical to `js_script` but with a different UX contract: the function receives `data` (current payload) and must return the transformed result. The runner reuses `executeScriptNode()` exactly.

```typescript
} else if (node.toolType === 'data_transform') {
  const fn = node.props?.transform_fn || 'return data';
  const wrappedCode = `const data = ctx.payload;\n${fn}`;
  const inputPayload = context.payload;
  context.payload = await executeScriptNode(wrappedCode, node.props?.imports || '', context);
  const endMs = Date.now();
  console.log(`NODE_LOG_JSON:${JSON.stringify({
    node_id: node.id, status: 'success',
    input: inputPayload, output: context.payload,
    duration: endMs - startMs, start_time: startTime,
    end_time: new Date(endMs).toISOString()
  })}`);
  emitStatus(node.id, 'success');
}
```

**Canvas changes:** None. Single input, single output — category `transform`, same port rendering as existing nodes.

**Property panel:** One CodeEditor field (`transform_fn`) with `data` variable pre-bound to the input payload. The `executeScriptNode` wrapper is transparent to the user.

**Confidence:** HIGH — trivial extension of existing `js_script` node.

---

### Node 3: Templating Node

**Decision: Deno-side Nunjucks, NOT Python signal delegation.**

The reason to avoid the Python signal path here is a fundamental architectural constraint: `deno_service.py` parses stdout only after the Deno process exits (the `run_flow_stream()` function uses `subprocess.run()` which buffers all output). Deno cannot receive Python's result back to continue execution in the same process. Signal delegation (EXEC_ODS, EXEC_EMAIL) works only for terminal operations where the result does not need to flow into a downstream Deno node.

The existing `email_executor.py` Jinja2 implementation is excellent for emails because email sending IS terminal. A templating node whose output text must feed downstream nodes cannot use this path.

Nunjucks (npm) supports `{{ expr }}`, `{% for %}`, and `{% if %}` — a superset of what the email node already supports. Add it to `deno.json`:

```json
{
  "imports": {
    "nunjucks": "npm:nunjucks@^3.2.4"
  }
}
```

Runner handler:

```typescript
} else if (node.toolType === 'template') {
  const nunjucks = await import('nunjucks');
  const template = node.props?.template || '';
  const env = new nunjucks.Environment(null, { autoescape: false });
  const templateContext = {
    payload: context.payload,
    variables: context.variables,
    ...(Array.isArray(context.payload) ? { records: context.payload } : context.payload)
  };
  const inputPayload = context.payload;
  const rendered = env.renderString(template, templateContext);
  context.payload = { text: rendered };
  const endMs = Date.now();
  console.log(`NODE_LOG_JSON:${JSON.stringify({
    node_id: node.id, status: 'success',
    input: inputPayload, output: context.payload,
    duration: endMs - startMs, start_time: startTime,
    end_time: new Date(endMs).toISOString()
  })}`);
  emitStatus(node.id, 'success');
}
```

The `cache_runner_deps()` warmup at startup pre-caches nunjucks so the first execution is not slow.

**Limitation to document:** Jinja2-specific filters (e.g., `| safe`, `| date`, `| tojson`) are not available in Nunjucks. Nunjucks has its own filter set. If byte-for-byte Jinja2 compatibility is needed, the pre-execution Python path must be used, with the output injected as a `prefetched_output` (same as LLM). For current BI use cases, Nunjucks is sufficient.

**Confidence:** MEDIUM — Nunjucks is well-tested but Jinja2 syntax divergences may surprise users who already use `{{expr}}` in email templates.

---

### Node 4: LLM Node

**Decision: Python pre-execution (same pattern as SQL/HTTP source nodes), NOT Deno native fetch.**

The decisive factor is credential security: `LlmConfig` stores encrypted API keys in PostgreSQL. If Deno called the LLM provider directly, the decrypted key would appear in either `node.props` (stored in `flow_nodes` column, visible in execution history) or in the Deno process environment (still logged). Python resolves credentials at pre-execution time without them ever touching Deno's context.

| Factor | Deno fetch | Python pre-execution |
|--------|-----------|----------------------|
| LlmConfig credential access | Requires passing key through flow JSON | Native SQLAlchemy query, decrypted in Python |
| API key exposure | Visible in `flow_nodes` DB column + execution logs | Never leaves Python process |
| Downstream data availability | Result available to next Deno node | Result available as prefetched_output |
| Dependency | Deno `fetch()`, no new deps | `httpx` already in backend |
| Provider support | All (OpenAI-compatible) | All (same httpx calls as `useLlmCall.js`) |

**`pre_execute_flow_nodes()` extension** in `source_executor.py`:

```python
# Detect 'llm' nodes and execute them before Deno starts
elif node.get('toolType') == 'llm':
    from app.services.llm_executor import execute_llm_node
    result = await execute_llm_node(node, db, upstream_context)
    prefetched_outputs[node['id']] = result
    node['__pre_executed'] = True
```

**New `llm_executor.py`:**

```python
import httpx
from app.models.models import LlmConfig
from app.core.encryption import decrypt_value

async def execute_llm_node(node: dict, db, upstream_context: any) -> dict:
    config_id = node['props'].get('config_id')
    llm_cfg = db.query(LlmConfig).filter(LlmConfig.id == config_id).first()
    provider = llm_cfg.provider
    api_key = decrypt_value(llm_cfg.api_key)
    model_id = node['props'].get('model_id', '')
    prompt_template = node['props'].get('prompt', '')
    # Resolve {{payload.*}} placeholders using upstream_context
    prompt = resolve_string(prompt_template, upstream_context)
    response_text = await call_provider(provider, api_key, model_id, prompt)
    return {"rows": [{"text": response_text}], "duration": duration_ms}
```

**Architectural constraint to document:** An LLM node placed after a `data_transform` node cannot consume that transform's output, because pre-execution runs before Deno starts. The LLM node receives only the initial flow payload as its context. Users who need LLM-after-transform must either use a `js_script` node with direct API calls (bypassing LlmConfig security) or restructure to put the transform in the pre-execution phase (i.e., as a source node).

**Canvas:** Single input port, single output port. Category `processor`. Property panel shows: config selector (dropdown fetching from `/llm-config/`), model_id text field, prompt textarea with `{{payload.*}}` hints.

**Confidence:** HIGH — pre-execution pattern is proven in the codebase.

---

### Node 5: Pickle Model Node

**Architecture:** Python pre-execution (same pattern as LLM). No Deno involvement beyond receiving the prefetched result.

**File storage decision (one-way door):**

| Option | Pros | Cons |
|--------|------|------|
| Local filesystem (recommended) | Zero new infra, fits current single-container setup | Not multi-replica safe without volume mount |
| PostgreSQL BYTEA | Transactional, no extra infra | Slow for large models; 1GB TOAST limit is usually fine but awkward |
| S3/MinIO | Scalable, production-ready | New infra dependency not justified for current scale |

**Recommended:** Store `.pkl` files on the local filesystem at `MODEL_STORAGE_PATH` env var (default: `/app/models_storage/`). Mount this path as a Docker named volume in `docker-compose.yml`. Store the file path and model metadata in a new `MLModel` DB table.

**New database model** (add to `models.py`):

```python
class MLModel(Base):
    __tablename__ = "ml_models"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)      # absolute path on server
    file_size_bytes = Column(Integer, nullable=True)
    feature_names = Column(JSON, default=list)            # expected input columns
    target_name = Column(String(100), nullable=True)      # output column name
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**New API endpoints** (`backend/app/api/endpoints/ml_models.py`):
- `POST /ml-models/` — multipart file upload, saves to disk, creates `MLModel` record
- `GET /ml-models/` — list available models (id, name, feature_names, created_at)
- `DELETE /ml-models/{id}` — removes file from disk + DB record

**New `ml_executor.py`**:

```python
import pickle, time
import pandas as pd
from app.models.models import MLModel

def execute_pickle_node(node: dict, db, upstream_data: any) -> dict:
    model_id = node['props'].get('model_id')
    ml_model = db.query(MLModel).filter(MLModel.id == model_id).first()
    t0 = time.time()
    with open(ml_model.file_path, 'rb') as f:
        model = pickle.load(f)
    records = upstream_data if isinstance(upstream_data, list) else [upstream_data]
    df = pd.DataFrame(records)
    predictions = model.predict(df)
    duration_ms = int((time.time() - t0) * 1000)
    return {
        "rows": [{"prediction": float(p)} for p in predictions.tolist()],
        "duration": duration_ms
    }
```

**New Python dependencies** (add to `backend/pyproject.toml`):
- `scikit-learn>=1.4.0`
- `pandas>=2.0.0`

**Security:** `pickle.load()` on user-uploaded files is an arbitrary code execution vector. Restrict upload endpoint to `admin`/`designer` roles. Add a warning in the UI: "Only upload .pkl files from trusted sources." This is acceptable for internal BI tooling where all users are organizational employees.

**Canvas:** Single input port, single output port. Category `processor`. Property panel: model selector dropdown (fetching `/ml-models/`) + optional output field name.

**Confidence:** HIGH for the execution pattern. MEDIUM for security posture (documented and accepted risk for internal tooling).

---

## Recommended Project Structure Changes

```
backend/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       └── ml_models.py          # NEW: upload, list, delete
│   ├── models/
│   │   └── models.py                 # ADD: MLModel table
│   ├── runtime/
│   │   ├── runner.ts                 # MODIFY: branch + data_transform + template nodes
│   │   └── deno.json                 # ADD: nunjucks npm import
│   └── services/
│       ├── deno_service.py           # NO CHANGE
│       ├── source_executor.py        # EXTEND: detect 'llm' and 'pickle_model' in pre-exec
│       ├── llm_executor.py           # NEW: httpx calls per provider
│       └── ml_executor.py            # NEW: pickle.load + model.predict
├── alembic/versions/
│   └── xxxx_add_ml_models.py        # NEW: migration for MLModel table
└── models_storage/                  # NEW: volume-mounted directory for .pkl files

dashboard-app/src/
└── components/editor/
    └── FlowEditorCanvas.vue         # MODIFY: dual output ports for branch node only
```

No new Vue views are needed. Model management happens through the existing `ConnectionsView` / `ToolCatalogView` UI patterns or a small model list panel added to the existing settings area.

---

## Architectural Patterns

### Pattern 1: Signal Delegation (existing — ODS, Email)

**What:** Deno emits a two-line signal (`EXEC_X:` header + `EXEC_X_PAYLOAD:` JSON). Python parses it after Deno exits and runs the operation. The Deno node marks its output as `{ status: 'delegated' }`.

**When to use:** Terminal operations (write to DB, send email) where the result does not need to flow into a downstream Deno node.

**Not suitable for:** Nodes whose output must feed downstream nodes in the same execution.

### Pattern 2: Pre-Execution (existing — SQL/HTTP source nodes; new — LLM, Pickle)

**What:** Python detects certain node types in `pre_execute_flow_nodes()` before starting Deno. Results stored in `prefetched_outputs`. Deno receives those nodes flagged as `__pre_executed = true` and emits their pre-computed output without running them.

**When to use:** For nodes requiring Python capabilities (DB access, ML libraries, encrypted credentials) AND whose output must feed downstream Deno nodes.

**Constraint:** Pre-executed nodes receive only the initial flow payload as context — they cannot consume the output of a Deno-side transform that runs before them in the graph.

### Pattern 3: Pure Deno Execution (existing — js_script, http, join, csv; new — data_transform, template)

**What:** Node logic runs entirely inside the Deno sandbox using `executeScriptNode()`, built-in fetch, or npm packages from the import map.

**When to use:** Pure data manipulation, HTTP calls, or template rendering that does not require Python libraries or server-side encrypted credentials.

---

## Data Flow Changes

### Branch Node Flow

```
[Upstream Node]  -->  output stored as nodeOutputs.set('nodeA', payload)
                            |
                     [Branch Node]
                     evaluates condition JS
                            |
              nodeOutputs.set('branch#true', payload)   if true
              nodeOutputs.set('branch#false', payload)  if false
                        /         \
        (fromHandle='true')    (fromHandle='false')
               |                       |
           [Node A]               [Node B]
      receives payload           receives payload
      if #true is defined        if #false is defined
      otherwise: skipped         otherwise: skipped
```

### LLM / Pickle Node Flow (pre-execution)

```
PHASE 1 — Python pre_execute_flow_nodes():
  Detects llm / pickle_model nodes
  → calls llm_executor / ml_executor
  → stores results in prefetched_outputs[node_id]
  → marks node.__pre_executed = True
  → passes annotated flow JSON to Deno

PHASE 2 — Deno runner.ts:
  Sees node.__pre_executed = True
  → reads prefetched_outputs[node_id]
  → emits NODE_LOG_JSON + NODE_STATUS:success
  → stores output in nodeOutputs for downstream nodes
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI-compatible APIs (Anthropic, Groq, Gemini) | httpx in `llm_executor.py`, credentials from `LlmConfig` | Provider-agnostic; reuses existing LlmConfig + encryption |
| Nunjucks (npm) | Dynamic import in Deno runner | Declared in `deno.json`, cached at startup by `cache_runner_deps()` |
| scikit-learn models (.pkl) | `pickle.load()` in `ml_executor.py` | Requires `scikit-learn` + `pandas` in `pyproject.toml` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| FlowEditorCanvas ↔ Runner | JSON blob via WebSocket → FastAPI → Deno stdin | `fromHandle` field added to connection schema |
| runner.ts ↔ deno_service.py | stdout signal lines | No new signal types for v1.9 |
| pre_execute_flow_nodes ↔ runner.ts | `prefetched_outputs` dict + `__pre_executed` flag | LLM/Pickle use this path |
| ml_models API ↔ filesystem | File saved to `MODEL_STORAGE_PATH`, path stored in DB | Must be volume-mounted in docker-compose |

---

## Build Order with Dependency Rationale

### Phase 1: Data Transform — build first

**Why:** No canvas changes, no new Python services, no new DB tables. Pure `runner.ts` extension reusing `executeScriptNode()`. Validates the new-node build pipeline (EditorTool DB record + runner handler) with zero risk. Confirms that new `toolType` values work end-to-end before tackling complex nodes.

**Touches:** `runner.ts` (+~15 lines), one Alembic migration or DB seed for the `EditorTool` record.

### Phase 2: Templating Node — build second

**Why:** Still pure Deno, no canvas changes, no Python services. Adds one npm dependency (`nunjucks`) to `deno.json`. Validates the import-map extension process and `cache_runner_deps()` warmup for a new package.

**Touches:** `runner.ts` (+~20 lines), `deno.json` (one import entry), `EditorTool` record.

### Phase 3: LLM Node — build third

**Why:** First node using pre-execution path. Requires extending `source_executor.py` / `pre_execute_flow_nodes()` and adding `llm_executor.py`. No canvas changes, no new DB tables (uses existing `LlmConfig`). Validates the pre-execution extension pattern before applying it to the more complex Pickle node that also needs new DB tables and file upload.

**Touches:** `source_executor.py` (detect `llm` type), new `llm_executor.py`, `EditorTool` record.

### Phase 4: Pickle Model Node — build fourth

**Why:** Depends on Phase 3 pre-execution pattern. Adds the most infrastructure: new `MLModel` DB table, Alembic migration, file upload endpoint, Docker volume, `scikit-learn`/`pandas` dependencies. Isolating this complexity after the simpler pre-execution pattern is proven reduces debugging surface.

**Touches:** `models.py`, new `ml_models.py` endpoint, new `ml_executor.py`, `source_executor.py` (detect `pickle_model`), Alembic migration, `docker-compose.yml` (volume), `pyproject.toml` (deps).

### Phase 5: Conditional / Branch Node — build last

**Why:** Highest risk. Modifies the `FlowConnection` schema (adds `fromHandle`), changes canvas port rendering in `FlowEditorCanvas.vue`, changes the payload routing loop in `runner.ts`, and introduces branch pruning logic (skip subtrees with undefined payloads). Any regression here breaks graph traversal for all node types. Building last ensures a known-good baseline from the four simpler nodes to compare against. Tests should include: both branches active, only true branch active, only false branch active, branch inside a dsplit loop.

**Touches:** `FlowEditorCanvas.vue` (dual ports, `fromHandle` writing), `runner.ts` (payload routing + branch handler + skip logic), `EditorTool` record.

---

## One-Way Door Decisions

1. **`fromHandle` in `FlowConnection`** — Adding this field is backward-compatible (absent = default `'out'` behavior). However, if the branch node is later redesigned (e.g., multi-branch switch), the `fromHandle` semantics become a constraint. Choose a forward-compatible name now; `fromHandle` as a freeform string (not a union type in the DB) allows future extension to `'case_1'`, `'case_2'`, etc.

2. **Nunjucks vs Python Jinja2 for Templating** — If users expect Jinja2-specific features that Nunjucks lacks (custom filters, `| safe`, `| date`), switching later requires adding a Python executor and changing how downstream nodes receive the result. Document the supported Nunjucks syntax in the property panel tooltip at launch to set correct expectations.

3. **Local filesystem for Pickle models** — Moving to multi-replica deployment later requires migrating to S3/MinIO. A `MODEL_STORAGE_BACKEND` env var with `local` and `s3` implementations is a cheap hedge. The abstraction is simple: `save_model(id, bytes)` / `load_model(id) -> bytes`.

4. **LLM pre-execution context limitation** — LLM nodes cannot consume outputs of Deno-side transform nodes (pre-execution runs before Deno). This is a permanent architectural constraint of the current signal architecture. Document it in the LLM node's property panel: "Prompt context is the initial flow payload. To use transformed data, place an HTTP source node or SQL source node before this node."

---

## Anti-Patterns

### Anti-Pattern 1: Bidirectional Deno-Python Signaling

**What people do:** Try to make Python inject template/LLM results back into the running Deno process mid-execution.

**Why it's wrong:** `run_flow_stream()` uses `subprocess.run()` (blocking). All stdout is buffered and only available after the process exits. Writing to Deno's stdin post-start is not supported.

**Do this instead:** Pre-execute nodes whose results must flow downstream. Use signal delegation (EXEC_*) only for terminal operations.

### Anti-Pattern 2: Evaluating Conditions as Python Expressions

**What people do:** Accept a Python expression string for branch condition and `eval()` it server-side.

**Why it's wrong:** `eval()` is arbitrary code execution with no sandbox. The Deno sandbox (`executeScriptNode`) already provides process-level isolation for user code evaluation.

**Do this instead:** Branch condition is a JS boolean expression evaluated via `executeScriptNode()` in Deno, same as `js_script`.

### Anti-Pattern 3: Passing LLM API Keys Through Flow JSON

**What people do:** Store the decrypted API key in `node.props.api_key` so Deno can call the LLM directly via `fetch()`.

**Why it's wrong:** Flow JSON is stored in `flow_nodes` (PostgreSQL JSON column), included in execution history, and visible in browser DevTools WebSocket frames.

**Do this instead:** Resolve credentials from `LlmConfig` in Python during pre-execution. The Deno process never sees the key.

### Anti-Pattern 4: Single Output Port on Branch Node

**What people do:** Implement branching as "the node passes the payload through unchanged; downstream nodes each evaluate the condition themselves."

**Why it's wrong:** Both downstream branches execute regardless of condition result, wasting resources and potentially causing unintended side effects (two ODS writes, two emails sent).

**Do this instead:** Dual output handles with branch pruning — the runner skips nodes in the non-taken branch entirely.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (single Docker container) | Local filesystem for models, single Deno subprocess per execution, acceptable |
| Multiple backend replicas | Shared filesystem (NFS) or S3 for model storage; local path breaks |
| High concurrency (>20 simultaneous flows) | Deno subprocess spawning is the bottleneck; consider a Deno worker pool or job queue |

---

## Sources

- Direct codebase analysis: `runner.ts` (963 lines), `deno_service.py` (651 lines), `FlowEditorCanvas.vue`, `models.py`, `email_executor.py`, `source_executor.py`, `integration_flows.py`
- Existing pre-execution pattern: `source_executor.py::pre_execute_flow_nodes()` + `integration_flows.py` WebSocket handler
- Existing keyed output pattern: `dsplit/djoin` branching in `runner.ts` lines 809-939
- Nunjucks: https://mozilla.github.io/nunjucks/ (compatible with `{{ }}` and `{% %}` syntax, Jinja2-inspired)
- Python pickle security: https://docs.python.org/3/library/pickle.html (not safe against malicious data — documented accepted risk)

---

*Architecture research for: v1.9 Advanced Node Types — Flow Editor Extension*
*Researched: 2026-05-31*
