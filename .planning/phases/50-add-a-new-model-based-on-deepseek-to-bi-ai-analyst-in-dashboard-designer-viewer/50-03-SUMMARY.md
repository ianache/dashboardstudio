---
phase: 50-add-a-new-model-based-on-deepseek-to-bi-ai-analyst-in-dashboard-designer-viewer
plan: 03
subsystem: ui
tags: [vue3, pinia, ai-analyst, deepseek, cors, model-selector]

# Dependency graph
requires:
  - phase: 50-01
    provides: GET /bff/ai/models endpoint returning model list with enabled flags
  - phase: 50-02
    provides: LLM config UI (llmStore.keys.deepseek) and DeepSeek provider in backend settings

provides:
  - Gear icon + model dropdown in AiAnalystPanel header listing all available AI models
  - Model switching mid-conversation with divider row inserted in chat
  - Model badge on ALL assistant messages showing which model produced each response
  - selectedModel and availableModels state in aiAnalyst Pinia store
  - fetchModels() and switchModel() actions in aiAnalyst store
  - model and deepseek_api_key fields in POST /bff/ai/chat request body
  - X-Deepseek-Api-Key in BFF CORS allowedHeaders so browser preflight passes

affects:
  - ai-analyst service (receives model field in chat requests)
  - bff aiProxy (receives and forwards model/deepseek_api_key fields)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Dynamic import of useLlmStore inside Pinia actions to avoid circular dependencies
    - onMounted/onUnmounted pattern for document click listener cleanup in Vue components
    - Divider message object (role='divider') as a first-class message type in chat array

key-files:
  created: []
  modified:
    - dashboard-app/src/stores/aiAnalyst.js
    - dashboard-app/src/components/dashboard/AiAnalystPanel.vue
    - dashboard-app/src/components/dashboard/AiAnalystMessage.vue
    - bff/src/index.js

key-decisions:
  - "Model badge shown on ALL assistant messages (v-if='message.model') — not filtered to DeepSeek only. Each response is attributed regardless of provider."
  - "selectedModel not reset on clearMessages() — user model choice persists across conversation clears."
  - "Dynamic import('@/stores/llm') inside actions avoids potential circular dependency with top-level import."
  - "Divider message (role='divider') inserted in messages array on switchModel() when conversation exists — no new HTTP request triggered."

patterns-established:
  - "role='divider' is a valid message type in aiAnalyst.messages — AiAnalystMessage handles it with a full-width divider row."
  - "Model badges use var(--c-tertiary) with rgba border/background tint — established pattern for secondary metadata labels in AI panel."

requirements-completed:
  - DEEPSEEK-05
  - DEEPSEEK-06
  - DEEPSEEK-07

# Metrics
duration: 3min
completed: 2026-06-02
---

# Phase 50 Plan 03: Frontend Model Selector Summary

**Gear icon dropdown in AiAnalystPanel lets users switch AI models mid-conversation; model badges on every assistant response; DeepSeek CORS preflight fixed in BFF.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-02T03:51:36Z
- **Completed:** 2026-06-02T03:54:08Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- aiAnalyst Pinia store now tracks `selectedModel` (default Gemini Flash) and `availableModels`, with `fetchModels()` reading the saved DeepSeek key from llmStore and `switchModel()` inserting divider messages
- AiAnalystPanel header gains a gear icon that opens a model dropdown; models list with lock icons for disabled entries; fetchModels called on mount; click-outside listener cleaned up on unmount
- AiAnalystMessage renders divider rows for role='divider' messages and a model badge on every assistant message
- BFF CORS allowedHeaders includes X-Deepseek-Api-Key so browser preflight for fetchModels() passes when user has a saved key

## Task Commits

Each task was committed atomically:

1. **Task 1: Update aiAnalyst store** - `27089c4` (feat)
2. **Task 2: Gear icon + dropdown in AiAnalystPanel; divider + badge in AiAnalystMessage** - `a1d5f3f` (feat)
3. **Task 3: X-Deepseek-Api-Key to BFF CORS allowedHeaders** - `4074ff5` (feat)

## Files Created/Modified
- `dashboard-app/src/stores/aiAnalyst.js` - Added selectedModel, availableModels, fetchModels(), switchModel(); updated sendMessage() with model field and deepseek_api_key in POST body
- `dashboard-app/src/components/dashboard/AiAnalystPanel.vue` - Gear button + model dropdown + scoped CSS; onMounted fetchModels; onUnmounted click cleanup
- `dashboard-app/src/components/dashboard/AiAnalystMessage.vue` - Divider template branch; model badge on assistant messages; modelLabel() helper; scoped CSS for both
- `bff/src/index.js` - Added X-Deepseek-Api-Key to CORS allowedHeaders array

## Decisions Made
- Model badge shown for ALL assistant messages (including Gemini) — locked decision from plan spec. Each response is attributed to its model.
- selectedModel is not reset on clearMessages() — model choice should persist across conversation clears.
- Dynamic import of useLlmStore inside actions avoids top-level circular dependency risk.

## Deviations from Plan

None — plan executed exactly as written. One minor addition: added `ai-msg--divider` CSS class to the `.ai-msg` root div for divider messages (the plan only specified styles for the inner `.ai-switch-divider` element). This ensures the outer container does not apply flexbox alignment styles that would misrender the full-width divider.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required beyond what was established in plans 50-01 and 50-02.

## Next Phase Readiness
- Phase 50 (DeepSeek integration) is now fully complete: backend model routing (50-01), LLM config UI (50-02), and frontend model selector (50-03) are all shipped.
- The full end-to-end flow is ready: user saves DeepSeek API key in Settings, opens AI panel, selects DeepSeek model, sends a message — the BFF receives the model and key, forwards to ai-analyst service, response streams back with model badge shown.

---
*Phase: 50-add-a-new-model-based-on-deepseek-to-bi-ai-analyst-in-dashboard-designer-viewer*
*Completed: 2026-06-02*
