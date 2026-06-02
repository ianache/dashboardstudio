# Phase 51: AI Analyst Chat Enhancements — Research

**Researched:** 2026-06-01
**Domain:** Vue 3 Pinia store refactor + Google ADK InMemorySessionService + FastAPI SSE
**Confidence:** HIGH — all findings are based on direct code inspection of the live codebase and live ADK introspection via `uv run python`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANALYST-01 | Pass active dashboard filters as context so the agent analyzes the same data the user sees | Filter values live in `useDashboardFilters` composable (`activeFilterValues`) and `resolvedDashboardFilters` computed. Both must be threaded through `aiAnalyst.js sendMessage()` to the `/chat` POST body, then applied in `cube.py query_data`. |
| ANALYST-02 | Maintain per-dashboard chat history within a session so users can ask follow-up questions | Frontend: change `messages: []` to `sessions: Map<dashboardId, Message[]>` + pass stable `session_id` in POST body. Backend: replace `uuid4()` per-request with get-or-create logic using `session_service.get_session()` / `create_session()`. |
| ANALYST-03 | Auto-summarize chat history when context exceeds 200 KB to prevent context window overflow | Backend: serialize `session.events` with `json.dumps(session.model_dump())` and check byte length before `run_async`. If > 200 KB, call LLM for summary, replace events with one synthetic user message, emit `context_summarized` SSE event. Depends on ANALYST-02 being complete first. |
</phase_requirements>

---

## Summary

Phase 51 adds three enhancements to the AI Analyst chat panel. All three are surgical, with no new dependencies required. The changes touch exactly four files on the backend and three on the frontend.

**ANALYST-01 (Filter context)** is the simplest: `activeFilterValues` and `resolvedDashboardFilters` are already available in `DashboardDesignerView.vue` via the `useDashboardFilters` composable, but `AiAnalystPanel.vue` currently has no access to them. The panel must receive the active filter values (either via props from the parent view or by importing the composable directly). The `sendMessage()` action in `aiAnalyst.js` must forward them in the POST body, and `cube.py` must apply them as CubeJS filter objects when the agent calls `query_data`.

**ANALYST-02 (Session history)** requires replacing the single flat `messages: []` state in `aiAnalyst.js` with a `Map`-keyed-by-dashboardId structure, and replacing the random `uuid4()` session ID in `main.py` with a stable ID derived from `dashboardId + userId`. The ADK `InMemorySessionService` already supports session reuse: `get_session()` returns `None` for unknown IDs, so the pattern is `existing = await get_session(...) or await create_session(...)`. The critical pitfall is that `create_session()` raises `AlreadyExistsError` (from `google.adk.errors.already_exists_error`) if the session already exists — never call it unconditionally.

**ANALYST-03 (Context summarization)** builds directly on ANALYST-02 and must be implemented after it. The ADK `Session` model exposes `events: list[Event]` and is Pydantic v2 serializable via `session.model_dump()`. Byte-level size estimation is trivial: `len(json.dumps(session.model_dump()).encode('utf-8'))`. When over the 200 KB threshold, the backend calls the LLM in a one-shot (non-agent) mode with a summarization prompt, replaces the session events with a single synthetic history message, and emits a `{"type": "context_summarized"}` SSE event before continuing the original request.

**Primary recommendation:** Implement in dependency order: ANALYST-01 independently, ANALYST-02, then ANALYST-03 on top of ANALYST-02.

---

## Standard Stack

### Core (all already installed — zero new dependencies)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `google-adk` | installed | Session management, agent runner | `InMemorySessionService`, `Session`, `Runner` |
| `pydantic` v2 | installed | Session serialization (`model_dump()`) | Used for byte-size estimation |
| `google.genai.types` | installed | Constructing synthetic `Content` for summarization | Already used in `main.py` |
| Vue 3 Pinia | installed | Frontend state — `Map`-based sessions per dashboard | No new stores needed |

**Installation:** No new packages required.

---

## Architecture Patterns

### ANALYST-01: Filter Context Flow

```
DashboardDesignerView
  activeFilterValues (ref)     ← useDashboardFilters composable
  resolvedDashboardFilters     ← computed CubeJS filter objects
       │
       ▼ (prop or composable import)
  AiAnalystPanel.vue
  send() → store.sendMessage(text, { filterValues, resolvedFilters })
       │
       ▼
  aiAnalyst.js sendMessage(text, filterContext)
       body: { message, context, filters: filterContext, model, ... }
       │
       ▼  /bff/ai/chat  →  /chat
  main.py POST /chat
       ChatRequest.filters (new optional field)
       prompt prepend: "[FILTERS] ..." alongside [CONTEXT]
       │
       ▼
  cube.py query_data(query, filters?)
       merge filters into CubeJS query.filters array
```

**Key finding:** `AiAnalystPanel.vue` does NOT currently import `useDashboardFilters`. The composable is only used in `DashboardDesignerView.vue` (line 619). The cleanest approach for ANALYST-01 is to expose `activeFilterValues` and `resolvedDashboardFilters` as props passed from `DashboardDesignerView` to `AiAnalystPanel`, since the panel is already a direct child (`<AiAnalystPanel v-if="aiAnalystStore.isPanelOpen" />`). Alternatively, read `activeDashboard.filters` plus `activeFilterValues` from `localStorage` (key: `ds_filters_${id}`) inside the store's `captureScreenContext()`. The localStorage approach avoids prop threading but couples the store to a storage key string — props are cleaner.

**Filter format sent to backend (resolved CubeJS filters):**
```javascript
// resolvedDashboardFilters is already in CubeJS filter format, e.g.:
[
  { member: "fct_horasreportadas.area", operator: "equals", values: ["Desarrollo"] },
  { member: "fct_horasreportadas.reg_date", operator: "inDateRange", values: ["2026-04-01", "2026-04-30"] }
]
```

**cube.py filter merge (ANALYST-01 backend):**
```python
async def query_data(query: dict, active_filters: list | None = None):
    if active_filters:
        existing = query.get("filters", [])
        query = {**query, "filters": existing + active_filters}
    # ... rest unchanged
```

The agent's system instruction must mention: "When active_filters are provided in the context, always pass them to query_data calls."

### ANALYST-02: Per-Dashboard Session Architecture

#### Frontend (aiAnalyst.js)

Replace:
```javascript
state: () => ({
  messages: [],    // ← flat array, no dashboard isolation
  ...
})
```

With:
```javascript
state: () => ({
  sessions: {},    // dashboardId → { messages: [], usage: {...} }
  activeDashboardId: null,
  ...
})
```

Use a plain object (not `Map`) because Pinia state must be JSON-serializable for devtools. Computed getter `messages` derives from `sessions[activeDashboardId]?.messages || []`.

**session_id derivation:**
```javascript
// In sendMessage() — stable per user+dashboard combination
const sessionId = `${authStore.user?.sub || 'default'}-${dashboardId}`
```

#### Backend (main.py)

Replace the current unconditional create-then-run pattern:

```python
# CURRENT (broken for history):
session_id = str(uuid.uuid4())
await session_service.create_session(app_name=APP_NAME, user_id="default", session_id=session_id)
```

With get-or-create:

```python
# ANALYST-02 pattern (confirmed safe via introspection):
from google.adk.errors.already_exists_error import AlreadyExistsError

async def get_or_create_session(user_id: str, session_id: str) -> None:
    existing = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if existing is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
```

**user_id source:** The BFF already injects `X-User-ID` (from Keycloak `sub`) and `X-User-Email` as headers on every proxied request (confirmed in `bff/src/proxy.js` line 233-238). The FastAPI endpoint can read `x_user_id: str | None = Header(default=None)` as a parameter — no auth changes needed.

**ChatRequest changes:**
```python
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None        # NEW: stable dashboard+user key
    filters: list | None = None           # NEW: active CubeJS filter objects
    screen_context: dict | None = None
    context: dict | None = None
    model: str = "gemini-2.5-flash-lite"
    deepseek_api_key: str | None = None
```

#### Session ID generation (frontend)

```javascript
// Stable session key: dashboardId-userId
// dashboardId is always a numeric DB ID (integer from backend)
// userId is Keycloak sub (stable UUID string)
const sessionId = `${dashboardId}-${authStore.user?.sub || 'anon'}`
```

### ANALYST-03: Context Summarization

**Trigger condition:** Before calling `active_runner.run_async()`, check the serialized session size:

```python
existing = await session_service.get_session(
    app_name=APP_NAME, user_id=user_id, session_id=session_id
)
if existing and existing.events:
    import json
    raw_size = len(json.dumps(existing.model_dump()).encode("utf-8"))
    if raw_size > 200_000:  # 200 KB
        await _summarize_and_replace(session_id, user_id, existing)
```

**Summarization approach — direct LLM call (not agent):**
```python
from google import genai

async def _summarize_and_replace(session_id: str, user_id: str, session):
    client = genai.Client()
    # Build history text from session events
    history_text = _events_to_text(session.events)
    summary_prompt = (
        "Summarize the following BI analysis conversation. "
        "Preserve: key metrics discussed, conclusions reached, data points found, open questions. "
        "Be concise but complete.\n\n" + history_text
    )
    summary_response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=summary_prompt
    )
    summary_text = summary_response.text

    # Delete old session and recreate with single synthetic message
    await session_service.delete_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    # The runner will prepend the summary as a user turn in the new message
    return summary_text
```

**CRITICAL finding:** `InMemorySessionService` does NOT have a `delete_session()` method (not found in source inspection). The alternative is to directly mutate `session_service.sessions[APP_NAME][user_id][session_id].events = []` and create a new initial event, or to use a wrapper dict that the summarization code manages independently. The safest approach given the in-memory implementation is to clear the events list directly (the `InMemorySessionService.sessions` dict is a standard Python dict, directly accessible). The summary is then injected as the first user message in the next `run_async` call by prepending it to the prompt.

**Alternative (simpler, avoids mutation):** Track session size externally in a module-level dict `_session_metadata: dict[str, dict]`. When size exceeds threshold, clear the session by recreating it (create a new `InMemorySessionService` entry after clearing the old one from `session_service.sessions`). This avoids relying on a missing `delete_session` API.

**SSE event for frontend divider:**
```python
yield ServerSentEvent(data={"type": "context_summarized"})
```

Frontend `_processStreamEvent` adds a new case:
```javascript
case 'context_summarized':
  this.messages.push({
    role: 'divider',
    label: 'Contexto resumido para mantener respuestas precisas',
    model: null
  })
  break
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session lookup | Custom session map in app state | `session_service.get_session()` | Already thread-safe per ADK design |
| Session size estimate | Tokenizer integration | `len(json.dumps(session.model_dump()).encode('utf-8'))` | 200 KB byte threshold is intentionally approximate; no tokenizer needed |
| Filter merging | Custom filter DSL | CubeJS native filter objects (already produced by `resolvedDashboardFilters`) | `buildCubeFilter` in `useDashboardFilters.js` already produces the exact format CubeJS expects |
| Summary LLM call | New agent runner | Direct `genai.Client().models.generate_content()` | Summarization is a single one-shot call, not a multi-turn agent interaction |

---

## Common Pitfalls

### Pitfall 1: Calling `create_session()` on an existing session ID
**What goes wrong:** `AlreadyExistsError` is raised — the request fails with a 500.
**Why it happens:** The current code always calls `create_session` with a fresh `uuid4()`. When session IDs become stable (ANALYST-02), the same session ID will arrive on every message in the same chat session.
**How to avoid:** Always call `get_session()` first. Create only if `None` is returned.
**Warning signs:** 500 errors on the second message in any conversation.

### Pitfall 2: Pinia `Map` type breaks devtools serialization
**What goes wrong:** Vue devtools / Pinia persist plugins cannot serialize `Map` objects.
**Why it happens:** `Map` is not JSON-serializable.
**How to avoid:** Use a plain object `{}` keyed by dashboardId as a `Map` substitute. `sessions[dashboardId]` works identically.

### Pitfall 3: `activeFilterValues` not accessible inside `AiAnalystPanel`
**What goes wrong:** The panel sends `filters: null` because it imports neither the composable nor the dashboard store filter state.
**Why it happens:** `useDashboardFilters` is only used in `DashboardDesignerView`. `AiAnalystPanel` imports only `useAiAnalystStore`.
**How to avoid:** Pass `activeFilterValues` and `resolvedDashboardFilters` as props to `AiAnalystPanel` from `DashboardDesignerView`, or move the filter capture into `sendMessage()` inside the store (reading from `dashboardStore.activeDashboard.filters` plus the `localStorage` key `ds_filters_${id}`). Props are architecturally cleaner.

### Pitfall 4: `delete_session()` does not exist on `InMemorySessionService`
**What goes wrong:** `AttributeError: 'InMemorySessionService' object has no attribute 'delete_session'` at runtime.
**Why it happens:** The method is not implemented in the current ADK version.
**How to avoid:** For session clearing during summarization, directly clear the events list: `session_service.sessions[APP_NAME][user_id][session_id].events.clear()`. This is safe because `InMemorySessionService` is a single in-process singleton.

### Pitfall 5: filter context doubles the token count for every message
**What goes wrong:** For dashboards with many filters, the serialized filter JSON repeats in every user turn of the session history, causing early context overflow.
**Why it happens:** Filters are injected into the user message prompt text on every request.
**How to avoid:** Inject filters once as a compact formatted string (not full JSON), e.g. `"[FILTERS] area=Desarrollo, date=2026-04-01..2026-04-30"`. Reserve full CubeJS filter JSON for the `query_data` tool invocation context.

### Pitfall 6: `activeDashboardId` not set when `AiAnalystPanel` mounts
**What goes wrong:** `sessions[null]` is used, and all dashboard histories collapse into a single `null` bucket.
**Why it happens:** The store does not know which dashboard is open unless explicitly told.
**How to avoid:** When the panel opens (`togglePanel()`), the store reads `dashboardStore.activeDashboardId` and sets `this.activeDashboardId`. Watch `dashboardStore.activeDashboardId` in the store to switch the active session context reactively.

---

## Code Examples

### Pattern: get-or-create session (backend, ANALYST-02)

```python
# Source: direct ADK source inspection (uv run python introspection, 2026-06-01)
from google.adk.errors.already_exists_error import AlreadyExistsError

async def ensure_session(user_id: str, session_id: str) -> None:
    existing = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if existing is None:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
```

### Pattern: session byte-size check (backend, ANALYST-03)

```python
# Source: direct Session.model_dump() inspection — Pydantic v2 model
import json

async def session_byte_size(session_id: str, user_id: str) -> int:
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if not session:
        return 0
    return len(json.dumps(session.model_dump()).encode("utf-8"))
```

### Pattern: clear session events for summarization (backend, ANALYST-03)

```python
# Direct mutation of InMemorySessionService internal dict
# Safe because session_service is a module-level singleton
def _clear_session_events(user_id: str, session_id: str) -> None:
    try:
        svc_sessions = session_service.sessions
        svc_sessions[APP_NAME][user_id][session_id].events.clear()
    except KeyError:
        pass  # Session doesn't exist yet — nothing to clear
```

### Pattern: per-dashboard session state (frontend, aiAnalyst.js, ANALYST-02)

```javascript
// Use plain object (JSON-serializable), not Map (not serializable)
state: () => ({
  sessions: {},          // { [dashboardId]: { messages: [], usage: {} } }
  activeDashboardId: null,
  loading: false,
  isPanelOpen: false,
  selectedModel: 'gemini-2.5-flash-lite',
  availableModels: []
}),

getters: {
  messages: (state) => {
    const id = state.activeDashboardId
    return id ? (state.sessions[id]?.messages || []) : []
  },
  usage: (state) => {
    const id = state.activeDashboardId
    return id ? (state.sessions[id]?.usage || defaultUsage()) : defaultUsage()
  }
},
```

### Pattern: stable session_id construction (frontend)

```javascript
// In sendMessage() or as a computed inside the store action
function buildSessionId(dashboardId, userSub) {
  return `${dashboardId}-${userSub || 'anon'}`
}
// authStore.user?.sub comes from Keycloak — stable UUID for the browser session
```

### Pattern: reading X-User-ID in FastAPI (backend)

```python
# BFF already injects this header (confirmed in bff/src/proxy.js line 233-238)
@app.post("/chat", response_class=EventSourceResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str | None = Header(default=None)
):
    user_id = x_user_id or "default"
    session_id = request.session_id or str(uuid.uuid4())
    await ensure_session(user_id, session_id)
    ...
```

### Pattern: filter context injection into agent prompt (backend, ANALYST-01)

```python
# Compact string format to minimize token cost per turn
def format_filters_for_prompt(filters: list) -> str:
    if not filters:
        return ""
    parts = []
    for f in filters:
        member = f.get("member", "")
        op = f.get("operator", "")
        vals = f.get("values", [])
        parts.append(f"{member} {op} {vals}")
    return "[ACTIVE FILTERS] " + "; ".join(parts)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| New session per request (`uuid4()`) | Stable session ID per dashboard+user | Phase 51 (ANALYST-02) | Agent can answer follow-up questions using prior context |
| Flat `messages: []` array | `sessions: {}` keyed by dashboardId | Phase 51 (ANALYST-02) | Users switching dashboards get separate histories |
| No filter context | Active CubeJS filters forwarded in every request | Phase 51 (ANALYST-01) | Agent queries match what the user sees on screen |
| Unbounded session growth | Auto-summarize at 200 KB | Phase 51 (ANALYST-03) | Prevents context overflow; reduces token cost on long sessions |

---

## Open Questions

1. **`delete_session()` absence in ADK**
   - What we know: Method does not exist on `InMemorySessionService` as of the installed version.
   - What's unclear: Whether future ADK versions will add it.
   - Recommendation: Use direct event list mutation (`events.clear()`) for Phase 51. Document the fragility. If ADK adds a proper API, migrate in a future phase.

2. **Should `activeDashboardId` live in the aiAnalyst store or be injected?**
   - What we know: `dashboardStore.activeDashboardId` already tracks the open dashboard.
   - What's unclear: Whether the aiAnalyst store should watch `dashboardStore` directly (coupling) or receive the ID via method call.
   - Recommendation: Read `dashboardStore.activeDashboardId` in `sendMessage()` at call time — no watcher needed. The store is already imported at the top of `aiAnalyst.js` (`import { useDashboardStore } from '@/stores/dashboard'`).

3. **`clearMessages()` behavior with per-dashboard sessions**
   - What we know: Current `clearMessages()` resets the flat array. With ANALYST-02, it must clear only the active dashboard's session.
   - Recommendation: Update `clearMessages()` to do `this.sessions[this.activeDashboardId] = null`. Also call `_clear_session_events()` on the backend via a new `DELETE /session` endpoint, or simply let the backend session expire naturally (in-memory, resets on restart anyway).

---

## Sources

### Primary (HIGH confidence)
- Direct source inspection of `ai-analyst/app/main.py`, `ai-analyst/app/agent.py`, `ai-analyst/app/tools/cube.py` — current implementation
- Direct source inspection of `dashboard-app/src/stores/aiAnalyst.js`, `dashboard-app/src/stores/dashboard.js`, `dashboard-app/src/composables/useDashboardFilters.js` — current frontend state model
- Direct source inspection of `dashboard-app/src/components/dashboard/AiAnalystPanel.vue`, `DashboardFilterBar.vue`, `DashboardDesignerView.vue` — component boundaries and prop flows
- `uv run python` ADK introspection: `InMemorySessionService` source, `Session.model_fields`, `get_session()` returns `None` for missing sessions (verified), `create_session()` raises `AlreadyExistsError` for duplicate IDs (verified), `session.model_dump()` is JSON-serializable (verified, empty session = 116 bytes)
- `bff/src/proxy.js` — confirmed `X-User-ID` and `X-User-Email` injection in `aiProxy.proxyReq`

### Secondary (MEDIUM confidence)
- ADK `Session.events` field structure inspected via `Event.model_fields.keys()` — events accumulate in the session between `run_async` calls

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; all tools already installed
- Architecture patterns: HIGH — verified via live code inspection and ADK introspection
- Pitfalls: HIGH — `AlreadyExistsError` and `delete_session` absence verified in live Python

**Research date:** 2026-06-01
**Valid until:** 2026-07-01 (stable ADK API; risk of ADK version bump changing session internals)
