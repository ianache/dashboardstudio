---
phase: 52-mejorar-nodo-llm-completion
plan: 01
subsystem: integrations
tags: [jinja2, llm, integration-flows, flow-editor, template-rendering]

# Dependency graph
requires:
  - phase: 51-ai-analyst-chat-enhancements
    provides: llm_executor.py baseline with user_prompt Jinja2 rendering
provides:
  - system_prompt Jinja2 rendering block in llm_executor.py
  - LLM field template hints in FlowEditorCanvas.vue for user_prompt and system_prompt

affects: [llm-executor, flow-editor-canvas, integration-flows]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "system_prompt_template variable naming convention for Jinja2-rendered fields"
    - "Self-contained rendering blocks (no shared helper) for system_prompt and user_prompt"
    - "Vue curly-brace escape pattern for literal {{ }} in template hints"

key-files:
  created: []
  modified:
    - backend/app/services/llm_executor.py
    - dashboard-app/src/components/editor/FlowEditorCanvas.vue

key-decisions:
  - "Two rendering blocks (1a for system_prompt, 1 for user_prompt) are intentionally self-contained — no shared helper extracted"
  - "LLM hint uses selectedNode.toolType === 'llm' condition so it only shows on LLM Completion nodes, not Email or other node types"
  - "Reused existing .fec-template-hint CSS class — no new styles added"

patterns-established:
  - "Jinja2 rendering pattern: rename variable to _template, try/except block with clear error message, use rendered_ prefix for output variable"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-06-05
---

# Phase 52 Plan 01: LLM Completion Jinja2 system_prompt + UI hints Summary

**system_prompt field in LLM Completion node now renders as Jinja2 template with ctx context, and both user_prompt and system_prompt fields show template hint in the Flow Editor UI**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-05T00:00:00Z
- **Completed:** 2026-06-05T00:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- system_prompt field now renders as Jinja2 template using the same `{payload, variables}` context as user_prompt
- Syntax errors in system_prompt return `{"success": false, "error": "Failed to render system prompt: ..."}` — no unhandled exception
- Missing variables (e.g. `{{ payload.nonexistent }}`) render as empty string — no error (default Jinja2 behavior)
- Template hint appears below both user_prompt and system_prompt textareas in the Flow Editor only for LLM Completion nodes
- Hint correctly absent from Email nodes and all other node types

## Task Commits

Each task was committed atomically:

1. **Task 1: Add system_prompt Jinja2 rendering to llm_executor.py** - `819d9bc` (feat)
2. **Task 2: Add Jinja2 template hints to LLM fields in FlowEditorCanvas.vue** - `526dbe9` (feat)

## Files Created/Modified
- `backend/app/services/llm_executor.py` - Renamed `system_prompt` to `system_prompt_template`, added rendering block 1a, updated messages array to use `rendered_system_prompt`
- `dashboard-app/src/components/editor/FlowEditorCanvas.vue` - Added `<p v-if>` hint element for LLM Completion node fields

## Decisions Made
- Two rendering blocks kept intentionally self-contained (not extracted to a shared helper) — plan specified this explicitly to avoid over-engineering
- LLM hint scoped to `selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)` so it does not pollute other node types
- Reused `.fec-template-hint` CSS class already defined in the file — no new CSS added

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- LLM Completion node now fully supports dynamic system prompts via Jinja2 templates
- Users can reference `{{ variables.nombre }}`, `{{ payload.campo }}`, and Jinja2 filters like `| tojson` in both prompt fields
- No blockers for subsequent phases

---
*Phase: 52-mejorar-nodo-llm-completion*
*Completed: 2026-06-05*
