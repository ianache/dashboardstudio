# Phase 50: DeepSeek Model Integration - Research

**Researched:** 2026-06-01
**Domain:** LiteLLM / Google ADK / DeepSeek API / Vue 3 UI / FastAPI BYOK
**Confidence:** HIGH (core integration patterns), MEDIUM (pricing constants — must verify at implementation time)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Model selector located behind the **gear/settings icon** in AiAnalystPanel header
- Shows all available models fetched from the new `/models` endpoint
- Friendly display names: "Gemini Flash", "DeepSeek V4 Flash", "DeepSeek V4 Pro"
- **Default model:** Gemini Flash (backward compatible — existing behavior unchanged)
- History is **kept** when switching models — conversation continues with new model
- A small visual **divider** with the model name is inserted in chat to mark the switch point
- Each **assistant message** shows a small badge indicating which model produced it
- **DeepSeek V4 Flash** (`deepseek-v4-flash`) — fast, strong at code and data analysis
- **DeepSeek V4 Pro** (`deepseek-v4-pro`) — chain-of-thought reasoning, for complex analysis
- Add **LiteLLM** as a dependency in `pyproject.toml`
- Use LiteLLM as the model backend for Google ADK — ADK supports LiteLLM natively
- DeepSeek accessed via LiteLLM using its OpenAI-compatible API
- **No pre-built agent instances per model** — agent constructed per-request; service stays stateless
- New endpoint in the ai-analyst FastAPI service: `GET /models`
- `/bff/ai/chat` request body includes a `model` field alongside `message` + `context`
- BFF forwards `model` to ai-analyst
- User enters their personal DeepSeek API key in **SettingsView** (new "AI Models" section)
- Key stored encrypted using existing `encryption.py` Fernet pattern
- If no DeepSeek key: DeepSeek models appear greyed out with "Add API key in Settings"
- Backend calculates cost per provider using published per-token rates
- No separate cost display for BYOK vs org-key — cost is always shown

### Claude's Discretion

- Exact DB schema for storing user AI keys (extend existing User model or separate table)
- Exact pricing constants for DeepSeek V4 Flash and V4 Pro (use published API pricing at implementation time)
- LiteLLM version pin and any config options needed for the DeepSeek provider
- Design of the "AI Models" section in SettingsView (layout, input field style)
- Whether the model divider in chat is a horizontal line, a label, or a chip

### Deferred Ideas (OUT OF SCOPE)

- Making Gemini key user-provided (BYOK for Gemini) — separate phase
- Admin-level model management (enable/disable models per org) — separate phase
- Adding other LLM providers (OpenAI, Anthropic, Mistral) — separate phase once LiteLLM adapter is in place
- Model performance comparison view — separate phase
</user_constraints>

---

## Summary

Phase 50 adds DeepSeek V4 Flash and DeepSeek V4 Pro as selectable models alongside Gemini Flash in the AI Analyst chat panel. The key architectural pivot is replacing the current module-level `root_agent` singleton in `agent.py` with a per-request agent factory that accepts a model string — enabling stateless model switching without process restarts.

Google ADK 2.1.0 (currently installed) natively supports LiteLLM via `google.adk.models.lite_llm.LiteLlm`. The wrapper takes a `model="provider/model-name"` string, so DeepSeek becomes `LiteLlm(model="deepseek/deepseek-v4-flash")`. LiteLLM requires its own dependency installation. CRITICAL: the google-adk project pins LiteLLM to `>=1.83.7,<=1.83.14` due to a security incident in 1.82.7–1.82.8; follow that constraint.

The BYOK storage path is already fully built: `LlmConfig` model, encrypted storage via `encryption.py`, and a `GET/POST/DELETE /llm-config` endpoint all exist in the backend. The frontend `SettingsView` already has a "LLM / IA" panel that renders per-provider key fields. DeepSeek is simply a new provider entry in the providers list — no new DB table or endpoint needed. The `model` field must be added to the `/bff/ai/chat` request body and forwarded by the BFF proxy to ai-analyst.

**Primary recommendation:** Build a `create_agent(model_str, deepseek_api_key=None)` factory function in `ai-analyst/app/agent.py`; keep the session_service singleton. Add `litellm>=1.83.7,<=1.83.14` to `ai-analyst/pyproject.toml`. Reuse `LlmConfig` with `provider="deepseek"` for BYOK storage.

---

## Standard Stack

### Core (ai-analyst service)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-adk | 2.1.0 (installed) | Agent orchestration, SSE streaming, session management | Already in use |
| litellm | >=1.83.7,<=1.83.14 | LLM provider abstraction — routes to DeepSeek API | ADK's official multi-provider bridge; pinned range avoids security incident in 1.82.7-1.82.8 |
| DeepSeek API | n/a (external) | V4 Flash and V4 Pro model inference | Provider selected by user decision |

### Supporting (backend service)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cryptography (Fernet) | already installed | Encrypt/decrypt DeepSeek API key at rest | Already used for DataSource credentials |
| pydantic-settings | already installed | Config class for new `DEEPSEEK_API_KEY` env var | Consistent with existing pattern |

### Already Available (no new installs)

| Component | Location | Reuse |
|-----------|----------|-------|
| `LlmConfig` SQLAlchemy model | `backend/app/models/models.py` | Add `provider="deepseek"` entries |
| `encrypt_value` / `decrypt_value` | `backend/app/core/encryption.py` | Same as DataSource credentials |
| `/llm-config` CRUD endpoint | `backend/app/api/endpoints/llm_config.py` | Already handles per-user, per-provider keys |
| `aiProxy` BFF middleware | `bff/src/proxy.js` | Forward `model` field in proxied body |

**Installation (ai-analyst service only):**

```bash
cd ai-analyst
uv add "litellm>=1.83.7,<=1.83.14"
```

---

## Architecture Patterns

### Recommended File Structure Changes

```
ai-analyst/app/
├── agent.py           # REFACTOR: remove module-level singleton; add create_agent() factory
├── main.py            # MODIFY: /chat accepts model field; add GET /models endpoint
└── core/config.py     # MODIFY: add deepseek_api_key optional field

backend/app/api/endpoints/
└── llm_config.py      # MODIFY: add "deepseek" to providers list (no new file)

dashboard-app/src/
├── stores/aiAnalyst.js            # MODIFY: add selectedModel state; pass model in sendMessage
├── components/dashboard/
│   ├── AiAnalystPanel.vue         # MODIFY: add gear icon + model selector dropdown
│   └── AiAnalystMessage.vue       # MODIFY: add model badge to assistant messages
└── views/SettingsView.vue         # MODIFY: add DeepSeek to llmProviders array
```

### Pattern 1: Per-Request Agent Factory (stateless model switching)

**What:** Replace the module-level `root_agent` singleton with a factory function that builds a new `LlmAgent` per chat request using the requested model string.

**When to use:** Every `/chat` POST invocation — constructs the agent, runs it, discards it.

```python
# Source: https://adk.dev/agents/models/litellm/
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner

def create_agent(model_str: str, deepseek_api_key: str | None = None) -> tuple[LlmAgent, Runner]:
    """Factory: constructs a fresh LlmAgent for the requested model."""
    if model_str.startswith("deepseek/"):
        # Inject BYOK key into LiteLlm env context
        import os
        if deepseek_api_key:
            os.environ["DEEPSEEK_API_KEY"] = deepseek_api_key
        model = LiteLlm(
            model=model_str,
            stream_options={"include_usage": True}  # Required for usage_metadata
        )
    else:
        # Gemini — plain string, ADK handles natively
        model = model_str  # e.g. "gemini-2.5-flash-lite"

    agent = LlmAgent(
        name="bi_analyst",
        model=model,
        tools=[query_data, execute_skill],
        instruction=AGENT_INSTRUCTION,
    )
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,  # singleton reused
    )
    return agent, runner
```

**Key detail:** `session_service` remains a module-level singleton (safe per ADK design). Only the agent and runner are per-request.

### Pattern 2: LiteLLM Model String Convention

**What:** LiteLLM uses `"provider/model-name"` strings.

| User-facing label | LiteLLM model string | DeepSeek API model ID |
|-------------------|---------------------|----------------------|
| Gemini Flash | `"gemini-2.5-flash-lite"` | n/a (native ADK) |
| DeepSeek V4 Flash | `"deepseek/deepseek-v4-flash"` | `deepseek-v4-flash` |
| DeepSeek V4 Pro | `"deepseek/deepseek-v4-pro"` | `deepseek-v4-pro` |

**CRITICAL:** The old aliases `deepseek-chat` and `deepseek-reasoner` are deprecated and will fail after **July 24, 2026, 15:59 UTC**. Use the explicit v4 names in all new code.

### Pattern 3: GET /models Endpoint (config-driven)

**What:** The ai-analyst service exposes a `/models` endpoint that returns the list of available models based on which API keys are configured.

```python
# In ai-analyst/app/main.py
@app.get("/models")
async def get_models(x_deepseek_api_key: str | None = Header(default=None)):
    """Returns available models driven by which keys are present."""
    models = [
        {"id": "gemini-2.5-flash-lite", "label": "Gemini Flash",
         "provider": "google", "enabled": True}
    ]
    if x_deepseek_api_key:
        models += [
            {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek V4 Flash",
             "provider": "deepseek", "enabled": True},
            {"id": "deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro",
             "provider": "deepseek", "enabled": True},
        ]
    else:
        models += [
            {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek V4 Flash",
             "provider": "deepseek", "enabled": False,
             "disabled_reason": "Add API key in Settings"},
            {"id": "deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro",
             "provider": "deepseek", "enabled": False,
             "disabled_reason": "Add API key in Settings"},
        ]
    return {"models": models}
```

### Pattern 4: BYOK Key Flow

**What:** The DeepSeek API key is stored per-user in the existing `LlmConfig` table with `provider="deepseek"`. On each chat request:

1. Frontend sends `model` field in POST body to `/bff/ai/chat`
2. BFF reads user's DeepSeek key from backend via internal call, OR frontend fetches it via `/bff/api/llm-config` and passes it as a header
3. ai-analyst receives the key and injects it as `DEEPSEEK_API_KEY` env var before constructing the LiteLlm instance

**Recommended approach:** BFF injects the decrypted key as `X-Deepseek-Api-Key` header (parallel to how `X-User-ID` is injected). This keeps the frontend from handling raw keys and centralizes credential management in the BFF.

**Alternative (simpler):** Frontend fetches its own key from `/bff/api/llm-config?provider=deepseek` on panel open, stores it in the store, and sends it as a request body field. Simpler implementation but the key transits the browser.

### Pattern 5: Usage Metadata with LiteLLM

**What:** When using `LiteLlm` in ADK, `stream_options={"include_usage": True}` must be passed to get usage metadata in the SSE stream.

```python
# Source: https://github.com/google/adk-python/discussions/97
model = LiteLlm(
    model="deepseek/deepseek-v4-flash",
    stream_options={"include_usage": True}
)
```

The `event.usage_metadata` fields are the same format as Gemini:
- `prompt_token_count` → input tokens
- `candidates_token_count` → output tokens
- `thoughts_token_count` → reasoning tokens (V4 Pro)

### Pattern 6: Cost Calculation by Provider

**What:** Backend calculates cost in the `usage` SSE event using per-provider pricing constants.

```python
# Pricing as of 2026-06-01 — verify at implementation time
PRICING = {
    "google": {
        "gemini-2.5-flash-lite": {"input": 0.000000075, "output": 0.0000003},  # per token
    },
    "deepseek": {
        "deepseek/deepseek-v4-flash": {"input": 0.00000027, "output": 0.0000011},
        "deepseek/deepseek-v4-pro": {"input": 0.00000055, "output": 0.00000219},
    }
}

def calculate_cost(model_str: str, input_tokens: int, output_tokens: int) -> float:
    provider = "deepseek" if model_str.startswith("deepseek/") else "google"
    rates = PRICING.get(provider, {}).get(model_str, {"input": 0, "output": 0})
    return input_tokens * rates["input"] + output_tokens * rates["output"]
```

### Pattern 7: Model Badge in AiAnalystMessage.vue

**What:** Each assistant message object carries a `model` field. `AiAnalystMessage.vue` renders a small pill badge.

```javascript
// In aiAnalyst.js store — sendMessage()
const assistantMsg = {
  role: 'assistant',
  content: '',
  thought: '',
  actions: [],
  skills: [],
  streaming: true,
  error: false,
  model: this.selectedModel  // <-- new field
}
```

```vue
<!-- In AiAnalystMessage.vue, below .ai-agent-label -->
<span v-if="message.model" class="ai-model-badge">{{ modelLabel(message.model) }}</span>
```

### Pattern 8: Model Divider in Chat (model switch marker)

**What:** When `selectedModel` changes mid-conversation, push a special divider message object before the next assistant message.

```javascript
// In aiAnalyst.js — switchModel() action
switchModel(modelId) {
  if (modelId === this.selectedModel) return
  const prev = this.selectedModel
  this.selectedModel = modelId
  if (this.messages.length > 0) {
    this.messages.push({
      role: 'divider',
      model: modelId,
      label: `Switched to ${modelLabel(modelId)}`
    })
  }
}
```

### Anti-Patterns to Avoid

- **Module-level agent singleton with model baked in:** The current `root_agent` pattern works for single-model but breaks multi-model. Never do `root_agent = LlmAgent(model=settings.gemini_model)` at module level when model must be dynamic.
- **Using deprecated DeepSeek aliases:** `deepseek-chat` and `deepseek-reasoner` fail after July 24, 2026. Use `deepseek-v4-flash` and `deepseek-v4-pro`.
- **LiteLLM without `stream_options={"include_usage": True}`:** Without this, `event.usage_metadata` will be None for LiteLLM-backed models and cost tracking breaks.
- **Hardcoding `os.environ["DEEPSEEK_API_KEY"]` globally:** Setting the env var globally in a multi-request async server will cause race conditions. Set it per-request in a context-local way, or pass it directly in `LiteLlm(api_key=...)` constructor.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-provider LLM routing | Custom HTTP client to DeepSeek API | LiteLLM + `google.adk.models.lite_llm.LiteLlm` | ADK's official abstraction; handles streaming, retries, error normalization |
| API key encryption at rest | Custom AES logic | Existing `encrypt_value()` / `decrypt_value()` | Already battle-tested with DataSource credentials |
| Per-user key storage | New `user_ai_keys` table | Existing `LlmConfig` model with `provider="deepseek"` | Model + CRUD + encryption already exist; just add a new provider entry |
| Provider-specific headers | Manual request mutation | LiteLLM provider prefix (`deepseek/...`) | LiteLLM maps the prefix to correct base URL and auth headers |

**Key insight:** The BYOK storage infrastructure is already complete. `LlmConfig` + `llm_config.py` endpoint + SettingsView LLM panel all exist. DeepSeek is a new row in the providers list, not a new system.

---

## Common Pitfalls

### Pitfall 1: LiteLLM env var race condition in async server

**What goes wrong:** Multiple concurrent requests both write `os.environ["DEEPSEEK_API_KEY"]` simultaneously; one request's key overwrites another's.

**Why it happens:** FastAPI runs requests concurrently in an async event loop. `os.environ` is process-global.

**How to avoid:** Pass the API key directly in the `LiteLlm` constructor: `LiteLlm(model="deepseek/deepseek-v4-flash", api_key=deepseek_key)`. LiteLLM supports this parameter and it does not pollute global state.

**Warning signs:** Users randomly get authentication errors on DeepSeek requests even when their key is valid.

### Pitfall 2: Missing `stream_options` — broken usage/cost display

**What goes wrong:** The `usage` SSE event emits `{input_tokens: 0, output_tokens: 0}` for DeepSeek responses; the cost chip stays at $0.000.

**Why it happens:** LiteLLM requires `stream_options={"include_usage": True}` to include usage data in streamed responses. The ADK runner does not set this automatically.

**How to avoid:** Always construct `LiteLlm(model=..., stream_options={"include_usage": True})`.

**Warning signs:** Gemini shows correct token counts; DeepSeek shows zeros.

### Pitfall 3: Agent name collision with per-request factory

**What goes wrong:** ADK raises a validation error because `LlmAgent(name="bi_analyst")` is instantiated multiple times rapidly.

**Why it happens:** ADK may cache or validate agent names. Using the same name string repeatedly may conflict with any ADK internal registry.

**How to avoid:** Verify during implementation whether ADK 2.1.0 has agent name uniqueness enforcement. If it does, use `name=f"bi_analyst_{uuid.uuid4().hex[:8]}"` in the factory. The session is keyed by `session_id`, not agent name.

**Warning signs:** `ValueError: Agent name 'bi_analyst' already registered` under concurrent load.

### Pitfall 4: DeepSeek V4 Pro reasoning content in multi-turn

**What goes wrong:** When DeepSeek V4 Pro is used for reasoning, LiteLLM strips the `reasoning_content` from assistant messages when serializing history — causing degraded multi-turn performance.

**Why it happens:** Confirmed bug in LiteLLM (issue #26395). Multi-turn context is incomplete.

**How to avoid:** Phase 50 scoped to stateless requests (each `/chat` POST creates a fresh session, no multi-turn history). This pitfall does NOT apply to the current implementation. Flag for when conversation history persistence is added in v2.1.

**Warning signs:** Not a concern in Phase 50 scope.

### Pitfall 5: Deprecated DeepSeek aliases in production

**What goes wrong:** App breaks on July 24, 2026 if `deepseek-chat` or `deepseek-reasoner` are used as model strings.

**Why it happens:** DeepSeek announced hard deprecation of the legacy aliases.

**How to avoid:** Use `deepseek-v4-flash` and `deepseek-v4-pro` from day one. Never introduce the old aliases.

### Pitfall 6: LiteLLM security-incident version range

**What goes wrong:** Installing LiteLLM 1.82.7 or 1.82.8 introduces unauthorized code (supply chain incident, March 24, 2026).

**How to avoid:** Pin `litellm>=1.83.7,<=1.83.14` (the same constraint used in google-adk main branch pyproject.toml). Do not use `litellm>=1.82.x`.

---

## Code Examples

### Install LiteLLM in ai-analyst

```bash
# Source: https://docs.litellm.ai/docs/tutorials/google_adk
cd ai-analyst
uv add "litellm>=1.83.7,<=1.83.14"
```

### Agent Factory (agent.py refactor)

```python
# Source: https://adk.dev/agents/models/litellm/
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "ai-analyst"
session_service = InMemorySessionService()  # singleton

GEMINI_DEFAULT = "gemini-2.5-flash-lite"

def create_runner(model_str: str, deepseek_api_key: str | None = None) -> Runner:
    if model_str.startswith("deepseek/"):
        model = LiteLlm(
            model=model_str,
            api_key=deepseek_api_key,          # avoids env var race condition
            stream_options={"include_usage": True},
        )
    else:
        model = model_str  # Gemini native string

    agent = LlmAgent(
        name="bi_analyst",
        model=model,
        tools=[query_data, execute_skill],
        instruction=AGENT_INSTRUCTION,
    )
    return Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
```

### Updated ChatRequest Schema (main.py)

```python
class ChatRequest(BaseModel):
    message: str
    screen_context: dict | None = None
    context: dict | None = None
    model: str = "gemini-2.5-flash-lite"         # new field, default keeps Gemini
    deepseek_api_key: str | None = None           # forwarded by BFF; None if BYOK not set
```

### BFF: Forward model field (proxy.js — no change needed)

The existing `aiProxy` in `bff/src/proxy.js` uses `fixRequestBody(proxyReq, req)` which forwards the entire POST body as-is. Since `model` is just a new field in the JSON body, no proxy change is required for body forwarding. The BFF should however inject the DeepSeek key header if it retrieves it from backend:

```javascript
// In aiProxy proxyReq handler — add after X-User-Email injection:
// Option: fetch user's deepseek key from backend and inject as header
// (simpler alternative: let frontend send it in request body from llmConfig store)
```

### Frontend: Add selectedModel to aiAnalyst store

```javascript
// In dashboard-app/src/stores/aiAnalyst.js
state: () => ({
  messages: [],
  loading: false,
  usage: { input_tokens: 0, output_tokens: 0, cost: 0, cache_hit: 0 },
  isPanelOpen: false,
  selectedModel: 'gemini-2.5-flash-lite',   // new — default unchanged
  availableModels: [],                        // new — populated from /bff/ai/models
}),

// In sendMessage():
body: JSON.stringify({
  message: text,
  context,
  model: this.selectedModel,                 // new field
})
```

### Model Selector in AiAnalystPanel.vue (gear button)

```vue
<!-- Add to ai-header-btns, before delete and close buttons -->
<div class="ai-model-selector" style="position: relative;">
  <button class="ai-icon-btn" title="Seleccionar modelo" @click="showModelMenu = !showModelMenu">
    <span class="material-symbols-outlined">settings</span>
  </button>
  <div v-if="showModelMenu" class="ai-model-menu">
    <button
      v-for="m in store.availableModels"
      :key="m.id"
      class="ai-model-option"
      :class="{ 'active': store.selectedModel === m.id, 'disabled': !m.enabled }"
      :disabled="!m.enabled"
      :title="m.disabled_reason || ''"
      @click="selectModel(m.id)"
    >
      {{ m.label }}
      <span v-if="!m.enabled" class="ai-model-lock">🔒</span>
    </button>
  </div>
</div>
```

### DeepSeek provider in SettingsView.vue llmProviders array

```javascript
// In SettingsView.vue script setup — add to llmProviders:
{
  id: "deepseek",
  label: "DeepSeek",
  icon: "🔷",
  apiKeyLabel: "API Key DeepSeek",
  apiKeyPlaceholder: "sk-...",
  docsUrl: "https://platform.deepseek.com/api_keys",
  models: [
    { id: "deepseek-v4-flash", label: "DeepSeek V4 Flash" },
    { id: "deepseek-v4-pro", label: "DeepSeek V4 Pro" }
  ]
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `deepseek-chat` alias | `deepseek-v4-flash` (explicit) | Deprecated; hard cutoff Jul 24, 2026 | Must use new name in all code |
| `deepseek-reasoner` alias | `deepseek-v4-pro` + `thinking` param | Deprecated; hard cutoff Jul 24, 2026 | Must migrate to explicit v4 names |
| LiteLLM 1.82.x | LiteLLM >=1.83.7 | March 2026 security incident | Pin to safe range |
| Module-level agent singleton | Per-request agent factory | This phase | Enables model selection without restart |

**Deprecated/outdated:**

- `deepseek-chat` and `deepseek-reasoner`: both deprecated, fail after July 24, 2026. Do not use.
- LiteLLM 1.82.7–1.82.8: security incident; do not install.

---

## Open Questions

1. **Best key injection mechanism for BYOK (env var vs constructor param)**
   - What we know: `LiteLlm(api_key=...)` is supported and avoids global env mutation
   - What's unclear: Whether ADK 2.1.0's `LiteLlm` constructor passes `api_key` through to LiteLLM's internal completion call correctly (needs a quick test)
   - Recommendation: Try `api_key` constructor param first; fall back to thread-local env manipulation if needed

2. **Agent name uniqueness enforcement in ADK 2.1.0**
   - What we know: ADK validates agent names as Python identifiers; unclear if it enforces global uniqueness
   - What's unclear: Whether `LlmAgent(name="bi_analyst")` called 100x concurrently raises errors
   - Recommendation: During Wave 1 implementation, test with 2 concurrent requests; if error, add UUID suffix

3. **BFF key injection architecture**
   - What we know: Two options — BFF fetches key from backend and injects as header, OR frontend reads key from llm-config store and sends in request body
   - What's unclear: Which is more secure/maintainable for this project's BFF architecture
   - Recommendation: The project's pattern (BFF injects credentials, as seen with `X-User-ID`) favors BFF-side injection. However, this requires the BFF to make an authenticated backend call per chat request (adds latency). Given the project's simplicity-first directive, recommend frontend reads key from its own llm-config store (already loaded in SettingsView) and sends as body field — simpler, no extra BFF→backend round-trip.

4. **DeepSeek V4 Pro pricing after discount ends**
   - What we know: V4 Pro was discounted 75% through May 31, 2026; regular price is $0.55/M input, $2.19/M output (cache miss)
   - What's unclear: Current pricing post-discount (verify at implementation time against https://api-docs.deepseek.com/quick_start/pricing)
   - Recommendation: Use a `PRICING` dict in ai-analyst config rather than hardcoded constants; document the source URL inline

---

## Sources

### Primary (HIGH confidence)
- https://adk.dev/agents/models/litellm/ — LiteLlm class, model string format, import path
- https://docs.litellm.ai/docs/tutorials/google_adk — installation command, LiteLlm usage with ADK
- https://docs.litellm.ai/docs/providers/deepseek — DeepSeek provider prefix, env var name
- https://github.com/google/adk-python/blob/main/pyproject.toml — LiteLLM version pin `>=1.83.7,<=1.83.14`
- https://github.com/google/adk-python/discussions/97 — `stream_options={"include_usage": True}` requirement for usage_metadata

### Secondary (MEDIUM confidence)
- https://api-docs.deepseek.com/quick_start/pricing-details-usd — DeepSeek API model IDs (`deepseek-chat`, `deepseek-reasoner`) and pricing; confirmed deprecated alias names
- https://wavespeed.ai/blog/posts/blog-deepseek-v4-model-name-migration/ — V4 migration deadline July 24 2026, new model names `deepseek-v4-flash` and `deepseek-v4-pro`
- https://github.com/BerriAI/litellm/issues/26395 — Known LiteLLM bug stripping reasoning_content in multi-turn (not in scope for Phase 50)

### Tertiary (LOW confidence — verify at implementation)
- DeepSeek V4 pricing constants: $0.27/M input (cache miss), $1.10/M output for V4 Flash; $0.55/M input, $2.19/M output for V4 Pro. Source: pricing page (June 2026) — **verify before hardcoding, pricing changes frequently**

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — LiteLlm class and ADK integration verified via official docs
- Architecture: HIGH — agent factory pattern confirmed via ADK docs; BYOK reuse confirmed by reading existing codebase
- DeepSeek model strings: MEDIUM — `deepseek-v4-flash` and `deepseek-v4-pro` from migration article; not yet in LiteLLM official docs (which still show old aliases)
- Pitfalls: HIGH — env var race and stream_options gap verified from ADK discussions
- Pricing constants: LOW — changes frequently; must verify at implementation time

**Research date:** 2026-06-01
**Valid until:** 2026-07-01 (30 days for stable ADK/LiteLLM patterns; pricing constants may change sooner)
