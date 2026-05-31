# Project Research Summary

**Project:** Dashboard Studio v1.9 — Advanced Node Types
**Domain:** Visual ETL / Integration Flow Editor — Node extension for a live production system
**Researched:** 2026-05-31
**Confidence:** HIGH

## Executive Summary

Dashboard Studio v1.9 adds five new node types to an existing, production-grade visual flow editor that runs on a Deno/Python signal architecture. The core stack is already validated and shipped; this release is purely additive. Three of the five nodes (Data Transform, Templating, Conditional/Branch) can be implemented entirely inside the existing Deno runner with no new Python services, while two (LLM, Pickle Model) require Python-side pre-execution because they need access to encrypted credentials and ML libraries that Deno cannot reach.

The recommended build order is **Data Transform → Templating → LLM → Pickle Model → Conditional/Branch**, from lowest to highest blast radius — a deliberate sequencing strategy to protect the canvas connection model (shared by all existing flows) until the very end.

**Key architectural resolution:** The LLM node must use Python pre-execution, NOT Deno fetch. Decrypted API keys must never pass through Deno — the flow JSON is stored in the `flow_nodes` DB column and is visible in browser WebSocket frames and execution history. Python pre-execution resolves credentials server-side only.

**Security is the highest-risk dimension:** Pickle deserialization is confirmed RCE (CWE-502, actively exploited in 2026), and LLM prompt injection is OWASP LLM Top 10 #1. Both require first-class mitigations, not afterthoughts.

---

## Key Findings

### Recommended Stack

**Core technologies (new additions only — existing stack unchanged):**

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | `>=2.38.0,<3.0` | LLM node — covers all OpenAI-compatible endpoints (Anthropic, Groq, Ollama) via `base_url` |
| `scikit-learn` | `>=1.8.0,<2.0` | Pickle model inference |
| `joblib` | `>=1.3.0` | sklearn serialization/deserialization |
| `numpy` | `>=2.0.0,<3.0` | Input coercion for sklearn predict (hard floor — 1.x produces silent dtype changes) |
| `nunjucks@^3.2.4` | npm (Deno) | Templating node — Jinja2-inspired syntax, runs in Deno without Python signal |

**No new frontend packages needed.** The Conditional node's dual output ports are ~60 lines of CSS + template changes on the existing `FlowEditorCanvas.vue`.

**Critical version constraints:**
- `numpy>=2.0.0` — hard floor; 1.x produces silent dtype changes with sklearn 1.8
- `openai<3.0` — v3 API surface is changing; cap to avoid surprise breaking changes

### Expected Features

**Data Transform Node** — Table stakes:
- JS function body in CodeEditor; receives `data` (current payload), returns transformed payload
- Uses existing `executeScriptNode()` — zero new runner code
- `pass_through` error mode so failed transforms don't kill the entire flow
- 10k-row payload size warning

**Templating Node** — Table stakes:
- Multi-line textarea with `{{ }}` placeholder resolution via Nunjucks
- Output is a string payload; natural predecessor to the Email node
- Enables Templating → Email composition without extra Script node

**LLM Node** — Table stakes:
- Connection selector (new `LlmConfig` DataSource type), model field (free-form string — no hardcoded dropdown)
- System prompt (designer-controlled), user prompt (payload-templated with `{{payload.*}}`)
- `temperature` (default 0.7), `max_tokens` (default 1024)
- Output shape: `{ content, model, usage }`
- 429 rate-limit retry with exponential backoff
- **Warning in UI:** LLM nodes cannot consume Data Transform outputs from the same flow (permanent architectural constraint)

**Pickle Model Node** — Table stakes:
- `.pkl` file upload endpoint returning artifact ID
- Feature list config (`expected_features`) displayed in property panel
- Python-side inference via `PickleExecutor` (subprocess-isolated)
- Predictions merged into input records (augment, not replace)

**Conditional/Branch Node** — Table stakes:
- JS boolean expression evaluated in Deno
- Two labeled output ports on canvas (true=green, false=red)
- `fromHandle` field on `FlowConnection` (backward-compatible — absent = `'out'`)
- Runner skips non-taken branch entirely
- Hardened cycle detection (exit(1) on cycle — currently silent bug at runner.ts:153)

**Defer to v2+:** LLM streaming, multi-turn conversation, Switch node with N branches, ONNX format, expression builder UI, Jinja2 for-loops in Templating

**Anti-features (do not build):**
- Hardcoded model dropdown for LLM (kills Ollama/Anthropic/Mistral compatibility)
- LLM API key stored in `node.props` — must use encrypted `LlmConfig` DataSource
- Pickle model stored in DB blob (performance problems >10MB)

### Architecture Approach

The existing system has three execution patterns:
- **Pure Deno:** `js_script`, `http_rest`, `join` — everything in runner.ts
- **Python signal delegation (terminal):** ODS, Email — Deno emits EXEC_ODS/EXEC_EMAIL, Python handles, result not fed back
- **Python pre-execution:** credentials/ML nodes — Python runs before Deno starts, result injected via `prefetched_outputs`

New node distribution across patterns:
- Pure Deno: Data Transform, Templating, Conditional/Branch
- Pre-execution: LLM, Pickle Model

**Major components and changes:**

| Component | Change |
|-----------|--------|
| `runner.ts` | ADD: `data_transform`, `template`, `branch` handlers; EXTEND: `fromHandle` routing; ADD: cycle detection exit(1) |
| `source_executor.py` | EXTEND: detect `llm` and `pickle_model` in pre-execution |
| `llm_executor.py` | NEW — httpx calls with decrypted `LlmConfig` credentials via `openai` SDK |
| `ml_executor.py` | NEW — `pickle.load()` in subprocess isolation + `model.predict()` |
| `ml_models.py` endpoint | NEW — multipart upload, `MLModel` DB table, list/delete |
| `FlowEditorCanvas.vue` | MODIFY: dual output ports for branch node; write `fromHandle` on port drag |
| `deno.json` | ADD: nunjucks import map entry |

### Critical Pitfalls

1. **Pickle deserialization is RCE** — `pickle.loads()` executes arbitrary code before `predict()`. Prevention: `picklescan` pre-validation + subprocess isolation + `admin`/`designer`-only upload.

2. **LLM API key must never pass through Deno** — Key in `node.props` ends up in `flow_nodes` DB column, execution history, and browser WebSocket frames. Prevention: always resolve from `LlmConfig` in Python pre-execution.

3. **Prompt injection via payload data** — `{{payload.description}}` in LLM prompts inherits whatever upstream sources provide. Prevention: `messages` role separation (system/user); sanitize and length-limit payload fields.

4. **Conditional/Branch cycle detection must be enforced** — `getTopologicalOrder()` currently has a silent bug at runner.ts:153 ("we'll proceed for now"). With a branch node, this produces silently wrong data flow. Prevention: exit(1) on cycle + canvas DFS check before committing an edge.

5. **Scikit-learn version mismatch causes silent wrong predictions** — A model trained on sklearn 1.3 loaded under 1.5 may produce incorrect `predict()` outputs without throwing. Prevention: extract `__sklearn_version__` at upload; store version in `MLModel` row; warn on mismatch.

6. **LLM nodes cannot consume Data Transform output** — Pre-execution runs before Deno starts. This is a permanent architectural constraint. Must appear as a first-class warning in the LLM property panel.

7. **Anthropic API requires extra header** — `openai` SDK with `base_url=https://api.anthropic.com/v1` requires `anthropic-version: 2023-06-01` header. Missing it causes 400 errors that look like auth failures.

---

## Implications for Roadmap

**5 phases, starting at phase 38:**

| Phase | Node | Risk | Rationale |
|-------|------|------|-----------|
| 38 | Data Transform | LOW | Zero infrastructure; validates new-node build pipeline |
| 39 | Templating (Nunjucks) | LOW | Pure Deno; validates import-map extension |
| 40 | LLM Node | MEDIUM | First pre-execution node; validates pattern before Pickle |
| 41 | Pickle Model | HIGH | Maximum infrastructure; depends on pre-execution pattern |
| 42 | Conditional/Branch | HIGH | Modifies shared `FlowConnection` schema; highest regression risk |

**Research flags (phases needing deeper review before planning):**
- Phase 41 (Pickle): `picklescan` bypass vectors — verify subprocess isolation covers the gap
- Phase 42 (Conditional/Branch): DSplit/DJoin interaction — confirm `fromHandle` doesn't collide with existing DSplit keyed output format

**Standard patterns (skip pre-planning research):**
- Phase 38 (Data Transform): trivial `executeScriptNode` alias
- Phase 39 (Templating): Nunjucks API is stable and well-documented
- Phase 40 (LLM): pre-execution pattern proven; `openai` SDK is production-validated

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All packages verified against PyPI/npm as of 2026-05-31 |
| Features | HIGH (architecture) / MEDIUM (behavioral) | Architecture sourced from codebase; behavioral patterns from n8n/Node-RED docs |
| Architecture | HIGH | Based on direct analysis of runner.ts (963 lines), deno_service.py (651 lines), and related services |
| Pitfalls | HIGH | Critical pitfalls verified against named CVEs, OWASP LLM Top 10 2025, and specific runner.ts line references |

**Overall confidence:** HIGH

### Gaps to Address

- **Anthropic API header requirement:** Document `anthropic-version` header in the LLM property panel UI
- **`picklescan` sufficiency:** Known bypass vectors exist; subprocess isolation is the stronger mitigation — verify coverage before Phase 41
- **Nunjucks filter parity:** Users familiar with Email node's Jinja2 will notice missing filters (`| date`, `| tojson`). Document divergences in property panel tooltip at launch
- **LLM node context limitation:** Cannot consume Data Transform output — permanent constraint, must appear prominently in UI

---

*Research completed: 2026-05-31*
*Ready for roadmap: yes*
