# Phase 39: Templating Node - Research

**Researched:** 2026-05-31
**Domain:** Deno runner extension + Python preview API + Vue UI enhancement
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `toolType`: `nunjucks_template`, `category`: `transform`
- Editor: `CodeEditor` (Monaco) with `language: 'jinja2'`
- Property panel: Special-cased "Preview" block (Sample JSON + Preview Button + Result)
- Preview Backend: `POST /api/v1/tools/template-preview` using Python Jinja2
- Runtime Engine: `npm:nunjucks` in Deno
- Error format: `[Template Error] NodeLabel: ErrorMessage`
- Migration: `034_add_nunjucks_template_tool.py`

### Claude's Discretion
- Placeholder for template: `Hello {{ name }}!`
- UI placement of Preview block: Stacks below standard properties

### Deferred Ideas
- None
</user_constraints>

---

## Summary

Phase 39 introduces a dedicated templating node. While the Email node already has internal templating, this node makes templating an explicit, previewable step that produces a string payload. 

The implementation spans the full stack:
1. **DB**: New tool definition with a `code` property.
2. **Backend (Python)**: A utility endpoint to render Jinja2 strings for the UI preview.
3. **Frontend (Vue)**: A custom UI block in `FlowEditorCanvas.vue` for the preview interaction.
4. **Runner (Deno)**: Integration of `nunjucks` npm package to render the template during flow execution.

**Key discovery:** Deno's `npm:nunjucks` is straightforward. The Nunjucks `renderString` method matches Jinja2's `render` well enough for the intended use cases.

---

## Standard Stack

### Core
| Library / File | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| `nunjucks` | `npm:nunjucks` | Template rendering in Deno | Industry standard JS templating, Jinja2-compatible |
| `jinja2` | current | Template rendering for UI preview | Existing backend dependency |
| `FastAPI` | current | Preview API endpoint | Project standard |

### Supporting
| File | Purpose | When to Use |
|------|---------|-------------|
| `FlowEditorCanvas.vue` | UI for the property panel | Add the preview block here |
| `033_add_data_transform_tool.py` | Migration template | Base the new migration on this |

---

## Architecture Patterns

### Pattern 1: Nunjucks in Deno Runner
```typescript
import nunjucks from "npm:nunjucks";

// ... in runNodeExecution
} else if (node.toolType === 'nunjucks_template' && node.props?.template) {
  try {
    const inputPayload = context.payload;
    // Configure nunjucks to not escape (we're producing a string, not HTML usually, 
    // and if we are, the downstream node handles it)
    nunjucks.configure({ autoescape: false });
    const rendered = nunjucks.renderString(node.props.template, inputPayload);
    context.payload = rendered;
    // ... logging and emitStatus
  } catch (err: any) {
    console.error(`[Template Error] ${node.label}: ${err.message}`);
    // ... error logging and exit
  }
```

### Pattern 2: Python Preview Endpoint
```python
@router.post("/tools/template-preview")
async def template_preview(
    request: TemplatePreviewRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        from jinja2 import Environment, meta
        env = Environment()
        template = env.from_string(request.template)
        rendered = template.render(request.data)
        return {"rendered": rendered}
    except Exception as e:
        return {"error": str(e)}
```

---

## Common Pitfalls

### Pitfall 1: Autoescaping in Nunjucks
**What goes wrong:** Nunjucks might escape `&` as `&amp;` by default if not configured.
**How to avoid:** Set `autoescape: false` in `nunjucks.configure`.

### Pitfall 2: Python/JS Syntax Mismatches
**What goes wrong:** Some advanced Jinja2 filters might not exist in Nunjucks.
**How to avoid:** Document that preview is "best-effort compatibility". Most common filters (`| upper`, `| date`, etc.) work in both.

### Pitfall 3: UI Layout Shift
**What goes wrong:** The preview block might make the sidebar too long and non-scrollable.
**How to avoid:** Ensure the sidebar has `overflow-y: auto`.

---

## Code Examples

### Preview Block in FlowEditorCanvas.vue
```html
<div v-if="selectedNode.toolType === 'nunjucks_template'" class="fec-preview-block">
  <div class="fec-prop-label">Sample Data (JSON)</div>
  <textarea v-model="previewDataJson" class="fec-preview-json"></textarea>
  <button @click="runPreview" :disabled="previewLoading">Preview</button>
  <div class="fec-preview-result">
    <div class="fec-prop-label">Rendered Result</div>
    <pre>{{ previewResult }}</pre>
  </div>
</div>
```

---

## Sources
- `EmailExecutor.py` confirmed Jinja2 usage.
- `FlowEditorCanvas.vue` confirmed property loop structure.
- Deno `npm:` documentation for Nunjucks import.
