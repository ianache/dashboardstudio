---
phase: 50-add-a-new-model-based-on-deepseek-to-bi-ai-analyst-in-dashboard-designer-viewer
verified: 2026-06-02T04:30:00Z
status: human_needed
score: 11/11 automated must-haves verified
re_verification: false
human_verification:
  - test: "Open AI Analyst panel — gear icon appears and opens model dropdown"
    expected: "Dropdown shows Gemini Flash (enabled), DeepSeek V4 Flash (locked with lock icon), DeepSeek V4 Pro (locked with lock icon) when no DeepSeek key is saved"
    why_human: "Visual rendering and click behavior cannot be verified programmatically; requires a running browser"
  - test: "Enter a DeepSeek API key in SettingsView and save, then open AI panel gear dropdown"
    expected: "DeepSeek V4 Flash and V4 Pro appear enabled (no lock icon); CORS preflight for GET /bff/ai/models with X-Deepseek-Api-Key header passes (browser network tab shows 200 on OPTIONS preflight)"
    why_human: "Real browser preflight and backend LlmConfig round-trip required; also verifies X-Deepseek-Api-Key header forwarding through BFF aiProxy"
  - test: "Send a chat message with Gemini selected; check assistant response bubble"
    expected: "Each assistant message shows a small 'GEMINI FLASH' badge in tertiary color below the AI ANALYST label"
    why_human: "Visual badge rendering requires a running UI"
  - test: "Select DeepSeek V4 Flash (after saving a key); verify switchModel behavior"
    expected: "A full-width divider row with 'SWITCHED TO DEEPSEEK V4 FLASH' label appears in the chat; subsequent messages show 'DEEPSEEK V4 FLASH' badge"
    why_human: "Message array mutation and divider rendering require a running session"
  - test: "Send a chat message with DeepSeek V4 Flash selected; inspect browser network POST /bff/ai/chat body"
    expected: "Request body contains model: 'deepseek/deepseek-v4-flash' and deepseek_api_key: '<saved_key>'"
    why_human: "Runtime request body inspection requires browser DevTools; also verifies BYOK key flows end-to-end from llmStore through sendMessage"
  - test: "Send a chat message with DeepSeek model active; check the cost chip in AI panel header"
    expected: "COST chip shows a non-zero value (e.g. $0.002); input/output token counts are non-zero"
    why_human: "Requires a live DeepSeek API call with a valid key to verify cost tracking and usage_metadata population via stream_options"
---

# Phase 50: DeepSeek Model Integration — Verification Report

**Phase Goal:** Add DeepSeek as a selectable model in the BI AI Analyst panel — backend model-agnostic routing via LiteLLM, frontend model selector UI, BYOK key flow from SettingsView through BFF to ai-analyst service.
**Verified:** 2026-06-02T04:30:00Z
**Status:** human_needed — all 11 automated checks pass; 6 items require a running browser/live API
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | GET /models returns Gemini always enabled; DeepSeek conditional on X-Deepseek-Api-Key | VERIFIED | `ai-analyst/app/main.py` lines 64-86: endpoint implemented exactly as specified with header-conditional enabled flag |
| 2 | POST /chat accepts model and deepseek_api_key fields; Gemini default preserved | VERIFIED | `ChatRequest` at lines 39-44: `model: str = "gemini-2.5-flash-lite"`, `deepseek_api_key: str | None = None` |
| 3 | LiteLLM invoked via LiteLlm(model=…, api_key=…) with no os.environ mutation | VERIFIED | `ai-analyst/app/agent.py` lines 59-63: `LiteLlm(model=model_str, api_key=deepseek_api_key or "", stream_options={"include_usage": True})` — no os.environ set |
| 4 | stream_options={"include_usage": True} set on LiteLlm | VERIFIED | `agent.py` line 63 confirms this parameter present |
| 5 | Cost calculated per-provider via PRICING dict; cost field in usage SSE event | VERIFIED | `main.py` lines 47-56 (PRICING dict), lines 128-140 (usage SSE with cost field) |
| 6 | DeepSeek appears as provider in SettingsView — deepseek entry in PROVIDERS array | VERIFIED | `llm.js` lines 59-79: deepseek provider with id, label, icon, apiKeyLabel, placeholder, docsUrl, two models |
| 7 | deepseek key slot exists in state.keys and loadConfigFromBackend reset | VERIFIED | `llm.js` lines 136 (state.keys.deepseek: ''), line 202 (reset includes deepseek) |
| 8 | aiAnalyst store has selectedModel, availableModels, fetchModels(), switchModel() | VERIFIED | `aiAnalyst.js` lines 15-61: all state fields and actions present with correct implementation |
| 9 | sendMessage() includes model and deepseek_api_key in POST body | VERIFIED | `aiAnalyst.js` lines 104-117: dynamic import of llmStore, deepseekKey extraction, JSON.stringify with model and conditional deepseek_api_key |
| 10 | Gear icon opens model dropdown; model badge on ALL assistant messages; divider for role='divider' | VERIFIED | `AiAnalystPanel.vue` lines 16-45 (gear + dropdown); `AiAnalystMessage.vue` lines 5-11 (divider branch), lines 26-28 (badge v-if="message.model") |
| 11 | X-Deepseek-Api-Key in BFF CORS allowedHeaders | VERIFIED | `bff/src/index.js` line 49: 'X-Deepseek-Api-Key' present in allowedHeaders array |

**Score:** 11/11 truths verified by static analysis

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ai-analyst/pyproject.toml` | litellm>=1.83.7,<=1.83.14 dependency | VERIFIED | Line 16 confirms correct version range |
| `ai-analyst/app/core/config.py` | deepseek_api_key field in Settings | VERIFIED | Line 20: `deepseek_api_key: str = ""` present |
| `ai-analyst/app/agent.py` | create_runner() factory; no root_agent or runner singletons | VERIFIED | Lines 52-74: create_runner() defined; grep for root_agent and module-level runner returns empty |
| `ai-analyst/app/main.py` | GET /models endpoint + ChatRequest with model/deepseek_api_key + cost tracking | VERIFIED | Lines 64-86 (/models), 39-44 (ChatRequest), 47-56 (PRICING), 128-140 (usage SSE with cost) |
| `dashboard-app/src/stores/llm.js` | deepseek provider in PROVIDERS array (5th entry); deepseek in state.keys | VERIFIED | Lines 59-79 (provider), 136 (state.keys), 202 (loadConfigFromBackend reset) |
| `dashboard-app/src/stores/aiAnalyst.js` | selectedModel, availableModels, fetchModels(), switchModel(), model in sendMessage() | VERIFIED | Lines 15-17 (state), 24-61 (actions), 95-97 (assistantMsg.model), 104-117 (body) |
| `dashboard-app/src/components/dashboard/AiAnalystPanel.vue` | Gear icon + model dropdown + onMounted/onUnmounted lifecycle | VERIFIED | Lines 16-45 (template), 191-215 (script: showModelMenu, selectModel, onMounted, onUnmounted) |
| `dashboard-app/src/components/dashboard/AiAnalystMessage.vue` | Divider branch; model badge; modelLabel() helper; scoped CSS | VERIFIED | Lines 5-11 (divider), 26-28 (badge), 118-126 (modelLabel), 477-518 (CSS) |
| `bff/src/index.js` | X-Deepseek-Api-Key in CORS allowedHeaders | VERIFIED | Line 49 confirmed |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.py POST /chat` | `agent.py create_runner()` | `active_runner = create_runner(request.model, request.deepseek_api_key)` | WIRED | Line 106 in main.py; matches pattern exactly |
| `agent.py create_runner()` | `google.adk.models.lite_llm.LiteLlm` | `LiteLlm(model=model_str, api_key=..., stream_options=...)` | WIRED | Lines 59-63 in agent.py; import at line 9 |
| `AiAnalystPanel.vue onMounted` | `aiAnalyst store fetchModels()` | `await store.fetchModels()` | WIRED | Line 211 in AiAnalystPanel.vue |
| `aiAnalyst store sendMessage()` | `/bff/ai/chat POST body` | `JSON.stringify({ message, context, model: this.selectedModel, ...deepseek_api_key })` | WIRED | Lines 112-117 in aiAnalyst.js |
| `AiAnalystMessage.vue` | `message.model field` | `v-if="message.model"` span.ai-model-badge | WIRED | Lines 26-28 in AiAnalystMessage.vue |
| `bff/src/index.js CORS allowedHeaders` | `fetchModels() X-Deepseek-Api-Key header` | Browser preflight OPTIONS | WIRED (static) | Line 49 confirmed; runtime pass-through via http-proxy-middleware requires human verification |
| `SettingsView.vue` | `llm.js PROVIDERS array` | `llmProviders = PROVIDERS` pattern | WIRED | Plan 50-02 confirmed PROVIDERS exported; SettingsView uses v-for on llmProviders (consistent with existing provider rendering pattern) |

### Notable Observation — BFF Proxy Header Forwarding

The `aiProxy` in `bff/src/proxy.js` does NOT explicitly forward `X-Deepseek-Api-Key` in its `proxyReq` handler (lines 231-242). It relies on http-proxy-middleware's default behavior of forwarding all incoming request headers that are not rewritten. Since the header is listed in CORS `allowedHeaders` (permitting the browser to send it), and the proxy does not strip it, it will be forwarded to the ai-analyst service by default. This is functionally correct but depends on http-proxy-middleware default behavior rather than explicit forwarding — flagged for human verification.

---

## Requirements Coverage

| Requirement | Source Plan | Description (from ROADMAP.md context) | Status | Evidence |
|-------------|------------|---------------------------------------|--------|---------|
| DEEPSEEK-01 | 50-01 | LiteLLM installed with correct version range | SATISFIED | `pyproject.toml` line 16: `litellm>=1.83.7,<=1.83.14` |
| DEEPSEEK-02 | 50-01 | Per-request create_runner() factory; no module-level singleton | SATISFIED | `agent.py`: create_runner() defined; no root_agent or module-level runner found |
| DEEPSEEK-03 | 50-01 | GET /models endpoint; POST /chat with model field and cost tracking | SATISFIED | `main.py` lines 64-150: all three requirements present |
| DEEPSEEK-04 | 50-02 | DeepSeek provider in PROVIDERS array; deepseek key slot in store | SATISFIED | `llm.js`: deepseek entry, state.keys.deepseek, loadConfigFromBackend reset |
| DEEPSEEK-05 | 50-03 | aiAnalyst store model state + fetchModels() + switchModel() | SATISFIED | `aiAnalyst.js`: selectedModel, availableModels, both actions implemented |
| DEEPSEEK-06 | 50-03 | AiAnalystPanel gear dropdown + AiAnalystMessage badges + dividers | SATISFIED | Both Vue files contain all required template branches and scoped CSS |
| DEEPSEEK-07 | 50-03 | X-Deepseek-Api-Key in BFF CORS allowedHeaders | SATISFIED | `bff/src/index.js` line 49 confirmed |

**Requirements coverage:** 7/7 DEEPSEEK requirements satisfied.

**REQUIREMENTS.md note:** DEEPSEEK-01 through DEEPSEEK-07 are defined in ROADMAP.md (Phase 50 requirements list) but are NOT present in `.planning/REQUIREMENTS.md`. The REQUIREMENTS.md file ends at Phase 46 (CHAT-05) and has no entries for Phase 50. This is an administrative gap — the requirement IDs exist in the roadmap and the plans, and the implementations are complete, but REQUIREMENTS.md traceability table is not updated. No functional gap.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `ai-analyst/app/main.py` | 27 | `@app.on_event("startup")` — deprecated FastAPI event decorator | Info | FastAPI recommends `lifespan` context manager in 0.93+. Does not affect Phase 50 functionality; pre-existing pattern. |
| `ai-analyst/app/agent.py` | 68 | `name="bi_analyst"` hardcoded — potential ADK name collision under concurrent requests | Warning | Research doc (PITFALL 3) flagged this: if ADK 2.1.0 enforces agent name uniqueness globally, concurrent requests could raise ValueError. The implementation did not add UUID suffix (plan noted it as conditional). Needs verification under concurrent load. |

No TODO, FIXME, placeholder, or empty implementation patterns found in Phase 50 files. No deprecated DeepSeek model string aliases used (`deepseek-chat`, `deepseek-reasoner` absent; correct `deepseek-v4-flash` and `deepseek-v4-pro` used throughout).

---

## Human Verification Required

### 1. Model Dropdown Visual Rendering

**Test:** Open the AI Analyst panel in a running app (click panel toggle in DashboardDesignerView), then click the gear icon in the panel header.
**Expected:** A dropdown appears listing "Gemini Flash" (enabled, check mark if active), "DeepSeek V4 Flash" (disabled, lock icon), "DeepSeek V4 Pro" (disabled, lock icon) when no DeepSeek key is saved in Settings.
**Why human:** CSS dropdown positioning, lock icon rendering, and disabled state visual appearance cannot be verified statically.

### 2. BYOK Key Unlock Flow + CORS Preflight

**Test:** Go to SettingsView → LLM / IA section → enter a DeepSeek API key → Save. Return to AI Analyst panel → click gear icon.
**Expected:** DeepSeek V4 Flash and V4 Pro now appear enabled. In browser DevTools Network tab, verify OPTIONS /bff/ai/models preflight response includes `Access-Control-Allow-Headers: X-Deepseek-Api-Key` and the subsequent GET /bff/ai/models returns 200 with DeepSeek models enabled.
**Why human:** Requires running BFF + ai-analyst + backend services; CORS preflight behavior requires real browser request.

### 3. Model Badge on Gemini Messages

**Test:** Send a chat message with Gemini Flash selected (default). Observe the assistant response bubble.
**Expected:** Below the "AI ANALYST" label in the response, a small uppercase badge "GEMINI FLASH" appears with tertiary-colored text and a subtle border/background.
**Why human:** Visual badge requires rendering in browser; color and style correctness cannot be automated.

### 4. Model Switch Divider

**Test:** After sending at least one message, save a DeepSeek key in Settings, return to AI panel, click gear, select "DeepSeek V4 Flash". Observe the chat messages area.
**Expected:** A full-width horizontal divider row appears with "SWITCHED TO DEEPSEEK V4 FLASH" as the label. Sending a new message produces a response with "DEEPSEEK V4 FLASH" badge.
**Why human:** Message array state mutation and divider rendering require a live Pinia store session.

### 5. POST /bff/ai/chat Body Content

**Test:** With DeepSeek V4 Flash selected and a key saved, send a chat message. In browser DevTools → Network → find POST /bff/ai/chat → inspect Request Payload.
**Expected:** JSON body contains `"model": "deepseek/deepseek-v4-flash"` and `"deepseek_api_key": "<your_key>"`.
**Why human:** Runtime request body inspection requires browser DevTools; verifies the full BYOK key flow from llmStore through sendMessage().

### 6. Live DeepSeek Cost Tracking

**Test:** With a valid DeepSeek API key and DeepSeek V4 Flash selected, send a real chat message and wait for the response.
**Expected:** The COST chip in the panel header shows a non-zero dollar amount (e.g., $0.002); IN and OUT token counts are non-zero. This confirms stream_options={"include_usage": True} is working and cost calculation runs correctly.
**Why human:** Requires a valid DeepSeek API key and a live network call to the DeepSeek API; cannot simulate.

### 7. Agent Name Collision Under Concurrent Load (Warning)

**Test:** Open two browser tabs both with the AI Analyst panel active, send a message in both simultaneously.
**Expected:** Both receive responses without error. No "Agent name bi_analyst already registered" error in ai-analyst service logs.
**Why human:** Concurrent ADK agent instantiation behavior cannot be verified statically; requires runtime test.

---

## Gaps Summary

No gaps found. All 11 automated must-haves verified, all 7 requirement IDs satisfied, no stub implementations detected.

The phase delivered:
- A complete per-request `create_runner()` factory in `ai-analyst/app/agent.py` using LiteLlm with constructor api_key parameter (avoiding the env var race condition anti-pattern)
- A `GET /models` endpoint in `ai-analyst/app/main.py` with header-driven enable/disable for DeepSeek models
- Per-provider cost calculation via a PRICING dict with the correct model string keys
- DeepSeek as the 5th PROVIDERS entry in `llm.js` with deepseek key slot correctly wired into state.keys and loadConfigFromBackend reset
- Complete model selector UX in `AiAnalystPanel.vue` (gear icon, dropdown, onMounted fetchModels, onUnmounted cleanup)
- Divider messages and model badges in `AiAnalystMessage.vue`
- X-Deepseek-Api-Key added to BFF CORS allowedHeaders

Items requiring human verification are behavioral/visual outcomes that the static codebase correctly enables but cannot confirm end-to-end without a running environment.

---

_Verified: 2026-06-02T04:30:00Z_
_Verifier: Claude (gsd-verifier)_
