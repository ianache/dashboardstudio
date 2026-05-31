# Phase 43: AI Service Foundation - Research

**Researched:** 2026-05-31
**Domain:** Google ADK (Agent Development Kit) Python microservice with FastAPI SSE streaming
**Confidence:** MEDIUM-HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Response delivery**
- `/chat` uses SSE streaming (not synchronous JSON)
- Typed events: `{type: 'token', text: '...'}` during generation, `{type: 'done', usage: {input_tokens, output_tokens}}` at end
- Phase 43 produces only `token` and `done` event types — `agent_step` events added in Phase 44 when tools are wired in
- Mid-stream errors: send `{type: 'error', message: '...'}` inline (do not drop connection with HTTP 500)

**Request/response schema**
- `/chat` request body: `{message: string}` — minimal for Phase 43; Phase 44/45 extend with session_id and screen_context
- `done` event usage object: `{input_tokens, output_tokens}` from Gemini response
- `/health` returns `{status: 'ok'}` with HTTP 200 — nothing more

**Service conventions**
- Mirror the backend exactly: FastAPI + uv + `python:3.11-slim` Dockerfile base
- Flat internal structure: `app/main.py` (FastAPI app + routes) + `app/agent.py` (Google ADK agent logic)
- Env file: `.env-ai-analyst` (follows existing `.env-backend`, `.env-bff` naming pattern)

**Port & Traefik wiring**
- Internal port: 8001 (sequential after backend's 8000)
- Port exposed for local dev: `ports: 8001:8001`
- No Traefik labels in Phase 43 — deferred to Phase 45

### Claude's Discretion
- Exact `pyproject.toml` dependencies and versions
- CORS configuration for dev
- How Google ADK `LlmAgent` is instantiated internally
- Dockerfile COPY order and layer caching optimizations

### Deferred Ideas (OUT OF SCOPE)
- Traefik routing for ai-analyst — Phase 45
- Session-aware requests (session_id, screen_context) — Phase 45
- `agent_step` SSE events (thought/action/result) — Phase 44
- Conversation history persistence — out of scope for v2.0
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SVC-01 | A dedicated Python microservice uses Google ADK to orchestrate the agent workflow with Gemini models via native API | Google ADK 2.1.0 with LlmAgent + Runner pattern; FastAPI SSE streaming; uv + pyproject.toml; docker-compose service entry |
</phase_requirements>

---

## Summary

Phase 43 builds a new Python microservice (`ai-analyst/`) that is structurally identical to the existing `backend/` service (FastAPI, uv, `python:3.11-slim` Docker image) but uses Google ADK 2.1.0 to power a Gemini-driven agent. The service exposes two endpoints: `GET /health` and `POST /chat`. The `/chat` endpoint streams a Server-Sent Events response using FastAPI's native SSE support, yielding `token` events for each text chunk from the model and a `done` event with token usage at completion.

The core ADK pattern is: define an `LlmAgent` with model and instruction, create a singleton `Runner` backed by `InMemorySessionService`, and call `runner.run_async()` per request. The Runner is stateless and safe to reuse across concurrent requests — only the `session_id` varies per call. For Phase 43 (no conversation history), a unique `session_id` per request is sufficient.

Google ADK auto-reads `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI` from environment. The project's `pydantic-settings` pattern (already in `backend/app/core/config.py`) is the right approach to layer agent-specific vars (`GEMINI_MODEL`, `GOOGLE_API_KEY`) on top.

**Primary recommendation:** Use `google-adk==2.1.0` with `LlmAgent` + `Runner` + `InMemorySessionService`. Wire FastAPI's native `EventSourceResponse` (added in FastAPI 0.135.0) for the SSE endpoint. Mirror `backend/pyproject.toml` structure exactly with `uv` as the package manager.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-adk | 2.1.0 | ADK orchestration, LlmAgent, Runner, sessions | The locked choice — provides the ADK orchestration layer over Gemini |
| fastapi | >=0.135.0 | Web framework + native SSE support | Already in use in `backend/`; native EventSourceResponse added in 0.135.0 |
| uvicorn[standard] | >=0.27.0 | ASGI server | Matches `backend/` Dockerfile CMD pattern |
| pydantic-settings | >=2.1.0 | Environment variable configuration | Same pattern as `backend/app/core/config.py` |
| python-dotenv | >=1.0.0 | .env file loading | Matches backend convention |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.26.0 | Async HTTP client | Needed by google-adk internally; explicit dep avoids version conflicts |
| python-multipart | >=0.0.6 | FastAPI form/body parsing | Required by FastAPI for request body parsing |

### What google-adk brings automatically

`google-adk` declares these in its own dependencies — no need to add to pyproject.toml:
- `google-genai` (Gemini client)
- `fastapi`, `uvicorn`, `starlette` (already there as own ADK server)
- `pyyaml`, `httpx`, `tenacity`, `opentelemetry-*`

**Installation (uv):**
```bash
# In ai-analyst/
uv add google-adk fastapi uvicorn pydantic-settings python-dotenv httpx python-multipart
```

Or declare in `pyproject.toml` dependencies then:
```bash
uv sync --frozen
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| google-adk LlmAgent | Direct google-genai SDK call | Direct SDK skips ADK orchestration layer; violates SVC-01 success criterion 3 ("not a direct Gemini SDK call") |
| FastAPI native SSE (0.135.0+) | sse-starlette library | sse-starlette is the older approach; FastAPI 0.135+ has EventSourceResponse built-in, matching the backend's FastAPI version trajectory |
| InMemorySessionService | DatabaseSessionService | DB session adds complexity out of scope for Phase 43; history persistence deferred to v2.1 |

---

## Architecture Patterns

### Recommended Project Structure

```
ai-analyst/
├── app/
│   ├── main.py          # FastAPI app, /health, /chat SSE endpoint
│   └── agent.py         # LlmAgent definition, Runner, session_service singletons
├── pyproject.toml       # uv project config (mirrors backend/pyproject.toml)
├── uv.lock              # generated by uv sync
└── Dockerfile           # mirrors backend/Dockerfile exactly (port 8001)
```

At repo root:
```
.env-ai-analyst          # GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI, GEMINI_MODEL
docker-compose.yaml      # add ai-analyst service entry
```

### Pattern 1: LlmAgent + Runner singleton

**What:** Define the agent and runner once at module level in `app/agent.py`. Import them in `app/main.py` for use in request handlers.
**When to use:** Always — Runner is stateless and safe for concurrent reuse per the ADK GitHub discussion #3924.

```python
# app/agent.py
# Source: https://adk.dev/agents/llm-agents/ + discussion #3924
import os
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

root_agent = LlmAgent(
    name="bi_analyst",
    model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction="You are a BI analyst assistant. Answer questions about business data clearly and concisely.",
)

runner = Runner(
    app_name="ai-analyst",
    agent=root_agent,
    session_service=session_service,
)
```

### Pattern 2: FastAPI SSE endpoint using native EventSourceResponse

**What:** Use FastAPI 0.135+ `EventSourceResponse` with an async generator that iterates `runner.run_async()` events.
**When to use:** The `/chat` endpoint.

```python
# app/main.py — the /chat endpoint
# Source: https://fastapi.tiangolo.com/tutorial/server-sent-events/ + ADK streaming docs
import uuid
import json
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode
from app.agent import runner, session_service
from pydantic import BaseModel

app = FastAPI(title="AI Analyst Service")

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name="ai-analyst",
        user_id="default",
        session_id=session_id,
    )

    async def stream():
        run_config = RunConfig(streaming_mode=StreamingMode.SSE)
        try:
            async for event in runner.run_async(
                user_id="default",
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=request.message)],
                ),
                run_config=run_config,
            ):
                # Emit token events for partial text chunks
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            yield ServerSentEvent(
                                data=json.dumps({"type": "token", "text": part.text})
                            )

                # Emit done event on final response with usage metadata
                if event.is_final_response():
                    usage = {}
                    if event.usage_metadata:
                        usage = {
                            "input_tokens": event.usage_metadata.prompt_token_count or 0,
                            "output_tokens": event.usage_metadata.candidates_token_count or 0,
                        }
                    yield ServerSentEvent(
                        data=json.dumps({"type": "done", "usage": usage})
                    )
        except Exception as e:
            yield ServerSentEvent(
                data=json.dumps({"type": "error", "message": str(e)})
            )

    return EventSourceResponse(stream())
```

### Pattern 3: pydantic-settings config (mirrors backend pattern)

```python
# app/core/config.py
# Source: mirrors backend/app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env-ai-analyst",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ADK / Gemini
    google_api_key: str = ""
    google_genai_use_vertexai: str = "FALSE"
    gemini_model: str = "gemini-2.0-flash"

    # Service
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    cors_origins: str = "http://localhost:3000"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Pattern 4: Dockerfile (exact mirror of backend/Dockerfile)

```dockerfile
# Source: mirrors backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Pattern 5: docker-compose.yaml service entry

```yaml
# Add to docker-compose.yaml services: block
ai-analyst:
  build:
    context: ./ai-analyst
    dockerfile: Dockerfile
  env_file:
    - ./.env-ai-analyst
  ports:
    - "8001:8001"
  restart: unless-stopped
  networks:
    - backends
```

No `depends_on` needed in Phase 43 — the service has no upstream dependencies yet.

### Anti-Patterns to Avoid

- **Creating a new Runner per request:** Runner should be a module-level singleton. Creating per-request wastes memory and defeats session isolation design.
- **Calling google-genai directly:** Bypasses the ADK orchestration layer, breaking the SVC-01 requirement that the service "uses Google ADK orchestration — not a direct Gemini SDK call."
- **Hardcoding GOOGLE_API_KEY or model name:** All agent configuration must come from environment variables.
- **Returning HTTP 500 on mid-stream errors:** Per the locked decision, errors must be sent inline as `{type: 'error', message: '...'}` SSE events — not as HTTP error responses.
- **Reusing the same session_id across requests:** Phase 43 has no conversation history. Generate `uuid.uuid4()` per request and create a fresh session.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM invocation & response streaming | Custom Gemini SDK wrapper with manual streaming | `google-adk` LlmAgent + Runner | ADK handles tool loop, event routing, retry, session state — months of edge cases |
| SSE response formatting | Manual `data: ...\n\n` string concatenation | FastAPI native `EventSourceResponse` + `ServerSentEvent` | Built-in keep-alive pings, correct headers (Cache-Control, X-Accel-Buffering), auto JSON encoding |
| Session isolation | Custom dict keyed by request | `InMemorySessionService` from ADK | ADK session service handles concurrent access; using a plain dict is not concurrency-safe |
| Token count extraction | Manually counting characters or words | `event.usage_metadata.prompt_token_count` / `candidates_token_count` | Gemini returns exact token counts in the response metadata |

**Key insight:** ADK's value is not the Gemini call itself — it is the event routing loop, the session state protocol, and the tool dispatch framework that Phase 44 will extend. Phase 43 must use ADK correctly so Phase 44 has a clean extension point.

---

## Common Pitfalls

### Pitfall 1: app_name mismatch between session creation and Runner

**What goes wrong:** `Session not found` error on the first request, or on every request after the first.
**Why it happens:** The `app_name` passed to `session_service.create_session()` must exactly match the `app_name` passed to `Runner(app_name=...)`. Any mismatch (capitalization, hyphens vs underscores) causes lookups to fail.
**How to avoid:** Define `APP_NAME = "ai-analyst"` as a module-level constant in `agent.py` and pass it to both `Runner` and every `session_service.create_session()` call.
**Warning signs:** `Session not found` errors in logs on the first user message.

### Pitfall 2: FastAPI version below 0.135.0 lacks native SSE

**What goes wrong:** `from fastapi.sse import EventSourceResponse` fails with ImportError.
**Why it happens:** Native SSE (`EventSourceResponse`, `ServerSentEvent`) was added in FastAPI 0.135.0. Older versions require the `sse-starlette` third-party library.
**How to avoid:** Pin `fastapi>=0.135.0` in `pyproject.toml`. Alternatively, use `sse-starlette` as a fallback, but prefer the native approach for consistency.
**Warning signs:** ImportError on startup.

### Pitfall 3: GOOGLE_GENAI_USE_VERTEXAI not set — ADK tries Vertex AI instead of Gemini API

**What goes wrong:** ADK attempts to use Application Default Credentials for Vertex AI and fails with authentication errors instead of using the API key.
**Why it happens:** ADK checks `GOOGLE_GENAI_USE_VERTEXAI` env var. If not set or set to `TRUE`, it uses Vertex AI. If `FALSE`, it uses `GOOGLE_API_KEY`.
**How to avoid:** Always set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` in `.env-ai-analyst`.
**Warning signs:** `google.auth.exceptions.DefaultCredentialsError` at startup.

### Pitfall 4: Missing `uv.lock` in Dockerfile COPY

**What goes wrong:** `uv sync --frozen` fails because `uv.lock` is not in the image.
**Why it happens:** The Dockerfile copies `pyproject.toml uv.lock ./` — if the developer hasn't run `uv sync` locally yet, `uv.lock` doesn't exist.
**How to avoid:** Run `uv sync` locally before building the image. Commit `uv.lock` to git.
**Warning signs:** `uv sync --frozen` fails with "lockfile not found."

### Pitfall 5: Streaming events not yielding partial tokens — only final response

**What goes wrong:** The SSE stream appears to buffer and only sends one large `token` event at the end, not incremental chunks.
**Why it happens:** `RunConfig(streaming_mode=StreamingMode.SSE)` must be explicitly passed to `runner.run_async()`. Without it, ADK defaults to non-streaming mode and yields only the final event.
**How to avoid:** Always construct and pass `run_config = RunConfig(streaming_mode=StreamingMode.SSE)` to every `run_async()` call.
**Warning signs:** UI appears frozen until the full response arrives, then shows everything at once.

### Pitfall 6: agent name containing hyphens or starting with a digit

**What goes wrong:** ADK raises `ValueError` on startup: "Agent name must be a valid Python identifier."
**Why it happens:** ADK validates that agent `name` follows Python identifier rules. `"bi-analyst"` is invalid (hyphen); `"bi_analyst"` is valid.
**How to avoid:** Use underscores in agent names: `name="bi_analyst"`.
**Warning signs:** `ValueError` at import time of `agent.py`.

---

## Code Examples

### Minimal pyproject.toml for ai-analyst/

```toml
# Source: mirrors backend/pyproject.toml structure
[project]
name = "ai-analyst"
version = "0.1.0"
description = "AI Analyst microservice — Google ADK + Gemini"
requires-python = ">=3.11"
dependencies = [
    "google-adk>=2.1.0",
    "fastapi>=0.135.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "python-multipart>=0.0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.uv]
dev-dependencies = []
```

### Minimal .env-ai-analyst

```bash
# .env-ai-analyst (at repo root)
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GEMINI_MODEL=gemini-2.0-flash
```

### Token count extraction from ADK event

```python
# Source: ADK GitHub discussion #2434 + ADK events docs
if event.is_final_response():
    usage = {"input_tokens": 0, "output_tokens": 0}
    if event.usage_metadata:
        usage["input_tokens"] = event.usage_metadata.prompt_token_count or 0
        usage["output_tokens"] = event.usage_metadata.candidates_token_count or 0
    yield ServerSentEvent(data=json.dumps({"type": "done", "usage": usage}))
```

### CORS for dev (Claude's discretion)

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sse-starlette` third-party library | FastAPI native `EventSourceResponse` in `fastapi.sse` | FastAPI 0.135.0 (2025) | One less dependency; keep-alive and correct headers built in |
| `LlmAgent` as distinct alias | `Agent` as primary class (`from google.adk import Agent`); `LlmAgent` is an alias | ADK 1.x → 2.x | Both work; official docs use `LlmAgent` for Python; `Agent` is the TypeScript/Java pattern |
| ADK 1.x: `Runner(app_name=..., agent=..., session_service=...)` | ADK 2.x: same constructor signature, but `App` object wrapping optional | ADK 2.0 (breaking) | For simple single-agent cases the flat `Runner(app_name=..., agent=..., session_service=...)` still works |
| Direct google-genai SDK calls | ADK Runner orchestration | 2025 (ADK launch) | ADK adds session, tool dispatch, event loop; required by SVC-01 |

**Deprecated/outdated:**
- ADK 1.x session schema: sessions from ADK 2.0 are incompatible with ADK <1.28 — pin `google-adk>=2.1.0` to stay on current schema.
- `google-generativeai` package (old SDK): ADK uses `google-genai` (new unified SDK). Do not add `google-generativeai` as a dependency.

---

## Open Questions

1. **FastAPI version compatibility with google-adk 2.1.0**
   - What we know: google-adk declares `fastapi` as its own dependency. The version google-adk bundles may differ from `fastapi>=0.135.0`.
   - What's unclear: Whether google-adk 2.1.0 pins a FastAPI version that includes `fastapi.sse`. If google-adk pins FastAPI <0.135.0, `from fastapi.sse import EventSourceResponse` will fail.
   - Recommendation: In `pyproject.toml` explicitly declare `fastapi>=0.135.0`. If there is a conflict, fall back to `sse-starlette` for SSE formatting.

2. **`event.is_final_response()` behavior in SSE streaming mode**
   - What we know: `is_final_response()` is the documented helper to detect the final user-facing event.
   - What's unclear: Whether in `StreamingMode.SSE` the final event carries `usage_metadata`, or if `usage_metadata` appears on a separate metadata-only event. The ADK GitHub issue #1995 flags inconsistencies in `total_token_count` vs `output_tokens` naming.
   - Recommendation: Guard with `if event.usage_metadata:` before accessing token counts. Log all events during development to observe the event stream shape.

3. **Session creation: async vs sync `create_session`**
   - What we know: Examples show `await session_service.create_session(...)`.
   - What's unclear: Whether `InMemorySessionService.create_session()` is actually async or sync (documentation and examples are inconsistent on `await`).
   - Recommendation: Use `await` — if `create_session` is sync, Python will raise a clear error immediately during testing.

---

## Sources

### Primary (HIGH confidence)
- PyPI `google-adk` — latest version 2.1.0 confirmed May 23, 2026
- FastAPI docs (fastapi.tiangolo.com/tutorial/server-sent-events/) — native SSE added in 0.135.0, `EventSourceResponse` and `ServerSentEvent` APIs verified
- ADK GitHub discussion #3924 — Runner singleton + session isolation pattern
- ADK agents LLM docs (adk.dev/agents/llm-agents/) — `LlmAgent` constructor, `model` as string parameter

### Secondary (MEDIUM confidence)
- ADK training hub (raphaelmansuy.github.io/adk_training/docs/streaming_sse/) — full SSE streaming code pattern verified against official ADK streaming docs
- ADK troubleshooting guide (iamulya.one) — pitfalls list cross-referenced with ADK GitHub issues
- ADK environment configuration (deepwiki.com/google/adk-docs) — `GOOGLE_API_KEY` + `GOOGLE_GENAI_USE_VERTEXAI=FALSE` pattern

### Tertiary (LOW confidence — verify during implementation)
- ADK 2.0 breaking changes: claimed from multiple sources but exact API diff not confirmed from official CHANGELOG (GitHub truncated content)
- `event.usage_metadata.prompt_token_count` / `candidates_token_count` field names: sourced from community discussion #2434 and #97; verify against actual event object during implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `google-adk 2.1.0` version confirmed from PyPI; FastAPI SSE from official docs
- Architecture: MEDIUM-HIGH — LlmAgent + Runner + InMemorySessionService pattern verified from multiple sources including official ADK GitHub; SSE endpoint pattern from ADK streaming tutorial verified against FastAPI docs
- Pitfalls: MEDIUM — session `app_name` mismatch and `GOOGLE_GENAI_USE_VERTEXAI` are confirmed from GitHub issues; `usage_metadata` field names are LOW confidence pending runtime verification

**Research date:** 2026-05-31
**Valid until:** 2026-06-14 (google-adk moves fast; re-verify pyproject.toml pins before implementing)
