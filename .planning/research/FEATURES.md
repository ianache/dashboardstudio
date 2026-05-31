# Feature Research — v1.9 Advanced Node Types

**Domain:** Visual ETL / Integration Flow Editor — Advanced Node Types
**Researched:** 2026-05-31
**Confidence:** HIGH (architecture sourced from codebase) / MEDIUM (behavioral patterns from n8n, Node-RED, Airflow docs)

---

## How Each Node Type Works in the Wild

This section captures the domain consensus from n8n, Node-RED, Apache Airflow, and Zapier before applying it to Dashboard Studio's specific runtime model.

---

## Node 1: Conditional / Branch Node

### How It Works in the Wild

n8n's IF node evaluates a condition and routes items to one of two outputs labeled "true" and "false". Each output is a separate wire drawn from a distinct port on the node's right side. Node-RED's Switch node extends this to N outputs, each mapping to a rule. Airflow's `BranchPythonOperator` returns a task_id string and all other branches are marked "skipped" — downstream convergence requires a `none_failed_min_one_success` trigger rule.

**What users configure:**
- A JS boolean expression evaluated against the current payload (e.g., `payload.status === 'active'`)
- Two output branches: true path and false path (named connections, not unlabeled wires)

**Input / Output:**
- Input: any payload (object or array)
- Output: same payload unchanged, routed to either the true or false output port
- The condition does NOT transform the data — it only routes it

### Application to Dashboard Studio

**The core problem: the canvas model is `{ from, to }` with no port field.**

Currently every node has exactly one output port (`fec-port--out`), positioned at the center-right of the node. A conditional node requires two output ports — one for true, one for false — so connections must carry a `port` field (e.g., `{ from, to, fromPort: 'true' | 'false' }`).

The runner's topological sort must also change: when a conditional node is encountered, it evaluates the expression and adds the false-branch nodes to a `skippedNodes` set (the DSplit/DJoin pattern already demonstrates this). The existing `skippedNodes` mechanism in `runner.ts` is the correct template.

**What happens when the condition fails (false)?**
- Items are routed to the false-branch connected nodes
- If no node is connected to the false port, execution continues without error (same semantics as n8n: unconnected branches are silently skipped)
- The node itself always emits `success` status — it is the routing that changes, not the node's success state

**What happens on expression error?**
- The node emits `error` status and execution halts (same as other nodes calling `Deno.exit(1)`)

### Table Stakes vs Nice-to-Haves

| Feature | Category | Notes |
|---------|----------|-------|
| JS boolean expression evaluated in Deno (uses `executeScriptNode` pattern) | Table stakes | Reuses existing infrastructure |
| Two labeled output ports (true / false) on node UI | Table stakes | Requires canvas port model change |
| Connection carries `fromPort` field (`'true'` or `'false'`) | Table stakes | DB schema change for connections |
| Runner skips false-branch nodes when condition is true (and vice versa) | Table stakes | Mirror DSplit's `skippedNodes` pattern |
| Node emits `success` status regardless of which branch taken | Table stakes | Routing is not a failure |
| Silent pass-through if false port has no downstream connection | Table stakes | Match n8n semantics |
| Inline expression editor with syntax hints | Table stakes | Reuse existing CodeEditor component |
| Expression builder UI (point-and-click condition builder) | Nice-to-have | High complexity; defer |
| Switch node with N branches | Nice-to-have | Defer until IF is validated |

**Complexity: HIGH.** Requires canvas model change (port field), runner change (branch-aware execution), and SVG rendering of two output ports with labels.

---

## Node 2: Data Transform Node

### How It Works in the Wild

n8n's Code node runs in "Run Once for All Items" mode and expects the user to write a JS function body that receives `$input.all()` and returns an array of items. Zapier's Formatter step applies built-in operations (text, number, date). The common denominator in every platform: the user writes a JS function that receives the payload and returns a new payload. The function can map, filter, reduce, or reshape.

**What users configure:**
- A JS function body that receives `payload` (the upstream data) and returns the transformed data
- Optional: mode toggle — "Process each item" vs "Process all items at once"

**Input / Output:**
- Input: any payload (typically an array of objects)
- Output: any payload returned by the user function

### Application to Dashboard Studio

This is essentially the existing `js_script` (Script node) with two differences:
1. The UX intent is explicit: "transform data", not "run arbitrary code"
2. The function signature is enforced: `function transform(payload) { return newPayload; }` — the user writes only the body

The runner execution is identical to `js_script` — call `executeScriptNode` with the user code. The distinction is purely in the UI/UX (different label, different icon, different property panel hint text, different toolType name `data_transform`).

**What happens when the transform throws?**
- Node emits `error` status, execution halts (same as `js_script`)

**What happens when the transform returns null/undefined?**
- Should be treated as "pass payload unchanged" (n8n behavior) or error (strict mode). Recommended: emit a warning and pass the original payload through.

### Table Stakes vs Nice-to-Haves

| Feature | Category | Notes |
|---------|----------|-------|
| JS function body in CodeEditor panel | Table stakes | Same as Script node |
| Enforced signature hint: `// payload is the input; return transformed data` | Table stakes | Comment scaffolding in default code |
| Runs via `executeScriptNode` in Deno | Table stakes | Zero new runtime work |
| Null/undefined return → pass payload through with warning | Table stakes | Defensive behavior |
| Mode toggle: per-item vs batch | Nice-to-have | Low value for current use cases; defer |
| Built-in transform helpers (jq-like) | Nice-to-have | Very high complexity; anti-feature risk |
| Visual field mapper UI | Nice-to-have | Complex; use Code node pattern instead |

**Complexity: LOW.** Runtime is identical to the Script node. The work is UI labeling, a new `toolType` database entry, and a distinct property panel template. No new runner code needed.

**Dependency:** Requires a `data_transform` entry in the `editor_tools` table (same `prop_defs` as `js_script`, different label/icon/category).

---

## Node 3: Templating Node

### How It Works in the Wild

n8n's Set node with "expression mode" inlines `{{ $json.field }}` syntax into string values. Jinja2 (used in the existing Email node) renders a template string against a context dict. The existing Dashboard Studio Email node already uses this exact pattern — `Jinja2 SandboxedEnvironment` in Python renders `{{expr}}` placeholders.

**What users configure:**
- A template string with `{{expression}}` placeholders (multi-line, potentially with HTML or structured text)
- Optional: output format label (plain text, HTML, markdown — purely cosmetic)

**Input / Output:**
- Input: any payload (object or array) — used as the template context
- Output: a single string (the rendered template)

### Application to Dashboard Studio

The Python-side rendering infrastructure already exists in `email_executor.py`. The Templating node needs a Deno-side signal (`EXEC_TEMPLATE`) handled in Python, similar to `EXEC_EMAIL`. However, there is a simpler alternative: since the template resolution logic `resolveString()` already exists in `runner.ts` and handles `{{path.to.val}}` syntax, a basic templating node can run entirely in Deno without a Python roundtrip.

The existing `resolveString(str, context)` in `runner.ts` is the engine. The user writes a multi-line template, the runner calls `resolveString` on every line, and emits the result as a string payload.

**What happens when a placeholder is not found?**
- Current `resolveString` behavior: leaves the placeholder text unchanged (e.g., `{{missing.field}}` stays as is)
- This is the correct table-stakes behavior (matches Jinja2 undefined = silent, matches n8n)

**What happens when the input payload is an array?**
- The template context should be set to `payload[0]` for single-object array (common upstream pattern)
- Or expose `records` as a context variable that iterates the array inside the template

### Table Stakes vs Nice-to-Haves

| Feature | Category | Notes |
|---------|----------|-------|
| Multi-line template textarea in properties panel | Table stakes | Not a CodeEditor — plain textarea |
| `{{dot.path}}` placeholder resolution against payload | Table stakes | Reuse `resolveString()` from runner.ts |
| Output is a string emitted as `context.payload` | Table stakes | Downstream nodes receive string payload |
| Array input: expose `payload` (array) and first item's fields directly | Table stakes | Match Email node templating context |
| Placeholder left unchanged if path not found | Table stakes | Current `resolveString` behavior |
| Preview panel rendering template with sample data | Nice-to-have | Medium complexity; useful but not blocking |
| Jinja2 `for` loops / `if` blocks | Nice-to-have | Requires Python delegation via EXEC signal |
| Output format selector (HTML/text/markdown) | Anti-feature | Cosmetic complexity with no runtime effect |

**Complexity: LOW.** Can run entirely in Deno using the existing `resolveString`. No new Python executor needed for the basic version. Output is a string.

**Dependency:** The Email node is the primary consumer — Templating node output → Email node body is a natural flow.

---

## Node 4: LLM Node

### How It Works in the Wild

n8n's OpenAI node, Langchain-based automation tools, and every major flow editor in 2025-2026 standardized on the OpenAI Chat Completion API format (`POST /v1/chat/completions`). The API is provider-agnostic when the endpoint is configurable. Users configure:
- An HTTP connection (base URL + API key) — reuses existing Connection infrastructure
- Model name string (e.g., `gpt-4o`, `claude-3-5-sonnet`, `llama3`)
- System prompt (static string or template with `{{}}`)
- User prompt (template with `{{}}` resolved against payload)
- Temperature (float 0.0–2.0, default 0.7)
- Max tokens (integer, default provider-dependent)
- Input: the user prompt, optionally including serialized payload
- Output: `{ content: string, model: string, usage: { prompt_tokens, completion_tokens } }`

**What is table stakes (industry consensus):**
- `model`, `system_prompt`, `user_prompt`, `temperature`, `max_tokens`
- Connection selector (HTTP type with bearer auth / API key)
- Output is the assistant's `content` string (plus metadata in a structured object)

**What is nice-to-have:**
- Streaming responses (requires SSE handling in Deno — complex)
- Multi-turn conversation history
- Tool calling / function calling
- Response format enforcement (JSON mode)

### Application to Dashboard Studio

The existing `http_rest` node already does `fetch()` in Deno with Bearer auth headers. The LLM node is essentially a specialized HTTP node with a fixed JSON body shape. This means the runner can execute it entirely in Deno — no Python delegation needed.

The Connection type should be `http_jwt` or a new `llm` type that stores `{ base_url, api_key, model_default }`. The simplest approach: reuse the existing HTTP connection type (stores `base_url` and `api_key`) and let the node override the model per-call.

**Body shape sent to the API:**
```json
{
  "model": "<node.props.model>",
  "messages": [
    { "role": "system", "content": "<resolved system_prompt>" },
    { "role": "user",   "content": "<resolved user_prompt>" }
  ],
  "temperature": <node.props.temperature>,
  "max_tokens": <node.props.max_tokens>
}
```

**What the node emits as output:**
```json
{
  "content": "<assistant reply>",
  "model": "<model used>",
  "usage": { "prompt_tokens": N, "completion_tokens": N, "total_tokens": N }
}
```

**What happens when the API returns an error?**
- HTTP non-2xx → node emits `error` status, execution halts
- Connection not found → validation error before request

**What happens when max_tokens is exceeded?**
- The API returns a truncated response with `finish_reason: "length"` — the node should emit `success` with the truncated content (it is the model's choice, not an error)

### Table Stakes vs Nice-to-Haves

| Feature | Category | Notes |
|---------|----------|-------|
| Connection selector (HTTP type, stores base URL + API key) | Table stakes | Reuse existing DataSource HTTP type |
| Model field (string, free-form to support any provider) | Table stakes | No hardcoded model list |
| System prompt textarea (supports `{{}}` template syntax) | Table stakes | Resolved via `resolveString` before send |
| User prompt textarea (supports `{{}}` template syntax) | Table stakes | Primary input, payload injected here |
| Temperature (0.0–2.0 float slider or number input, default 0.7) | Table stakes | Industry-standard parameter |
| Max tokens (integer, default 1024) | Table stakes | Prevents runaway costs |
| Output: `{ content, model, usage }` object as next payload | Table stakes | Downstream nodes can use `{{content}}` |
| HTTP 4xx/5xx → node error, execution halt | Table stakes | Match existing HTTP node behavior |
| Streaming responses | Nice-to-have | Requires SSE in Deno subprocess; defer |
| Multi-turn conversation (history management) | Nice-to-have | Requires stateful context; defer |
| JSON response format enforcement | Nice-to-have | Add `response_format` field later |
| Tool calling / function calling | Nice-to-have | Large feature; separate node type if needed |
| Hardcoded model dropdown (OpenAI-only) | Anti-feature | Kills compatibility with Ollama, Anthropic, etc. |

**Complexity: MEDIUM.** The Deno execution is straightforward (HTTP POST). The UI requires 5 configurable fields with the system/user prompts being multi-line. The main complexity is UX: the user prompt needs clear guidance on how to inject payload data via `{{}}` syntax.

**Dependency:** Requires an HTTP-type DataSource connection configured with the LLM provider's base URL and API key. No new connection type needed — reuse existing HTTP connection, or add a simple `llm` connection type that stores `{ base_url, api_key }`.

---

## Node 5: Pickle Model Node

### How It Works in the Wild

scikit-learn's `predict()` method accepts:
- A 2D NumPy array of shape `(n_samples, n_features)` — the canonical form
- A pandas DataFrame (column names must match training feature names)
- A list of lists (Python auto-converts to array)

The safest format for a runtime that receives JSON data from Deno: a list of dicts (one dict per sample, keys = feature names). Python-side: `pd.DataFrame(records)` then `model.predict(df)`.

**What users configure:**
- Upload a `.pkl` file (the trained model)
- Feature list (column names expected by the model, in order)
- Output column name (what to call the prediction result field)
- Optional: predict mode — `predict` (class labels) vs `predict_proba` (probabilities)

**Input / Output:**
- Input: array of objects where each object has the feature fields (e.g., `[{ age: 25, salary: 50000 }, ...]`)
- Output: same array with a new field added containing the prediction (e.g., `[{ age: 25, salary: 50000, prediction: 1 }, ...]`)

**What happens when `predict()` throws?**
- Missing feature column → ValueError → node emits `error` and halts
- Model file corrupted → UnpicklingError → same
- Feature count mismatch → same

**What happens with Python version / sklearn version mismatch?**
- Pickle files are NOT forward/backward compatible across major sklearn versions. A model pickled with sklearn 1.3 may fail to load under 1.5. This is the single most critical pitfall for this node.

### Application to Dashboard Studio

The Pickle node requires Python-side execution because Deno cannot load `.pkl` files. This means it must follow the `EXEC_ODS` / `EXEC_EMAIL` delegation pattern:
1. Deno emits `EXEC_PICKLE:<node_id>:<batch_id>`
2. Deno emits `EXEC_PICKLE_PAYLOAD:<json>` (the data records + model reference)
3. Python's `deno_service.py` intercepts the signal, calls a new `PickleExecutor`
4. `PickleExecutor` loads the pkl file, runs `predict()`, returns results
5. Results are injected back into `context.payload` via the existing ods_result pattern

**Model file storage:** The `.pkl` file needs to be stored server-side. Options:
- Backend filesystem: simple, works, but not containerization-friendly
- Database blob: acceptable for small models (< 10MB)
- Recommended: store as a named artifact in a backend upload endpoint, referenced by an artifact ID in the node props

**Input format to `predict()`:**
```python
import pandas as pd
df = pd.DataFrame(records)  # records = list of dicts from payload
features = node_props['features']  # ordered list of column names
X = df[features]
predictions = model.predict(X)
# Merge predictions back: zip(records, predictions)
```

### Table Stakes vs Nice-to-Haves

| Feature | Category | Notes |
|---------|----------|-------|
| Upload endpoint for `.pkl` file (stores server-side, returns artifact ID) | Table stakes | Required before node can function |
| Node props store `artifact_id` (not raw file path) | Table stakes | Portable across environments |
| Feature list config (ordered list of column names) | Table stakes | Required for DataFrame construction |
| Output field name config (default: `prediction`) | Table stakes | Merges prediction into each record |
| `predict` mode (class labels) | Table stakes | Primary use case |
| Python-side `PickleExecutor` following EXEC_PICKLE signal pattern | Table stakes | Required for Deno-to-Python delegation |
| Error if feature columns missing from payload | Table stakes | Clear error message with missing field name |
| `predict_proba` mode (probability scores) | Nice-to-have | Add `predict_mode` toggle; returns array of floats |
| sklearn version pinning warning in UI | Nice-to-have | Display sklearn version model was trained on |
| ONNX export as alternative to pickle | Nice-to-have | Better cross-version compatibility; separate feature |
| Model versioning / multiple artifact storage | Nice-to-have | Defer; file upload + ID is sufficient for v1.9 |

**Complexity: HIGH.** Requires: (1) a file upload API endpoint, (2) artifact storage schema, (3) a new `PickleExecutor` class, (4) the EXEC_PICKLE signal protocol in `deno_service.py`, (5) `pandas` and `scikit-learn` as new backend dependencies, (6) handling the sklearn version compatibility pitfall.

---

## Feature Landscape Summary

### Table Stakes (All 5 Nodes)

| Feature | Node | Complexity | Dependencies |
|---------|------|------------|--------------|
| Two labeled output ports (true/false) on canvas | Conditional | HIGH | Canvas port model change, connection schema change |
| `fromPort` field on connections (true/false) | Conditional | HIGH | DB migration for connections table |
| Expression evaluator (reuse `executeScriptNode`) | Conditional | LOW | No new runtime code |
| False-branch `skippedNodes` in runner | Conditional | MEDIUM | Mirror DSplit pattern |
| `data_transform` toolType DB entry | Transform | LOW | New DB row, no code |
| Function body CodeEditor with enforced signature hint | Transform | LOW | Reuse CodeEditor component |
| Null-return pass-through behavior | Transform | LOW | Two-line runner guard |
| Multi-line template textarea | Templating | LOW | No CodeEditor — plain textarea |
| `resolveString()` applied to template body | Templating | LOW | Already exists in runner.ts |
| String output as `context.payload` | Templating | LOW | One-liner in runner |
| Connection selector (HTTP type) | LLM | LOW | Reuse existing DataSource HTTP |
| Model, system prompt, user prompt, temperature, max_tokens fields | LLM | LOW | Standard prop_defs |
| OpenAI-compatible POST via Deno fetch | LLM | LOW | Same pattern as http_rest node |
| `{ content, model, usage }` output shape | LLM | LOW | Parse API response |
| `.pkl` upload endpoint + artifact storage | Pickle | HIGH | New API endpoint + DB table |
| `PickleExecutor` Python class | Pickle | HIGH | New service, new deps |
| EXEC_PICKLE signal protocol in deno_service.py | Pickle | MEDIUM | Mirror EXEC_ODS pattern |
| Feature list config, prediction column merge | Pickle | MEDIUM | DataFrame construction |

### Differentiators

| Feature | Node | Value | Notes |
|---------|------|-------|-------|
| `{{}}` syntax in LLM prompts | LLM | High | Connects pipeline data directly into prompts without extra nodes |
| Prediction merged into records (augment, not replace) | Pickle | High | Downstream nodes still have all original fields |
| Conditional routes payload unchanged (pure routing) | Conditional | Medium | Preserves data integrity across branches |
| Templating node output feeds Email node | Templating | High | Creates a natural Templating to Email composition |

### Anti-Features (Do Not Build)

| Anti-Feature | Reason | Alternative |
|--------------|--------|-------------|
| Expression builder UI for Conditional | Huge complexity for marginal UX gain — target users are developers | Plain JS expression textarea with examples |
| Hardcoded model dropdown for LLM | Excludes Ollama, Anthropic, Mistral, etc. | Free-form `model` string field |
| LLM streaming | Requires SSE in Deno subprocess — conflicts with batch signal model | Batch response is sufficient for ETL context |
| Jinja2 for loops in Templating node | Requires Python delegation, adds EXEC_TEMPLATE signal overhead | Use the existing Email node's Jinja2 support; or use Script node for complex logic |
| ONNX as default Pickle format | Adds major dependency, different workflow | Support as future upgrade; start with `.pkl` |
| Pickle model file stored in DB blob | Performance problems above 10MB, not streamable | Filesystem artifact with artifact_id reference |

---

## Feature Dependencies

```
Conditional Node
    requires -> canvas port model change (fromPort on connections)
    requires -> runner.ts branch-aware execution (skippedNodes pattern)
    can reuse -> executeScriptNode (boolean expression evaluation)

Data Transform Node
    can reuse -> executeScriptNode (identical runtime)
    requires -> new toolType DB entry only

Templating Node
    can reuse -> resolveString() in runner.ts
    enhances -> Email Node (natural predecessor)
    does NOT require -> Python delegation (Deno-only)

LLM Node
    requires -> HTTP-type DataSource connection (existing)
    can reuse -> fetch() pattern from http_rest node
    does NOT require -> Python delegation (Deno-only)

Pickle Model Node
    requires -> file upload endpoint (new)
    requires -> artifact storage (new DB table or filesystem path)
    requires -> PickleExecutor Python class (new service)
    requires -> EXEC_PICKLE signal in deno_service.py (new protocol)
    requires -> pandas + scikit-learn as backend deps (new)
```

---

## Phase Sequencing Recommendation

Phase order based on implementation complexity and dependencies:

1. **Data Transform Node** — Zero new infrastructure. New DB row + UX label. Ship first to validate toolType extension pattern.

2. **Templating Node** — Zero new runtime. Deno-only `resolveString` application. Natural next step; enables Templating to Email flows.

3. **LLM Node** — Deno-only HTTP call. Requires existing HTTP connection. Medium UI complexity (5 fields + two multi-line textareas). No new Python code.

4. **Conditional / Branch Node** — Highest canvas complexity. Requires port model migration (DB + frontend + runner). Do after simpler nodes are shipped to reduce risk.

5. **Pickle Model Node** — Highest backend complexity. Requires new executor, upload API, dependencies. Ship last.

Rationale: Phases 1-3 are additive (new toolType entries + runner else-if branches). Phase 4 is invasive (changes the canvas connection model). Phase 5 is expansive (new backend service stack). This ordering minimizes blast radius per phase.

---

## Edge Cases Requiring Explicit Design Decisions

| Scenario | Node | Recommended Behavior |
|----------|------|---------------------|
| Condition expression syntax error at runtime | Conditional | `error` status, halt; expression is user code so errors are expected and logged |
| Condition true but no node connected to true port | Conditional | `success` status, execution ends (no downstream nodes to run) |
| Condition false but no node connected to false port | Conditional | `success` status, execution ends — this is intentional "if only" pattern |
| Transform returns `null` or `undefined` | Transform | Emit console warning, pass original `context.payload` through unchanged |
| Template placeholder references missing field | Templating | Leave placeholder text as-is (current `resolveString` behavior) — document clearly |
| LLM API returns HTTP 429 (rate limit) | LLM | `error` status, halt — retry logic is out of scope for v1.9 |
| LLM `finish_reason: "length"` (truncated) | LLM | `success` status — truncation is model behavior, not a node failure |
| Pickle: feature column missing from payload record | Pickle | `error` status, halt — log which column is missing |
| Pickle: model sklearn version mismatch | Pickle | `error` status with descriptive message — document that model must match backend sklearn version |
| Pickle: payload is empty array | Pickle | `success` status, output empty array — match ODS node behavior |

---

## Sources

- n8n IF node documentation: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/
- n8n conditional logic guide: https://theowllogic.com/conditional-logic-in-n8n
- Node-RED Switch node: https://flowfuse.com/node-red/core-nodes/switch/
- Airflow branching: https://docs.astronomer.io/learn/airflow-branch-operator
- scikit-learn predict() input format: https://machinelearningmastery.com/make-predictions-scikit-learn/
- scikit-learn pickling implications: https://uwekorn.com/2021/04/26/implications-of-pickling-ml-models.html
- n8n data transformation: https://docs.n8n.io/data/transforming-data/
- OpenAI-compatible API standard: https://www.onprem.ai/en/knowhow/llm-api-standards/
- n8n OpenAI integration 2026: https://tokenmix.ai/blog/n8n-openai-compatible-api
- Dashboard Studio runner.ts, deno_service.py, FlowEditorCanvas.vue (codebase — HIGH confidence)

---

*Feature research for: Dashboard Studio v1.9 Advanced Node Types*
*Researched: 2026-05-31*
