# Phase 38: Data Transform Node - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `data_transform` node that reshapes, filters, or maps the flow payload using a JavaScript function body. Simpler than the Script node — no top-level ESM imports, just a function body that receives `data` (the payload) and `ctx` (the full context). Pure Deno addition — no Python backend changes required.

</domain>

<decisions>
## Implementation Decisions

### Function signature
- User writes a function body (not a full module) — runner wraps it as: `async function(data, ctx) { <user code> }`
- `data` is the payload shortcut; `ctx` is the full context object (includes `ctx.variables`, `ctx.payload`)
- Async/await is allowed — reuses `executeScriptNode()` as-is, no synchronous restriction
- Default code template: `return data;` — minimal pass-through showing the signature

### Property panel
- Label: `Transform Function`
- Placeholder: `// receives data (payload) and ctx (context)\nreturn data;`
- Code editor uses `language: 'javascript'` via existing `CodeEditor.vue`

### Simplicity boundary
- No top-level ESM `import` statements — detect and reject with a clear error message
- Dynamic `import()` calls inside the function body are allowed (async is on)
- `ctx.variables` available via `ctx` — comes for free from the function signature
- `toolType` string: `data_transform`
- Category: `transform` (matches existing `CAT_META.transform`)

### Warning behavior (>10,000 rows)
- Check performed BEFORE running the function — on the input payload
- Condition: `Array.isArray(data) && data.length > 10000`
- Output to ExecutionConsole only (zero frontend changes) — flow continues normally
- Message format: `[Transform Warning] Input has N rows (>10,000). Large payloads may be slow.`

### Error presentation
- Uses existing red node state + ExecutionConsole log — no new frontend indicators
- Error format: `[Transform Error] NodeLabel: ErrorType: ErrorMessage`
- Log entry includes error type + message only (no stack trace)
- Follows the `[HTTP Error]`, `[ODS Error]`, `[Join Error]` naming convention

</decisions>

<specifics>
## Specific Ideas

- The node is intentionally a "lite Script node" — if you need imports or full module-level code, use the Script node
- The `[Transform Warning]` prefix is deliberately different from `[Transform Error]` so users can scan the console quickly
- No new DB tables, no Python services, no frontend component changes — this is purely runner.ts + one Alembic migration

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CodeEditor.vue` — Monaco editor already used by Script node; reusable as-is for the property panel
- `executeScriptNode()` in `runner.ts:65` — existing JS execution engine; Data Transform reuses it with a modified wrapper (`async function(data, ctx)` instead of `async function(ctx)`)
- `js_script` handler in `runner.ts:412` — the near-identical execution pattern to copy for `data_transform`
- Migration `010_add_js_script_tool.py` — exact pattern to follow for the new `editor_tools` DB entry

### Established Patterns
- Tool definition lives in `biportal.editor_tools` table with `type`, `prop_defs` (JSON), `default_props` (JSON), `category`
- `prop_defs` schema: `{ code: { label, type: 'code', language, placeholder } }` — drives the property panel with no frontend changes needed
- Node execution: write result to `context.payload`, emit `NODE_LOG_JSON:` signal, `emitStatus(node.id, 'success'|'error')`
- Node error path: emit `NODE_LOG_JSON` with status=error, `console.error(...)`, `emitStatus(node.id, 'error')`, `Deno.exit(1)`
- Last Alembic migration: `032_add_email_tool.py` — next migration should be `033_add_data_transform_tool.py`

### Integration Points
- `runner.ts` — add `else if (node.toolType === 'data_transform')` branch after the `js_script` block (~line 427)
- New Alembic migration `033_add_data_transform_tool.py` — inserts row into `biportal.editor_tools`
- No changes to `deno_service.py`, `main.py`, frontend stores, or canvas components

</code_context>

<deferred>
## Deferred Ideas

- **Visual schema mapper node** — A dedicated future node type where the user specifies a source JSON schema and a target JSON schema, then visually connects fields via drag & drop in a panel. Features: value mapping between source/target fields, array iteration (process source array items to produce target array items), complex transformation operations. This is a major new capability and belongs in its own phase well after v1.9.

</deferred>

---

*Phase: 38-data-transform-node*
*Context gathered: 2026-05-31*
