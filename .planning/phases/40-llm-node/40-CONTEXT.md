# Phase 40: LLM Node - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add an `llm` node to integration flows that allows calling OpenAI-compatible endpoints securely.

### Core Value
Enable AI-powered transformations, summarization, and data generation within flows while keeping sensitive API keys on the backend and never passing them to the Deno runner.

### Success Criteria
- User can create an LLM Connection (DataSource) with Base URL and API Key.
- User can add an LLM Node, select a Connection, and define System and User prompts.
- User Prompt supports `{{payload.key}}` interpolation from initial flow input.
- LLM execution happens in Python (Pre-execution) so API keys never enter Deno.
- Automatic retries on rate limits (429) are handled by the backend.
- Results are passed to Deno as prefetched outputs.

</domain>

<requirements>
## v1.9 Requirements (Traceability)

- **LLM-01**: Encrypted LLM Connection (URL, Key, Default Model).
- **LLM-02**: Separate System/User prompts with `{{payload.*}}` support.
- **LLM-03**: Configurable temperature and max_tokens.
- **LLM-04**: Automatic retries on 429 errors.

</requirements>

<code_context>
## Relevant Files

- `backend/app/models/models.py`: `DataSource` model (will use for LLM connections).
- `dashboard-app/src/constants/connectionTypes.js`: Register `llm` connection type.
- `backend/app/services/source_executor.py`: Add LLM pre-execution logic.
- `backend/app/runtime/runner.ts`: Ensure pre-executed LLM result is used.
- `backend/alembic/versions/`: Migration to register the `llm` tool.

</code_context>

<deferred>
## Deferred Ideas

- Streaming responses (v2).
- Multi-turn history (v2).
- JSON mode enforcement (v2).

</deferred>

---

*Phase: 40-llm-node*
*Context gathered: 2026-05-31*
