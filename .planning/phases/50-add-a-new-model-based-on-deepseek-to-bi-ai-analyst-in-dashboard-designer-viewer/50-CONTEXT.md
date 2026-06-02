# Phase 50: DeepSeek Model Integration - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Add DeepSeek models (DeepSeek V4 Flash and DeepSeek V4 Pro) as selectable options alongside Gemini in the BI Analyst chat panel, available in both the Dashboard Designer and Dashboard Viewer. Includes:
- UI model selector (gear menu in AiAnalystPanel)
- Backend LiteLLM adapter to make Google ADK model-agnostic
- BYOK: user-managed DeepSeek API key stored in SettingsView
- Per-model cost tracking using provider-specific pricing

**Out of scope:** Replacing Google ADK framework, adding other LLM providers, admin-level model management UI, or making Gemini key user-provided.

</domain>

<decisions>
## Implementation Decisions

### Model selector UI
- Located behind the **gear/settings icon** in AiAnalystPanel header — keeps the chat header clean
- Shows all available models fetched from the new `/models` endpoint
- Friendly display names: "Gemini Flash", "DeepSeek V4 Flash", "DeepSeek V4 Pro"
- **Default model:** Gemini Flash (backward compatible — existing behavior unchanged)

### Mid-conversation model switching
- History is **kept** when switching models — the conversation continues with the new model
- A small visual **divider** with the model name is inserted in the chat to mark the switch point

### Message model badge
- Each **assistant message** shows a small badge indicating which model produced it (e.g., "Gemini Flash" / "DeepSeek V4 Flash")
- Badge is shown for ALL assistant messages including Gemini — allows users to compare responses from different models in the same conversation

### DeepSeek models exposed
- **DeepSeek V4 Flash** (`deepseek-v4-flash` via LiteLLM string `deepseek/deepseek-v4-flash`) — fast, strong at code and data analysis, BI chat primary use
- **DeepSeek V4 Pro** (`deepseek-v4-pro` via LiteLLM string `deepseek/deepseek-v4-pro`) — chain-of-thought reasoning, slower, for complex multi-step analysis
- Both exposed in the selector alongside Gemini Flash
- NOTE: The older V3/R1 alias names (`deepseek-chat` / `deepseek-reasoner`) are deprecated and hard-removed by DeepSeek on July 24, 2026. V4 Flash and V4 Pro are the current canonical model names.

### Backend integration — LiteLLM adapter
- Add **LiteLLM** as a dependency in `pyproject.toml`
- Use LiteLLM as the model backend for Google ADK — ADK supports LiteLLM natively
- DeepSeek accessed via LiteLLM using its OpenAI-compatible API (`deepseek/deepseek-v4-flash`, `deepseek/deepseek-v4-pro`)
- **No pre-built agent instances per model** — agent is constructed per-request with the selected model string; keeps the service stateless

### /models endpoint
- New endpoint in the ai-analyst FastAPI service: `GET /models`
- Returns list of available models (name, label, provider) driven by which API keys are configured
- Frontend `AiAnalystPanel` fetches this on panel open to populate the selector
- Enables adding/removing models without frontend deploys

### Model parameter on requests
- `/bff/ai/chat` request body includes a `model` field alongside the existing `message` + `context`
- BFF forwards `model` to ai-analyst
- ai-analyst routes to the correct LiteLLM backend based on `model`

### BYOK — DeepSeek API key
- User enters their personal DeepSeek API key in **SettingsView** (new "AI Models" section)
- Key stored encrypted in the backend using the existing `encryption.py` Fernet pattern (same as DataSource credentials)
- Stored per-user in the DB (new `user_ai_keys` table or extended user model)
- Key sent to ai-analyst as a request header or body field on each `/bff/ai/chat` call
- If no DeepSeek key is set: DeepSeek models appear greyed out in the selector with "Add API key in Settings"

### Cost tracking
- Backend calculates cost per provider using published per-token rates
- DeepSeek pricing applied when a DeepSeek model is active
- The existing `usage` display in AiAnalystPanel (tokens + cost) continues to work — just reflects correct numbers for the active model
- No separate cost display for BYOK vs org-key — cost is always shown

### Claude's Discretion
- Exact DB schema for storing user AI keys (extend existing User model or separate table)
- Exact pricing constants for DeepSeek V4 Flash and V4 Pro (use published API pricing at implementation time)
- LiteLLM version pin and any config options needed for the DeepSeek provider
- Design of the "AI Models" section in SettingsView (layout, input field style)
- Whether the model divider in chat is a horizontal line, a label, or a chip

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ai-analyst/app/core/config.py` — `Settings` class with `gemini_model` env var and `@lru_cache get_settings()`. New `deepseek_api_key` field follows the same pattern.
- `backend/app/core/encryption.py` — `process_sensitive_fields()` Fernet encryption. Use to encrypt/decrypt user DeepSeek keys before storing in DB.
- `backend/app/models/models.py` — SQLAlchemy models in `biportal` schema. Extend here for user AI keys.
- `dashboard-app/src/stores/aiAnalyst.js` — `usage` state (`input_tokens`, `output_tokens`, `cost`, `cache_hit`), `sendMessage()` POSTs to `/bff/ai/chat`. Add `model` field to the request body. Add `selectedModel` to state.
- `AiAnalystPanel.vue` + `AiAnalystMessage.vue` — existing chat UI. Gear icon + model selector goes in panel header. Badge goes in `AiAnalystMessage.vue`.

### Established Patterns
- `agent.py` — `LlmAgent(model=settings.gemini_model, ...)` — model is just a string; LiteLLM model strings follow `provider/model-name` convention.
- DataSource credential storage pattern — `process_sensitive_fields(data, "encrypt")` before save, decrypt on read. Same pattern for DeepSeek keys.
- Stream event types in `aiAnalyst.js` (`thought`, `answer`, `usage`, `done`) — the `usage` event already carries per-request cost; just update backend calculation.

### Integration Points
- `bff/` — AI proxy routes (`/bff/ai/chat`, `/bff/ai/skill`). Add `/bff/ai/models` to proxy the new ai-analyst `/models` endpoint. Add `model` field forwarding.
- `ai-analyst/app/main.py` — FastAPI app. Add `GET /models` route here.
- `backend/app/api/endpoints/` — Add user AI key CRUD endpoint (save/delete DeepSeek key). Called from SettingsView.
- `SettingsView.vue` — Add "AI Models" section with DeepSeek key input field.

</code_context>

<specifics>
## Specific Ideas

- DeepSeek V4 Flash and V4 Pro should both be available — the user explicitly wants both in the selector
- Gemini Flash stays the default; no regression for existing users
- The `/models` endpoint is driven by config — if `DEEPSEEK_API_KEY` is set (or user has BYOK key), DeepSeek models appear enabled
- When no DeepSeek key is set, models show as disabled with a "Add key in Settings" tooltip — don't hide them, just grey them out so users know they exist
- Cost calculation uses DeepSeek's published per-token pricing at implementation time

</specifics>

<deferred>
## Deferred Ideas

- Making Gemini key user-provided (BYOK for Gemini) — separate phase
- Admin-level model management (enable/disable models per org) — separate phase
- Adding other LLM providers (OpenAI, Anthropic, Mistral) — separate phase once LiteLLM adapter is in place
- Model performance comparison view — separate phase

</deferred>

---

*Phase: 50-add-a-new-model-based-on-deepseek-to-bi-ai-analyst-in-dashboard-designer-viewer*
*Context gathered: 2026-06-01*
*Context revised: 2026-06-01 — Updated model names from V3/R1 aliases (deepseek-chat, deepseek-reasoner) to canonical V4 names (DeepSeek V4 Flash, DeepSeek V4 Pro). The old aliases are deprecated and hard-removed by DeepSeek on July 24, 2026.*
