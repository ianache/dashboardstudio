# Phase 39: Templating Node - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `nunjucks_template` node that renders a Jinja2/Nunjucks template string against the flow payload and outputs a plain text string. Includes a live Preview panel (sample JSON → rendered output) in the property panel without running the full flow. Designed as the natural predecessor to the Email node.

</domain>

<decisions>
## Implementation Decisions

### Template editor UI
- Use `CodeEditor` component (Monaco), NOT a plain textarea
- Monaco language: `jinja2` (closest available language for Nunjucks syntax highlighting)
- Default template: empty string (Claude's discretion for placeholder text)
- Property panel label: Claude's discretion (e.g., "Template")

### Preview panel
- Always visible below the template editor — no collapse toggle
- Three elements stacked: (1) sample JSON textarea, (2) Preview button, (3) rendered output display area
- Preview panel is special-cased in `FlowEditorCanvas.vue` with `v-if="selectedNode.toolType === 'nunjucks_template'"`
- Not driven by prop_defs — it's a custom UI block added directly in the canvas component

### Preview rendering
- Backend API: new FastAPI endpoint `POST /api/v1/tools/template-preview`
- Accepts: `{ template: string, data: object }`
- Returns: `{ rendered: string }` on success, `{ error: string }` on failure
- Uses Python's Jinja2 (already installed — zero new dependencies)
- Preview endpoint requires auth (same `Depends(get_current_user)` pattern)

### Template syntax
- Full Jinja2/Nunjucks syntax supported: `{% for item in items %}`, `{% if cond %}`, filters like `| upper`, `| default('N/A')`
- Runtime rendering (flow execution) done in Deno via `import nunjucks from "npm:nunjucks"`
- Preview rendering done in Python via Jinja2 (syntax-compatible for common cases)

### Runtime behavior
- `toolType`: `nunjucks_template`, category: `transform`
- `context.payload` becomes a plain string after the node executes
- Downstream Email node uses `{{payload}}` in its body field to consume the rendered string — no special wiring needed
- On template render error: fail flow with `[Template Error] NodeLabel: ErrorMessage`, red node state

</decisions>

<specifics>
## Specific Ideas

- Preview and runtime use different engines (Jinja2 vs Nunjucks) but are syntax-compatible for the common cases — acceptable trade-off documented so users know preview is approximate
- The natural use case is: Source → Templating → Email. The Email body field just holds `{{payload}}`.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CodeEditor.vue` — Monaco editor; reuse with `language="jinja2"` for syntax highlighting
- Python Jinja2 — already in backend dependencies; use `Environment(undefined=Undefined).from_string(template).render(data)` for the preview endpoint
- `Depends(get_current_user)` — use for the new preview endpoint
- Migration pattern from `033_add_data_transform_tool.py` — copy for `034_add_nunjucks_template_tool.py`

### Established Patterns
- `type: 'code'` in prop_defs → CodeEditor renders automatically in the property panel
- Email node body uses `resolveString(props.body, context)` — `{{payload}}` in Email body resolves to the string context.payload naturally
- runner.ts `else if` branch after `data_transform` block — add `nunjucks_template` branch here
- Deno can import npm packages: `import nunjucks from "npm:nunjucks"` (no separate install needed)

### Integration Points
- `FlowEditorCanvas.vue`: add special-case preview UI block after the standard `visiblePropDefs` loop for `nunjucks_template` toolType
- `backend/app/api/endpoints/` — add new file `template_tools.py` or add to `editor_tools.py` for the preview endpoint
- `backend/app/api/router.py` — register the new endpoint
- `runner.ts` — new `else if (node.toolType === 'nunjucks_template')` branch

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 39-templating-node*
*Context gathered: 2026-05-31*
