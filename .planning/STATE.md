---
gsd_state_version: 1.0
milestone: v1.8
milestone_name: BFF Service Architecture
current_phase: 33
current_plan: Not started
status: ready_to_plan
last_updated: "2026-05-28T00:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State: Dashboard Studio v1.8

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-28)

**Core value:** BFF concentra auth y session management, expone API unificada al frontend — el browser nunca ve tokens
**Current focus:** Phase 33 — BFF Foundation (ready to plan)

## Current Position

Phase: 33 of 37 (BFF Foundation)
Plan: Not started
Status: Ready to plan
Last activity: 2026-05-28 — Roadmap created for v1.8 BFF Service Architecture (phases 33-37)

Progress: [░░░░░░░░░░] 0% (0/5 phases complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 0 (this milestone)
- Prior milestone avg: ~3 plans/phase

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 33-37 | TBD | - | - |

## Accumulated Context

### Decisions

- **v1.8 stack:** Express 5 + openid-client v6 (NOT keycloak-connect — maintenance mode). openid-client v6 is a complete API rewrite from v5; do not follow v5 tutorials.
- **Session store:** PostgreSQL via connect-pg-simple (reuses existing DB; Redis deferred to scaling phase).
- **Build order:** Phase 33 (scaffold) → 34 (auth) → 35 (FastAPI proxy) → 36 (CubeJS proxy) → 37 (FE migration). Order is non-negotiable; 37 is a one-way door.
- **CORS ownership:** BFF is the sole CORS handler. FastAPI CORSMiddleware must be removed in Phase 35.

### Blockers/Concerns

- **Phase 34 prerequisite:** Keycloak confidential client `dashboard-bff` must be registered in Keycloak admin console at `oauth2.qa.comsatel.com.pe` with correct callback URI and PKCE settings before Phase 34 begins. Cannot be automated.
- **Phase 36 research flag:** Whether the running CubeJS deployment uses `queryRewrite` is unknown. Inspect CubeJS schema files before starting Phase 36; scope may expand.
- **Phase 37 is irreversible:** Frontend migration removes keycloak-js atomically. All BFF phases (33-36) must be end-to-end verified before starting Phase 37.

### Session Continuity

Last session: 2026-05-28
Stopped at: Roadmap written — 5 phases defined, 18 requirements mapped, files written
Resume file: None
