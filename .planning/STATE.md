---
gsd_state_version: 1.0
milestone: v1.9
milestone_name: Advanced Node Types
status: planning
last_updated: "2026-05-31T00:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State: Dashboard Studio v1.9

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-31)

**Core value:** Extender el editor de flujos con cinco nuevos tipos de nodo — transformación de datos, plantillas Nunjucks, LLM, modelos ML (Pickle), y lógica condicional
**Current focus:** Phase 38 — Data Transform Node (ready to plan)

## Current Position

Phase: 38 of 42 (Data Transform Node)
Plan: —
Status: Ready to plan
Last activity: 2026-05-31 — Roadmap created for v1.9

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- **Execution pattern split:** Data Transform, Templating, Conditional/Branch run purely in Deno. LLM and Pickle Model use Python pre-execution — credentials and ML libraries cannot be reached from Deno.
- **LLM API keys:** Must always live in encrypted LlmConfig DataSource. Never in node.props. node.props ends up in flow_nodes DB column and browser WebSocket frames.
- **Pickle isolation:** subprocess isolation is the primary mitigation; picklescan is supplementary. Verify subprocess coverage before Phase 41 planning.
- **Build order rationale:** Lowest blast radius first (38→39→40→41→42). Phase 42 last because it modifies the shared FlowConnection schema used by all existing flows.
- **fromHandle field:** New field on FlowConnection — absent means 'out' (backward-compatible). Conditional node writes true/false; runner routes only the matching branch.

### Research Flags (resolve before planning these phases)

- **Phase 41 (Pickle):** Verify subprocess isolation covers known picklescan bypass vectors before writing plans.
- **Phase 42 (Branch):** Confirm `fromHandle` does not collide with existing DSplit keyed output format in runner.ts.

### Blockers/Concerns

- None yet

## Session Continuity

Last session: 2026-05-31
Stopped at: Roadmap created — ready to plan Phase 38
Resume file: None
