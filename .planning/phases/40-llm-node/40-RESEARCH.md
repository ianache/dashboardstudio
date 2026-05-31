# Phase 40: LLM Node - Research

**Researched:** 2026-05-31
**Domain:** LLM Integration + Secure Pre-execution
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `toolType`: `llm`, `category`: `source` (as it's pre-executed) or `transform` (if we handle it in-runner, but roadmap says pre-execution).
- Connection: Use standard `DataSource` with type `llm`.
- Security: API keys MUST NOT enter Deno runner.
- Logic: Implement in `pre_execute_flow_nodes` in Python.

### Claude's Discretion
- Prompt engine: Use `jinja2` (already in backend).
- Request library: Use `httpx` (already in backend).
- Retry logic: Implement simple loop with exponential backoff or use `tenacity`.

</user_constraints>

---

## Summary

Phase 40 implements the "Python pre-execution" pattern for LLM nodes. This pattern ensures that sensitive API keys are handled only by the FastAPI backend and never passed as plain-text props to the Deno sub-process.

### Flow Architecture
1. **Flow Preparation (Python)**: `integration_flows.py` calls `pre_execute_flow_nodes`.
2. **LLM Execution (Python)**: 
   - Python finds `llm` nodes.
   - It retrieves the `DataSource`, decrypts the `api_key`.
   - It renders the `user_prompt` using `jinja2` and the `initial_payload`.
   - It makes the HTTP call to the LLM endpoint (OpenAI compatible).
   - It stores the resulting text in `prefetched_outputs[node_id]`.
   - It marks the node as `__pre_executed: true`.
3. **Runner (Deno)**: 
   - `runner.ts` sees the node is pre-executed.
   - It grabs the result from `prefetched_outputs`.
   - It continues execution normally.

This architecture limits LLM nodes to only use data from the **initial flow payload**, which is acceptable for v1.9 and satisfies `LLM-02`.

---

## Implementation Details

### 1. DataSource Registration
Update `dashboard-app/src/constants/connectionTypes.js`:
```javascript
{ value: 'llm', label: 'LLM (OpenAI Compatible)' }
// Defaults
llm: { url: 'https://api.openai.com/v1', api_key: '', model: 'gpt-4o' }
```

### 2. Alembic Migration
Add `035_add_llm_tool.py`:
```python
prop_defs = {
    "connection_id": { "label": "Connection", "type": "connection", "connection_type": "llm" },
    "system_prompt": { "label": "System Prompt", "type": "textarea" },
    "user_prompt": { "label": "User Prompt", "type": "textarea" },
    "temperature": { "label": "Temperature", "type": "number", "default": 0.7 },
    "max_tokens": { "label": "Max Tokens", "type": "number", "default": 1024 }
}
```

### 3. Python LLM Client
In `app/services/llm_executor.py` (New):
```python
async def execute_llm(props: dict, payload: dict) -> str:
    # 1. Resolve prompt
    template = jinja2.Template(props['user_prompt'])
    prompt = template.render(payload=payload)
    
    # 2. Call API
    async with httpx.AsyncClient() as client:
        # Implement retry loop for 429
        # ...
```

### 4. Runner Update
`runner.ts` already handles `__pre_executed` nodes. No changes needed to the main loop, only ensure the `llm` tool is registered in the DB.

---

## Common Pitfalls

### Pitfall 1: Timeouts
**Risk:** LLM calls can take 10-30s, potentially timing out the WebSocket or the `subprocess.run` (120s limit).
**Mitigation:** Set reasonable timeouts in `httpx` and monitor performance.

### Pitfall 2: Memory/Payload Size
**Risk:** LLM output might be large.
**Mitigation:** Same as `data_transform`, Deno handles it once it's in `prefetched_outputs`.

### Pitfall 3: Prompt Syntax
**Risk:** `jinja2` uses `{{ }}` which might conflict if the user wants literal braces.
**Mitigation:** Standard `jinja2` behavior; user can use `{% raw %}` if needed.

---

## Sources
- `source_executor.py` logic for pre-execution.
- `llm_config.py` for encryption patterns.
- OpenAI API documentation for 429 retry headers.
