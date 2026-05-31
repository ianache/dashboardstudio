# Requirements: Dashboard Studio v1.9

**Defined:** 2026-05-31
**Core Value:** Extender el editor de flujos con cinco nuevos tipos de nodo — lógica condicional, transformación de datos, plantillas de texto, LLM, y modelos ML

## v1.9 Requirements

### Data Transform

- [ ] **TRANS-01**: User can add a Data Transform node with a JS function body (CodeEditor) that receives `data` and returns the transformed payload
- [ ] **TRANS-02**: A warning appears in the execution console when the transform input payload exceeds 10,000 rows

### Templating

- [ ] **TMPL-01**: User can add a Templating node with a multi-line Nunjucks template textarea; `{{expr}}` markers resolve against node input; output is a text string
- [ ] **TMPL-02**: User can preview the rendered template output against sample data directly in the node property panel

### LLM

- [ ] **LLM-01**: User can configure an LLM Connection with endpoint URL, API key, and default model name (free-form string — no hardcoded dropdown)
- [ ] **LLM-02**: LLM node has separate system prompt (designer-controlled) and user prompt fields; user prompt supports `{{payload.*}}` markers for dynamic content
- [ ] **LLM-03**: LLM node has configurable temperature (default 0.7) and max_tokens (default 1024) parameters
- [ ] **LLM-04**: LLM node retries automatically on 429 rate-limit responses using the provider's `retry-after-ms` header or exponential backoff

### Pickle Model

- [ ] **MODEL-01**: User can upload a `.pkl` file from the integrations area and list/delete uploaded models
- [ ] **MODEL-02**: Pickle model inference runs in a subprocess-isolated environment to prevent RCE from malicious pickle files
- [ ] **MODEL-03**: Pickle Model node property panel shows the expected feature columns for the selected model
- [ ] **MODEL-04**: The scikit-learn version is stored at upload time; a warning is shown if the inference environment version differs

### Conditional/Branch

- [ ] **BRNCH-01**: User can add a Conditional/Branch node with a JS boolean expression; the node has two output ports (True/False) on the canvas
- [ ] **BRNCH-02**: True/False output ports are labeled and visually differentiated (green=true, red=false) on the canvas
- [ ] **BRNCH-03**: Flows with circular connections exit with a clear error instead of proceeding silently (fix runner.ts:153)

## v2 Requirements

### LLM (Future)

- **LLM-F01**: LLM node supports streaming responses visible in the execution console
- **LLM-F02**: LLM node supports multi-turn conversation history within a single flow run
- **LLM-F03**: LLM node can enforce JSON response format (structured output)

### Pickle Model (Future)

- **MODEL-F01**: ONNX format supported as an alternative to pickle (safer serialization)
- **MODEL-F02**: Model versioning — multiple versions of the same model uploadable and selectable per-node

### Conditional/Branch (Future)

- **BRNCH-F01**: Switch node with N configurable branches (extend IF node once validated)
- **BRNCH-F02**: Visual expression builder UI for the branch condition (no-code)

## Out of Scope

| Feature | Reason |
|---------|--------|
| pass_through error mode on Transform | Descoped by user — flow fails explicitly on transform errors for now |
| Model training in the platform | Out of scope — platform is inference-only; training happens externally |
| LLM API key in node.props | Security anti-feature — keys must always flow through encrypted DataSource |
| Hardcoded model dropdown in LLM node | Anti-feature — breaks Ollama, Anthropic, Mistral compatibility |
| Pickle model stored in DB blob | Performance issue >10MB; filesystem storage with Docker volume instead |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRANS-01 | Phase 38 | Pending |
| TRANS-02 | Phase 38 | Pending |
| TMPL-01 | Phase 39 | Pending |
| TMPL-02 | Phase 39 | Pending |
| LLM-01 | Phase 40 | Pending |
| LLM-02 | Phase 40 | Pending |
| LLM-03 | Phase 40 | Pending |
| LLM-04 | Phase 40 | Pending |
| MODEL-01 | Phase 41 | Pending |
| MODEL-02 | Phase 41 | Pending |
| MODEL-03 | Phase 41 | Pending |
| MODEL-04 | Phase 41 | Pending |
| BRNCH-01 | Phase 42 | Pending |
| BRNCH-02 | Phase 42 | Pending |
| BRNCH-03 | Phase 42 | Pending |

**Coverage:**
- v1.9 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 (complete)

---
*Requirements defined: 2026-05-31*
*Last updated: 2026-05-31 — traceability confirmed after roadmap creation*
