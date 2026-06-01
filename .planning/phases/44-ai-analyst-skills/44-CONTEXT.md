# Phase 44: AI Analyst Skills - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrating business-specific tools into the `ai-analyst` service. This includes a CubeJS query tool for real-time data analysis and a Skills Catalog tool for triggering platform actions. The phase also includes extending the chat API to accept and process "screen context" (visible dashboard data).

</domain>

<decisions>
## Implementation Decisions

### Tool Pattern
- Use **Google ADK Python Function Tools**. Define tools as standard async Python functions with descriptive docstrings.
- Docstrings must include schema information (e.g., example CubeJS dimensions/measures) so the LLM understands the data model.

### CubeJS Integration
- Service: `cube_api:4000` (internal Docker network).
- Authentication: HS256 JWT using `CUBEJS_API_SECRET` (default: `welcome1`).
- Endpoint: `/v1/load`.

### Skills Catalog
- URL: `https://raw.githubusercontent.com/ianache/skills-catalog/main/catalog.yaml`.
- Parsing: `PyYAML`.
- Scope: Fetch at service startup (singleton).

### Screen Context
- Schema: `/chat` request body will now accept `{"message": "...", "screen_context": {...}}`.
- Implementation: In `main.py`, if `screen_context` is provided, create a preliminary message in the agent session: `[CONTEXT] The user is currently looking at this data: {context_json}`.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ai-analyst/app/agent.py`: Location to register new tools.
- `ai-analyst/app/main.py`: Location to update ChatRequest schema.
- `ai-analyst/app/core/config.py`: Add `CUBEJS_URL`, `CUBEJS_SECRET`, `SKILLS_CATALOG_URL`.

### established Patterns
- `httpx` for async requests.
- `pydantic-settings` for config.

</code_context>

<specifics>
## Specific Ideas

- The CubeJS tool should be called `query_data`. Its docstring should explain that it expects a JSON object with `measures` and `dimensions`.
- The Skills tool should be called `execute_skill`. Its docstring should dynamically list the top-level categories from the catalog.

</specifics>

---

*Phase: 44-ai-analyst-skills*
*Context gathered: 2026-05-31*
