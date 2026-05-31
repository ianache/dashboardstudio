# Project Roadmap: Dashboard Studio

## Milestones

- ✅ **v1.6 ODS Execution Engine** — Phases 29-31 (shipped 2026-05-17)
- ✅ **v1.7 Email Node** — Phase 32 (shipped 2026-05-17)
- ✅ **v1.8 BFF Service Architecture** — Phases 33-37 (shipped 2026-05-31)
- 🚧 **v1.9 Advanced Node Types** — Phases 38-42 (in progress)

## Progress Table

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-28. Core & Extensions | Pre-v1.6 | 28/28 | Complete | 2026-05-17 |
| 29. Metadata Inspection API | v1.6 | 2/2 | Complete | 2026-05-16 |
| 30. ODS Node UI Enhancement | v1.6 | 1/1 | Complete | 2026-05-16 |
| 31. ODS Execution Engine | v1.6 | 3/3 | Complete | 2026-05-17 |
| 32. Email Node Implementation | v1.7 | 3/3 | Complete | 2026-05-17 |
| 33. BFF Foundation | v1.8 | 3/3 | Complete | 2026-05-28 |
| 34. Keycloak Auth Flow | v1.8 | 3/3 | Complete | 2026-05-28 |
| 35. FastAPI Proxy + CORS | v1.8 | 2/2 | Complete | 2026-05-28 |
| 36. CubeJS Proxy + Network Isolation | v1.8 | 2/2 | Complete | 2026-05-28 |
| 37. Frontend Migration | v1.8 | 2/2 | Complete | 2026-05-29 |
| 38. Data Transform Node | v1.9 | 1/1 | Complete | 2026-05-31 |
| 39. Templating Node | v1.9 | 1/1 | Complete | 2026-05-31 |
| 40. LLM Node | v1.9 | 1/1 | Complete | 2026-05-31 |
| 41. Pickle Model Node | v1.9 | 3/3 | Complete | 2026-05-31 |
| 42. Conditional/Branch Node | v1.9 | 1/1 | Complete | 2026-05-31 |


---

## ✅ v1.6 ODS Execution Engine (Phases 29-31) — SHIPPED 2026-05-17

<details>
<summary>View v1.6 Details</summary>

### Phase 29: Metadata Inspection API
- [x] 29-01: Implement MetadataService with PostgreSQL support.
- [x] 29-02: Expose metadata inspection via FastAPI endpoints.

### Phase 30: ODS Node UI Enhancement
- [x] 30-01: Update ODS node UI with dynamic selectors, refresh buttons, and conditional identity fields.

### Phase 31: ODS Execution Engine
- [x] 31-01: Core ODSExecutor Service (ods_executor.py with Append, Overwrite, Upsert)
- [x] 31-02: Deno Integration & Signal Protocol (runner.ts, deno_service.py)
- [x] 31-03: Validation, Testing & Hardening (validation, logging, tests, deprecation)

**Archive:** `.planning/milestones/v1.6-ROADMAP.md`

</details>

---

## ✅ v1.7 Email Node with Dynamic Templates (Phase 32) — SHIPPED 2026-05-17

<details>
<summary>View v1.7 Details</summary>

### Phase 32: Email Node Implementation
- [x] 32-01: Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration)
- [x] 32-02: Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [x] 32-03: UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

**Archive:** `.planning/milestones/v1.7-ROADMAP.md`

</details>

---

## ✅ v1.8 BFF Service Architecture (Phases 33-37) — SHIPPED 2026-05-31

<details>
<summary>View v1.8 Details</summary>

### Phase 33: BFF Foundation
- [x] 33-01: BFF Express 5 scaffold — package.json, Dockerfile, config.js, health route
- [x] 33-02: Infrastructure config — docker-compose bff + redis service, .env-bff.example
- [x] 33-03: Session store — connect-redis wired to Redis, HttpOnly cookie

### Phase 34: Keycloak Auth Flow
- [x] 34-01: ESM Migration & OIDC Client Setup — openid-client v6, discovery
- [x] 34-02: Auth routes — login, callback, me, logout (PKCE OIDC)
- [x] 34-03: Token Management & Refresh — tokenRefresh middleware, concurrent refresh coordination

### Phase 35: FastAPI Proxy + CORS Consolidation
- [x] 35-01: FastAPI proxy — Bearer injection, CORS stripping, path rewrite /bff/api → /api
- [x] 35-02: Backend CORS cleanup — remove CORSMiddleware from main.py

### Phase 36: CubeJS Proxy + Network Isolation
- [x] 36-01: CubeJS proxy — cubeToken.js HS256 signer, per-request JWT signing
- [x] 36-02: Backend network isolation — remove Traefik labels and public ports from backend/cubejs

### Phase 37: Frontend Migration
- [x] 37-01: Remove keycloak-js — delete keycloak.js, update auth store to use /bff/auth/me
- [x] 37-02: Final cleanup — main.js BFF init, router guards, keycloak-js uninstalled

**Archive:** `.planning/milestones/v1.8-ROADMAP.md`

</details>

---

## 🚧 v1.9 Advanced Node Types (Phases 38-42) — IN PROGRESS

**Milestone Goal:** Extend the integration flow editor with five new node types — data transformation, Nunjucks templating, LLM integration, ML model inference, and conditional branching.

**Build order rationale:** Lowest blast radius first. Phases 38-39 are pure Deno additions with zero infrastructure changes. Phase 40 introduces the Python pre-execution pattern. Phase 41 extends pre-execution with the highest-risk component (Pickle). Phase 42 is last because it modifies the shared FlowConnection schema used by all existing flows.

## Phases

- [x] **Phase 38: Data Transform Node** - Add a JS transform node that reshapes/maps/filters the flow payload via a CodeEditor function body
- [x] **Phase 39: Templating Node** - Add a Nunjucks templating node that renders `{{expr}}` markers against node input and outputs a text string (completed 2026-05-31)
- [x] **Phase 40: LLM Node** - Add an LLM node backed by a new encrypted LLM Connection type; Python pre-executes API calls so credentials never enter Deno (completed 2026-05-31)
- [x] **Phase 41: Pickle Model Node** - Add a node for file upload for `.pkl` models, subprocess-isolated inference, and a node that runs `predict()` within a flow (completed 2026-05-31)
- [ ] **Phase 42: Conditional/Branch Node** - Add a branch node with true/false output ports and harden cycle detection in runner.ts

## Phase Details

### Phase 38: Data Transform Node
**Goal**: Users can reshape, filter, or map flow payload data using a JavaScript function body without writing a full Script node
**Depends on**: Phase 37 (v1.8 complete)
**Requirements**: TRANS-01, TRANS-02
**Success Criteria** (what must be TRUE):
  1. User can drag a Data Transform node onto the canvas and open a CodeEditor in the property panel with a function body that receives `data` and returns the transformed payload
  2. Connecting a Data Transform node between two other nodes passes the transformed output as the next node's input — not the original payload
  3. When the input payload contains more than 10,000 rows, a warning message appears in the execution console (flow continues normally)
  4. A transform error (e.g. malformed JS, runtime exception) fails the flow with a clear error message pinned to the transform node
**Plans**: 1 plan

Plans:
- [x] 38-01-PLAN.md — Register data_transform in editor_tools + add runner.ts execution branch (completed 2026-05-31)

### Phase 39: Templating Node
**Goal**: Users can render dynamic text output by filling a Nunjucks template with flow payload data, enabling a natural predecessor step before the Email node
**Depends on**: Phase 38
**Requirements**: TMPL-01, TMPL-02
**Success Criteria** (what must be TRUE):
  1. User can drag a Templating node onto the canvas and see a "Preview" section in the property panel
  2. Clicking "Preview" renders the template against sample JSON data using the backend Jinja2 engine
  3. Running a flow with a Templating node renders the result using the Deno Nunjucks engine and passes the string to the next node
  4. Template errors are correctly caught and displayed with a `[Template Error]` prefix
**Plans**: 1 plan

Plans:
- [x] 39-01-PLAN.md — Register nunjucks_template tool + FastAPI preview + UI block + Runner logic (completed 2026-05-31)

### Phase 40: LLM Node
**Goal**: Users can call any OpenAI-compatible LLM endpoint from within a flow by selecting an encrypted LLM Connection; API keys never appear in Deno or execution history
**Depends on**: Phase 39
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04
**Success Criteria** (what must be TRUE):
  1. User can create an LLM Connection in the connections area with an endpoint URL, API key, and default model name (free-form string — no hardcoded dropdown)
  2. LLM node property panel exposes a system prompt field (designer-controlled) and a user prompt field supporting `{{payload.*}}` markers for dynamic content
  3. User can configure temperature (default 0.7) and max_tokens (default 1024) directly in the property panel
  4. When the LLM provider responds with HTTP 429, the node retries automatically using the `retry-after-ms` header value or exponential backoff, and the flow does not fail on transient rate limits
  5. The LLM property panel displays a prominent warning that LLM nodes cannot consume Data Transform node output (permanent architectural constraint)
**Plans**: 1 plan

Plans:
- [x] 40-01-PLAN.md — Register llm connection + migration + executor service + scrubbing logic (completed 2026-05-31)

### Phase 41: Pickle Model Node
**Goal**: Users can upload a scikit-learn `.pkl` model, select it in a flow node, and run batch inference against the node's input payload — in a subprocess-isolated environment that prevents RCE
**Depends on**: Phase 40
**Requirements**: MODEL-01, MODEL-02, MODEL-03, MODEL-04
**Success Criteria** (what must be TRUE):
  1. User can upload a `.pkl` file from the Settings area, see it appear in a model list, and delete it; upload is restricted to admin and designer roles
  2. Pickle deserialization and `predict()` execution happen in a subprocess-isolated Python process; a malicious pickle payload cannot escape to the host backend process
  3. The Pickle Model node property panel shows the expected feature columns for the selected model, loaded from metadata stored at upload time
  4. When the scikit-learn version in the inference environment differs from the version recorded at upload time, a `[Model Warning]` appears in the execution console
**Plans**: 3 plans

Plans:
- [x] 41-01-PLAN.md — ML Registry + Migration + Metadata Worker + RBAC API (completed 2026-05-31)
- [x] 41-02-PLAN.md — Model Management UI + Node Property Panel (completed 2026-05-31)
- [x] 41-03-PLAN.md — Isolated Inference Engine + Warning Propagation (completed 2026-05-31)

### Phase 42: Conditional/Branch Node
**Goal**: Users can split flow execution into true and false branches based on a JS boolean expression evaluated at runtime; the canvas visually distinguishes branches, and cycles are caught before they can produce wrong data
**Depends on**: Phase 41
**Requirements**: BRNCH-01, BRNCH-02, BRNCH-03
**Success Criteria** (what must be TRUE):
  1. User can add a Conditional/Branch node with a JS boolean expression in the property panel; the node renders two distinct output ports (true and false) on the canvas
  2. True port is green and false port is red; connecting a cable from either port sets `fromHandle` on the connection so runner.ts routes execution to only the matching branch
  3. When a user draws a connection that creates a cycle on the canvas, the editor rejects the connection with an error and does not allow the flow to be saved with the cycle in place
  4. A flow that previously had a silent cycle (runner.ts:153 bug) now exits with a clear error message identifying the cycle instead of producing silently wrong output
**Plans**: TBD

Plans:
- [ ] 42-01: TBD

---

*For detailed milestone history, see .planning/milestones/*
*Last updated: 2026-05-31 after v1.9 roadmap creation*
