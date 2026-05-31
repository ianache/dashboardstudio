# Phase 43: AI Service Foundation - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

A new standalone Python microservice (`ai-analyst/`) that accepts a chat message and returns a Gemini-powered response via Google ADK. No agent tools yet — pure skeleton. Downstream phases add tools (Phase 44), BFF proxy (Phase 45), and chat UI (Phase 46).

</domain>

<decisions>
## Implementation Decisions

### Response delivery
- `/chat` uses SSE streaming (not synchronous JSON)
- Typed events: `{type: 'token', text: '...'}` during generation, `{type: 'done', usage: {input_tokens, output_tokens}}` at end
- Phase 43 produces only `token` and `done` event types — `agent_step` events added in Phase 44 when tools are wired in
- Mid-stream errors: send `{type: 'error', message: '...'}` inline (do not drop connection with HTTP 500)

### Request/response schema
- `/chat` request body: `{message: string}` — minimal for Phase 43; Phase 44/45 extend with session_id and screen_context
- `done` event usage object: `{input_tokens, output_tokens}` from Gemini response
- `/health` returns `{status: 'ok'}` with HTTP 200 — nothing more

### Service conventions
- Mirror the backend exactly: FastAPI + uv + `python:3.11-slim` Dockerfile base
- Flat internal structure: `app/main.py` (FastAPI app + routes) + `app/agent.py` (Google ADK agent logic)
- Env file: `.env-ai-analyst` (follows existing `.env-backend`, `.env-bff` naming pattern)

### Port & Traefik wiring
- Internal port: 8001 (sequential after backend's 8000)
- Port exposed for local dev: `ports: 8001:8001` — makes Phase 43 testing easy without a BFF proxy
- No Traefik labels in Phase 43 — deferred to Phase 45 when BFF integration is done

### Claude's Discretion
- Exact `pyproject.toml` dependencies and versions
- CORS configuration for dev
- How Google ADK `LlmAgent` is instantiated internally
- Dockerfile COPY order and layer caching optimizations

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/Dockerfile`: Exact template to copy for `ai-analyst/Dockerfile` — same `FROM python:3.11-slim`, `uv sync --frozen`, `uvicorn` CMD pattern
- `backend/app/core/config.py`: Reference for Pydantic Settings pattern to read env vars

### Established Patterns
- `uv` as package manager (not pip/poetry) — replicate in `ai-analyst/pyproject.toml`
- Docker Compose service entry pattern: `build.context`, `env_file`, `restart: unless-stopped`, `networks: backends`
- Services are internal-only by default (no `ports:`); exception: add `ports: 8001:8001` for Phase 43 dev access

### Integration Points
- `docker-compose.yaml`: Add `ai-analyst` service entry — depends on nothing in Phase 43
- `.env-ai-analyst`: New env file at repo root following `.env-backend` convention
- Phase 44 will add tools to `app/agent.py` — keep the agent module boundary clean

</code_context>

<specifics>
## Specific Ideas

- "The service should feel like a second backend" — same tooling, same file layout conventions, same Dockerfile base
- SSE chosen explicitly even for Phase 43 so Phase 46 doesn't need a contract change when the UI ships

</specifics>

<deferred>
## Deferred Ideas

- Traefik routing for ai-analyst — Phase 45
- Session-aware requests (session_id, screen_context) — Phase 45
- agent_step SSE events (thought/action/result) — Phase 44
- Conversation history persistence — out of scope for v2.0 (Requirements doc)

</deferred>

---

*Phase: 43-ai-service-foundation*
*Context gathered: 2026-05-31*
