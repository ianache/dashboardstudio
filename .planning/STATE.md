---
gsd_state_version: 1.0
milestone: v1.9
milestone_name: Advanced Node Types
status: planning
last_updated: "2026-05-31T00:00:00.000Z"
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State: Dashboard Studio v1.9

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-31)

**Core value:** Extender el editor de flujos con nodos avanzados — condicionales, transformación, plantillas, LLM, y modelos ML
**Current focus:** Not started — defining requirements

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-05-31 — Milestone v1.9 started

## Accumulated Context

### Decisions

- **v1.8 stack:** Express 5 + openid-client v6 (NOT keycloak-connect — maintenance mode). openid-client v6 is a complete API rewrite from v5; do not follow v5 tutorials.
- **Session store:** Redis via connect-redis.
- **CORS ownership:** BFF is the sole CORS handler. FastAPI CORSMiddleware removed.
- **Auth model:** Browser uses HttpOnly cookie session, never sees tokens directly.
- **Execution history:** Already fully implemented in v1.8 (ExecutionHistoryModal + ExecutionHistoryPanel wired in IntegrationsView).

### v1.9 Architecture Notes

- **Conditional/Branch node:** Requires dual output handles on canvas (true/false). Only one branch executes per run.
- **LLM node:** Uses OpenAI-compatible endpoint. New "LLM" connection type needed in DataSource. Executor runs in Python backend (not Deno) since it needs HTTP client + API key from encrypted Connection.
- **Pickle Model node:** File upload endpoint needed. Models stored server-side. Backend runs predict() via joblib/pickle.

### Blockers/Concerns

- None yet

### Session Continuity

Last session: 2026-05-31
Stopped at: Starting milestone v1.9 definition
Resume file: None
