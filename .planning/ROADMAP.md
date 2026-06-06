# Project Roadmap: Dashboard Studio

## Milestones

- ✅ **v1.6 ODS Execution Engine** — Phases 29-31 (shipped 2026-05-17)
- ✅ **v1.7 Email Node** — Phase 32 (shipped 2026-05-17)
- ✅ **v1.8 BFF Service Architecture** — Phases 33-37 (shipped 2026-05-31)
- ✅ **v1.9 Advanced Node Types** — Phases 38-42 (shipped 2026-05-31)
- 🚧 **v2.0 BI Analyst** — Phases 43-46 (in progress)

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
| 41. Pickle Model Node | 3/3 | Complete   | 2026-06-01 | 2026-05-31 |
| 42. Conditional/Branch Node | v1.9 | 1/1 | Complete | 2026-05-31 |
| 43. AI Service Foundation | v2.0 | 2/2 | Complete | 2026-05-31 |
| 44. AI Analyst Skills | v2.0 | 2/2 | Complete | 2026-05-31 |
| 45. BFF Integration | 1/1 | Complete   | 2026-06-01 | - |
| 46. Chat UI | 3/3 | Complete   | 2026-06-01 | - |


---

<details>
<summary>✅ v1.6 ODS Execution Engine (Phases 29-31) — SHIPPED 2026-05-17</summary>

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

<details>
<summary>✅ v1.7 Email Node with Dynamic Templates (Phase 32) — SHIPPED 2026-05-17</summary>

### Phase 32: Email Node Implementation
- [x] 32-01: Core Email Service (email_executor.py, email_schemas.py, Jinja2 integration)
- [x] 32-02: Deno Integration (EXEC_EMAIL signal, runner.ts modifications, deno_service.py handler)
- [x] 32-03: UI & Testing (FlowEditorCanvas.vue updates, HTML sanitization, unit tests)

**Archive:** `.planning/milestones/v1.7-ROADMAP.md`

</details>

---

<details>
<summary>✅ v1.8 BFF Service Architecture (Phases 33-37) — SHIPPED 2026-05-31</summary>

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

<details>
<summary>✅ v1.9 Advanced Node Types (Phases 38-42) — SHIPPED 2026-05-31</summary>

**Milestone Goal:** Extend the integration flow editor with five new node types — data transformation, Nunjucks templating, LLM integration, ML model inference, and conditional branching.

### Phase 38: Data Transform Node
- [x] 38-01-PLAN.md — Register data_transform in editor_tools + add runner.ts execution branch (completed 2026-05-31)

### Phase 39: Templating Node
- [x] 39-01-PLAN.md — Register nunjucks_template tool + FastAPI preview + UI block + Runner logic (completed 2026-05-31)

### Phase 40: LLM Node
- [x] 40-01-PLAN.md — Register llm connection + migration + executor service + scrubbing logic (completed 2026-05-31)

### Phase 41: Pickle Model Node
- [x] 41-01-PLAN.md — ML Registry + Migration + Metadata Worker + RBAC API (completed 2026-05-31)
- [x] 41-02-PLAN.md — Model Management UI + Node Property Panel (completed 2026-05-31)
- [x] 41-03-PLAN.md — Isolated Inference Engine + Warning Propagation (completed 2026-05-31)

### Phase 42: Conditional/Branch Node
- [x] 42-01-PLAN.md — Branch node UI, fromHandle protocol, BFS cycle detection (completed 2026-05-31)

</details>

---

## 🚧 v2.0 BI Analyst (Phases 43-46) — IN PROGRESS

**Milestone Goal:** Deploy an interactive BI analyst agent that reads the current dashboard context, executes analytical queries via CubeJS, and triggers pre-configured skills — all from a chat panel embedded in the dashboard designer. The browser session never leaves the platform.

**Build order rationale:** Service before tools before gateway before UI. Phase 43 establishes the Python microservice skeleton so Phases 44-46 have a stable target. Phase 44 wires the two agent tools (CubeJS + skills catalog) that deliver the core analytical value. Phase 45 adds the BFF proxy layer so the frontend can reach the service securely. Phase 46 delivers the chat panel that users actually interact with.

## Phases

- [x] **Phase 43: AI Service Foundation** - New Python microservice (ai-analyst/) with Google ADK, Gemini API, and a basic `/chat` endpoint that accepts a message and returns a streamed agent response
- [x] **Phase 44: AI Analyst Skills** - CubeJS query tool and skills catalog tool wired into the Google ADK agent, enabling ad-hoc data queries and skill execution from within a conversation (completed 2026-05-31)
- [x] **Phase 45: BFF Integration** - BFF routes that proxy `/bff/ai/*` requests to the AI service with session validation and screen context passthrough (completed 2026-06-01)
- [x] **Phase 46: Chat UI** - Vue 3 collapsible chat panel matching the Stitch design: message bubbles, expandable Thought/Actions/Result sections, live usage stats, and CTA skill buttons (completed 2026-06-01)

## Phase Details

### Phase 43: AI Service Foundation
**Goal**: A deployable Python microservice exists that accepts a chat message and returns a Gemini-powered agent response via Google ADK
**Depends on**: Phase 42 (v1.9 complete)
**Requirements**: SVC-01
**Success Criteria** (what must be TRUE):
  1. Running `docker-compose up ai-analyst` starts the service on a dedicated port with a `/health` endpoint returning 200
  2. Posting a plain text message to the `/chat` endpoint returns a structured agent response (at minimum: final answer text)
  3. The service uses the Gemini model via Google ADK orchestration — not a direct Gemini SDK call from a single function
  4. Agent configuration (model name, Gemini API key) is read from environment variables, not hardcoded
**Plans**: 2 plans

Plans:
- [x] 43-01-PLAN.md — ai-analyst/ service scaffold (pyproject.toml, Dockerfile, config.py, env template)
- [x] 43-02-PLAN.md — Agent + endpoints + docker-compose wiring (agent.py, main.py, SSE /chat)

### Phase 44: AI Analyst Skills
**Goal**: The agent can answer questions about dashboard data by running CubeJS queries, and can execute skills from a dynamically loaded catalog
**Depends on**: Phase 43
**Requirements**: SVC-02, SVC-03, AGENT-01, AGENT-02, AGENT-03
**Success Criteria** (what must be TRUE):
  1. Asking the agent "what were total sales last month?" causes it to invoke the CubeJS tool, execute a dimension/measure query, and return a data-grounded answer
  2. When the agent receives screen context (chart data), it can describe visible trends, peaks, or anomalies in plain language without executing an additional CubeJS query
  3. The skills catalog (catalog.yaml from github.com/ianache/skills-catalog) is fetched and parsed at service startup; available skill names are visible in agent tool descriptions
  4. Asking the agent to run a skill by name causes it to invoke the catalog tool and return the skill's execution result or a clear error if the skill is not found
**Plans**: 2 plans

Plans:
- [x] 44-01-PLAN.md — CubeJS Tool + Screen Context support
- [x] 44-02-PLAN.md — Skills Catalog Tool + Startup Fetch integration

### Phase 45: BFF Integration
**Goal**: The dashboard-app frontend can reach the AI service through the BFF with session validation; unauthenticated requests are rejected before touching the AI service
**Depends on**: Phase 44
**Requirements**: SVC-04
**Success Criteria** (what must be TRUE):
  1. A POST to `/bff/ai/chat` with a valid session cookie is forwarded to the AI service and returns its response; a request with no session cookie receives HTTP 401
  2. The BFF extracts the current user's session context and forwards it as a header or body field to the AI service with every request
  3. Screen context (JSON payload of visible chart data) sent by the frontend is passed through to the AI service without modification
**Plans**: 1 plan

Plans:
- [x] 45-01-PLAN.md — BFF Integration & Core Proxy Logic

### Phase 46: Chat UI
**Goal**: Dashboard designers can open a chat panel, ask questions about their dashboard, and interact with agent responses including skill CTAs — without leaving the designer
**Depends on**: Phase 45
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05
**Success Criteria** (what must be TRUE):
  1. User can open and close the AI Analyst panel via a button in the dashboard designer toolbar; the panel is collapsible and does not overlap the canvas when open
  2. Submitting a question in the chat input automatically captures the visible chart data from the current dashboard view and sends it as screen context with the request
  3. Agent responses render in message bubbles with three independently expandable sections: Thought Process, Actions Taken, and Final Result
  4. The panel header shows live usage stats that update after each response: input tokens, output tokens, cache hit %, and session cost
  5. When an agent response includes a recommended skill, a call-to-action button appears inside the message bubble; clicking it triggers that skill and shows the result inline
**Plans**: 3 plans

Plans:
- [x] 46-01-PLAN.md — Chat Logic & State Management
- [x] 46-02-PLAN.md — AI Analyst UI Components
- [ ] 46-03-PLAN.md — Gap closure: Actions Taken section, cache hit % stats, skill CTA buttons (CHAT-03, CHAT-04, CHAT-05)

### Phase 47: Multi System Design

**Goal:** Implementar un sistema de temas UI (claro/oscuro) con toggle en el menú lateral. El modo oscuro es el actual design system; el modo claro se basa en `design/DESIGN-light.md`. El tema persiste en localStorage y se aplica vía `data-theme` en el elemento raíz.
**Requirements**: design/DESIGN-light.md
**Depends on:** Phase 46
**Plans:** 1/1 plans complete

Plans:
- [ ] 47-01-PLAN.md — CSS light theme vars + uiStore theme state + SideMenu toggle icons

### Phase 48: Theme Alignment — fondos y colores de texto del menú lateral y páginas según System Design (light/dark)

**Goal:** Migrate all hardcoded colors in the shell layer, all in-scope views, and common components to CSS custom property tokens so the light/dark toggle transforms the entire product visually. Excludes FlowEditorView, IntegrationsView, and FlowEditorCanvas.
**Requirements**: THEME-01
**Depends on:** Phase 47
**Plans:** 4/4 plans complete

Plans:
- [ ] 48-01-PLAN.md — Shell components: SideMenu, TopBar, AppLayout (highest density migration)
- [ ] 48-02-PLAN.md — Heavy views: ConnectionsView, SettingsView, LoginView, DashboardDesignerView
- [ ] 48-03-PLAN.md — Remaining views (9 files) + PageHeader and ConfirmModal
- [ ] 48-04-PLAN.md — Verify and close 5 locked shared components (DashboardCard, KpiWidget, QuickActionCard, PanelHeadBodyPieComponent, MIcon)

### Phase 49: Diseño Minimalista Profesional @features/FEAT5.md

**Goal:** Rediseñar el Dashboard Studio para lograr un aspecto minimalista, profesional y moderno, empleando colores neutros e iconos de alta calidad, mientras se preserva la funcionalidad existente.
**Requirements**: THEME-01
**Depends on:** Phase 48
**Plans:** 3/4 plans executed

Plans:
- [x] 49-01-PLAN.md — Refactor DashboardDesignerView modals to Glassmorphism and Inter typography
- [x] 49-02-PLAN.md — Update global CSS tokens for minimalist shadows, borders, and outlined buttons
- [x] 49-03-PLAN.md — Migrate iconography to Lucide via MIcon adapter pattern
- [ ] 49-04-PLAN.md — Visual verification of minimalist aesthetic

### Phase 50: Add a new model based on DeepSeek to BI/AI Analyst in dashboard designer / viewer

**Goal:** Add DeepSeek V4 Flash and DeepSeek V4 Pro as selectable models alongside Gemini Flash in the BI Analyst chat panel. Includes a LiteLLM adapter (per-request agent factory), a GET /models endpoint, BYOK key storage via the existing LlmConfig infrastructure, and a gear-icon model selector with per-message model badges.
**Requirements**: DEEPSEEK-01, DEEPSEEK-02, DEEPSEEK-03, DEEPSEEK-04, DEEPSEEK-05, DEEPSEEK-06, DEEPSEEK-07
**Depends on:** Phase 49
**Plans:** 3/3 plans complete

Plans:
- [ ] 50-01-PLAN.md — ai-analyst service: LiteLLM install, create_runner() factory, /models endpoint, cost tracking
- [ ] 50-02-PLAN.md — SettingsView: add DeepSeek provider to llm.js PROVIDERS (BYOK key storage)
- [ ] 50-03-PLAN.md — Frontend: aiAnalyst store model state + AiAnalystPanel gear selector + AiAnalystMessage badges

### Phase 51: AI Analyst chat enhancements: dashboard filters, session history, context summarization

**Goal:** Improve BI AI Analyst usability: (1) pass active dashboard filters as context so the agent analyzes the same data the user sees, (2) maintain per-dashboard chat history within a session so users can ask follow-up questions, (3) auto-summarize chat history when it exceeds 200KB to prevent context window overflow.
**Requirements**: ANALYST-01, ANALYST-02, ANALYST-03
**Depends on:** Phase 50
**Plans:** 5/5 plans complete

Plans:
- [ ] 51-01-PLAN.md — Filter context: AiAnalystPanel resolvedFilters prop + aiAnalyst.js + cube.py merge + main.py ChatRequest (ANALYST-01)
- [ ] 51-02-PLAN.md — Per-dashboard sessions: aiAnalyst.js sessions map + backend get-or-create + stable session_id (ANALYST-02)
- [ ] 51-03-PLAN.md — Context summarization: 200KB size check + _summarize_session() + context_summarized SSE event (ANALYST-03)

### Phase 52: Mejorar nodo LLM Completion en Integration Flows para permitir interpolacion de variables desde ctx en los campos User Prompt y System Prompt similar al comportamiento del nodo Email en sus campos Subject y Body

**Goal:** Habilitar interpolacion Jinja2 en system_prompt del nodo LLM Completion y agregar hints visuales en ambos campos (user_prompt y system_prompt) en el editor de flujos — paridad con el nodo Email.
**Requirements**: none
**Depends on:** Phase 51
**Plans:** 1/1 plans complete

Plans:
- [ ] 52-01-PLAN.md — llm_executor.py system_prompt Jinja2 rendering + FlowEditorCanvas.vue LLM field hints

### Phase 53: panel de ejecucion por nodo en integration flows con ctx entrada salida y logs

**Goal:** Agregar un panel de inspeccion por nodo en el Flow Editor que muestre el ctx (entrada, salida) y logs de ejecucion de cada nodo. El panel se activa al hacer clic en un nodo ejecutado, usando datos ya capturados por el backend via WebSocket y BD sin cambios en backend.
**Requirements**: EXEC-INSPECTOR-01
**Depends on:** Phase 52
**Plans:** 2 plans

Plans:
- [ ] 53-01-PLAN.md — Create NodeInspectorPanel.vue dumb component (3 tabs, JSON display, variables table, export)
- [ ] 53-02-PLAN.md — Wire inspector into FlowEditorCanvas.vue (node_log capture, selectNode(), fec-right guard, human verify)

---

*For detailed milestone history, see .planning/milestones/*
*Last updated: 2026-06-06 after Phase 53 plans created*
