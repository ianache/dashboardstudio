---
plan: 50-01
phase: 50
status: complete
completed: 2026-06-01
---

## Summary

Refactored the ai-analyst service to be model-agnostic: installed LiteLLM, replaced the module-level `root_agent` singleton with a per-request `create_runner()` factory, added a `GET /models` endpoint driven by API key presence, and updated `POST /chat` to route to the correct model with per-provider cost calculation.

## Key Files

### Modified
- `ai-analyst/pyproject.toml` — litellm>=1.83.7,<=1.83.14 added
- `ai-analyst/app/core/config.py` — deepseek_api_key field added to Settings
- `ai-analyst/app/agent.py` — create_runner() factory replaces module-level runner singleton
- `ai-analyst/app/main.py` — GET /models endpoint; ChatRequest model/deepseek_api_key fields; cost tracking in usage SSE event

## Decisions

- Used LiteLlm constructor api_key parameter instead of os.environ to avoid race conditions in async context
- stream_options={"include_usage": True} required for DeepSeek usage metadata population
- GET /models returns all 3 models always, with enabled:false + disabled_reason when key absent — better UX than hiding disabled models

## Self-Check: PASSED
