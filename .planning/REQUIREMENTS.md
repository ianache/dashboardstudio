# Requirements: Dashboard Studio v2.0 — BI Analyst

**Defined:** 2026-05-31
**Core Value:** Agente BI interactivo que lee el contexto del dashboard, ejecuta consultas analíticas y dispara skills operativas — sin salir de la interfaz del diseñador

## v2.0 Requirements (Etapa 1 — Base Agent)

### Chat Interface

- [ ] **CHAT-01**: User can open and close an AI Analyst panel from the dashboard designer
- [ ] **CHAT-02**: User can submit a natural language question; the panel captures the current screen context (visible chart data) automatically with each request
- [ ] **CHAT-03**: Agent responses display in message bubbles with three expandable sections: Thought Process, Actions Taken, Final Result
- [ ] **CHAT-04**: Panel header shows live usage stats: input tokens, output tokens, cache hit %, and session cost
- [ ] **CHAT-05**: User can trigger an agent-recommended skill via a call-to-action button embedded in the response

### Agent Capabilities

- [x] **AGENT-01**: Agent can interpret visible dashboard chart data and explain trends, peaks, or anomalies in plain language
- [x] **AGENT-02**: Agent can execute ad-hoc CubeJS queries to explore data beyond what is currently displayed on screen
- [ ] **AGENT-03**: Agent can trigger pre-configured skills from the skills catalog (catalog.yaml) on user request or agent recommendation

### AI Service

- [x] **SVC-01**: A dedicated Python microservice uses Google ADK to orchestrate the agent workflow with Gemini models via native API
- [x] **SVC-02**: The AI service integrates CubeJS as an agent tool — executes dimension/measure queries and returns structured results to the agent
- [ ] **SVC-03**: The AI service loads the skills catalog (catalog.yaml) dynamically at startup to discover available actions
- [ ] **SVC-04**: All AI requests are proxied through the BFF for session validation before reaching the AI service

## v2.1 Requirements (Etapa 2 — Advanced Agent)

Deferred to next milestone.

### Semantic Reasoning

- **ONTO-01**: Agent integrates kmportal ontology engine to understand business metric semantics
- **ONTO-02**: Agent can validate business rules using ontology constraints before responding
- **ONTO-03**: Agent performs root cause analysis by traversing the business knowledge graph

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice/audio playback | UI nicety shown in Stitch design but not in PRD Etapa 1 |
| Conversation history persistence | Adds DB schema complexity — defer to v2.1 |
| Multi-agent orchestration | Etapa 1 is single-agent; multi-agent is Etapa 2+ |
| Table browser side panel (plans/FEAT04) | Separate feature, not part of BI Analyst agent scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SVC-01 | Phase 43 | Complete |
| SVC-02 | Phase 44 | Complete |
| SVC-03 | Phase 44 | Pending |
| AGENT-01 | Phase 44 | Complete |
| AGENT-02 | Phase 44 | Complete |
| AGENT-03 | Phase 44 | Pending |
| SVC-04 | Phase 45 | Pending |
| CHAT-01 | Phase 46 | Pending |
| CHAT-02 | Phase 46 | Pending |
| CHAT-03 | Phase 46 | Pending |
| CHAT-04 | Phase 46 | Pending |
| CHAT-05 | Phase 46 | Pending |

**Coverage:**
- v2.0 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-31*
*Last updated: 2026-05-31 after roadmap creation (traceability complete)*
