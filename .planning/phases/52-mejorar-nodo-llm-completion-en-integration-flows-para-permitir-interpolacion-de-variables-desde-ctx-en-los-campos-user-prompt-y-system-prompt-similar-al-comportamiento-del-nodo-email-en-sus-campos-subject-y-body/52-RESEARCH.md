# Phase 52: LLM Completion ctx Variable Interpolation - Research

**Researched:** 2026-06-05
**Domain:** Python Jinja2 template rendering (FastAPI service) + Vue 3 UI hint injection
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Variables disponibles en ctx:** `{ payload, variables }` — mismo que usa `user_prompt` actualmente. `{{ payload }}`, `{{ payload[0].campo }}`, `{{ variables.nombre }}`. NO se agregan aliases ni conveniencias adicionales.
- **Comportamiento ante errores de template:** Errores de sintaxis → fallar el nodo con mensaje de error claro (igual al comportamiento actual de user_prompt). Variables inexistentes → silencio (string vacío, comportamiento default de Jinja2, NO activar StrictUndefined).
- **Hints en el UI:** Un hint debajo de cada textarea — uno bajo `user_prompt` y otro bajo `system_prompt`. Mismo CSS `.fec-template-hint`. Texto: `Usa {{ payload.campo }} y {{ variables.nombre }}. Soporta filtros Jinja2 como | tojson`. Condición `v-if`: cuando `selectedNode.toolType === 'llm'` Y key sea `user_prompt` o `system_prompt`.
- **Alcance por campo:** `user_prompt` — SOLO agregar hint en UI (backend ya funciona, no tocar). `system_prompt` — agregar rendering Jinja2 en `llm_executor.py` + hint en UI.
- **Capa de rendering:** Python (`llm_executor.py`), NOT Deno runner.

### Claude's Discretion

- Orden exacto del rendering en llm_executor.py (renderizar system_prompt antes o después de user_prompt — ambos con el mismo ctx).

### Deferred Ideas (OUT OF SCOPE)

- None — la discusión se mantuvo dentro del alcance de la fase.
</user_constraints>

---

## Summary

This phase is a minimal, surgical change with two independent touch points: one in the Python backend (`llm_executor.py`) and one in the Vue component (`FlowEditorCanvas.vue`). The domain is already mastered in both layers — Jinja2 is already imported and used for `user_prompt` rendering; the `.fec-template-hint` CSS class already exists with the exact style needed.

The backend change adds exactly one Jinja2 rendering block for `system_prompt`, cloned from the `user_prompt` block on lines 30-41 of `llm_executor.py`. The context shape is identical: `{"payload": ..., "data": ..., "variables": {}}`. The only ordering decision (Claude's discretion) is whether to render `system_prompt` before or after `user_prompt` — since both use the same context snapshot taken at execution time, order has no semantic impact; rendering `system_prompt` first (before `user_prompt`) is conventional and keeps the messages array order (system → user) as the code order.

The UI change adds two `<p v-if>` hint elements in `FlowEditorCanvas.vue` near lines 716-723, where the Email node hints already live. The condition pattern is directly analogous to the Email node pattern already present in the template.

**Primary recommendation:** Clone the `user_prompt` Jinja2 rendering block for `system_prompt` in `llm_executor.py`, then add two `v-if` hint `<p>` tags in `FlowEditorCanvas.vue` matching the existing `.fec-template-hint` pattern.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jinja2 | Already installed (in `llm_executor.py` imports) | Template rendering in Python | Already used for `user_prompt`; no new dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Vue 3 `v-if` directive | ^3.4 (already in project) | Conditional UI hint rendering | Exact same mechanism as existing Email hints |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 (Python) | Nunjucks (Deno) | Email uses Nunjucks in runner.ts — NOT applicable here; LLM is pre-executed by Python, completely different execution path |
| Default undefined behavior | StrictUndefined | StrictUndefined would raise on missing vars; decision is to keep silent empty string behavior |

**Installation:** None required — no new dependencies.

---

## Architecture Patterns

### Existing Code Layout (Touch Points Only)

```
backend/app/services/
└── llm_executor.py         # Line 22: system_prompt read; Line 30-41: user_prompt Jinja2 block
                            # ADD: system_prompt Jinja2 block after line 22, before line 30

dashboard-app/src/components/editor/
└── FlowEditorCanvas.vue    # Lines 716-723: Email hints
                            # ADD: two <p v-if> hints for LLM fields after line 723
                            # Lines 2838-2855: .fec-template-hint CSS (no change needed)
```

### Pattern 1: Jinja2 system_prompt rendering (Python)

**What:** Render `system_prompt` as a Jinja2 template using the same context as `user_prompt`.
**When to use:** After reading `system_prompt` from props, before building the LLM payload.
**Example:**

```python
# Source: direct read of llm_executor.py lines 22 and 30-41

# EXISTING (line 22) — do not change:
system_prompt = props.get("system_prompt") or "You are a helpful assistant."

# ADD THIS BLOCK immediately after line 22, before the "# 1. Render User Prompt" comment:
# 1a. Render System Prompt using Jinja2
try:
    if isinstance(ctx, dict) and "payload" in ctx:
        context = ctx
    else:
        context = {"payload": ctx, "data": ctx, "variables": {}}
    system_prompt = jinja2.Template(system_prompt).render(context)
except Exception as e:
    return {"success": False, "error": f"Failed to render system prompt: {str(e)}"}

# EXISTING block (lines 30-41) — do not change:
# 1. Render User Prompt using Jinja2
try:
    if isinstance(ctx, dict) and "payload" in ctx:
        context = ctx
    else:
        context = {"payload": ctx, "data": ctx, "variables": {}}
    template = jinja2.Template(user_prompt_template)
    rendered_user_prompt = template.render(context)
except Exception as e:
    return {"success": False, "error": f"Failed to render user prompt: {str(e)}"}
```

**Note on ordering:** Rendering `system_prompt` before `user_prompt` is the right choice because:
1. It follows the messages array order (system comes before user)
2. Both use the same context snapshot — no dependency between the two renders
3. Keeps error messages distinguishable ("system prompt" vs "user prompt")

**Note on context duplication:** The context-building logic (`if isinstance(ctx, dict)...`) will be written twice. This is intentional per the SIMPLICITY FIRST directive — no premature refactoring. If deduplication is desired later, it can be extracted into a local variable before both blocks.

### Pattern 2: Vue UI hint injection

**What:** Add `<p v-if>` hints below the `user_prompt` and `system_prompt` textareas.
**When to use:** When `selectedNode.toolType === 'llm'` AND the key is `user_prompt` or `system_prompt`.

```html
<!-- Source: direct read of FlowEditorCanvas.vue lines 716-723 (Email pattern) -->

<!-- EXISTING Email hints (lines 716-723) — do not change: -->
<p v-if="key === 'subject'" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Supports {"{{"}variable_insert{"}}"} template syntax
</p>
<p v-if="def.type === 'textarea' && ['subject', 'body'].includes(key)" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Supports {"{{"}variable_insert{"}}"} and {"{%"} for {"%}"} template syntax
</p>

<!-- ADD AFTER line 723 (inside the same </div> closing the prop group): -->
<p v-if="selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Usa {"{{"}payload.campo{"}}"} y {"{{"}variables.nombre{"}}"}. Soporta filtros Jinja2 como | tojson
</p>
```

**Why one hint, not two:** Both fields show identical info, so a single `v-if` covering both keys is cleaner than two separate `<p>` elements. The condition `['user_prompt', 'system_prompt'].includes(key)` reads like the Email `['subject', 'body'].includes(key)` pattern exactly.

### Anti-Patterns to Avoid

- **Touching user_prompt rendering code:** The `user_prompt` Jinja2 block (lines 30-41) must NOT be modified. The decision is "ONLY add hint in UI for user_prompt." Any refactor of that block is out of scope.
- **Using Nunjucks or runner.ts:** The Email node uses Nunjucks in Deno. LLM is Python-layer. Never route system_prompt rendering through Deno.
- **Adding StrictUndefined to the Jinja2 environment:** Decision is to use default behavior (missing vars → empty string). Do NOT add `jinja2.StrictUndefined`.
- **Creating a shared context helper function:** SIMPLICITY FIRST — the context-building is 3 lines and written twice. No abstraction needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template rendering | Custom string interpolation with `.replace()` | `jinja2.Template().render()` | Already present in the file; handles edge cases, filters, loops |
| UI hint styling | New CSS class | `.fec-template-hint` (lines 2838-2855) | Already defined, already themed with `var(--primary)` tokens |

**Key insight:** Both the Jinja2 rendering pattern and the UI hint CSS are already in place. This phase is pure clone-and-adapt, not design.

---

## Common Pitfalls

### Pitfall 1: Context not passed correctly to system_prompt render
**What goes wrong:** `system_prompt` renders with empty context because `ctx` at line 22 hasn't been normalized yet (the normalization block is inside the user_prompt try/except lower down).
**Why it happens:** The context normalization (`if isinstance(ctx, dict) and "payload" in ctx`) is inside the `user_prompt` try block — it won't be shared with the new `system_prompt` block unless explicitly duplicated.
**How to avoid:** Write the full context check inline in the new `system_prompt` block (same 3-line pattern). Do not assume the `context` variable exists from a previous block.
**Warning signs:** `{{ payload }}` renders as empty string in system_prompt even when payload has data.

### Pitfall 2: v-if condition renders hint on wrong node type
**What goes wrong:** The hint appears on ALL textarea fields across all node types because `['user_prompt', 'system_prompt'].includes(key)` could theoretically match prop keys with the same names on other tools.
**Why it happens:** The `key` variable is scoped to the current prop loop, not node type.
**How to avoid:** ALWAYS include `selectedNode.toolType === 'llm'` in the condition — already specified in the locked decisions. The full condition is `selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)`.
**Warning signs:** Template hints appear on non-LLM nodes that happen to have a prop named `user_prompt`.

### Pitfall 3: Vue template curly brace escaping
**What goes wrong:** `{{ payload.campo }}` in a Vue template causes a runtime error because Vue interprets double-curly-braces as its own interpolation syntax.
**Why it happens:** The existing Email hints already work around this with the `{"{{"}variable_insert{"}}"}` escape pattern (Vue's way to output literal `{{` and `}}`).
**How to avoid:** Use the same escape pattern already present in lines 717-722. The hint text `{"{{"}payload.campo{"}}"}` renders as literal `{{ payload.campo }}` in the browser.
**Warning signs:** Vue compilation warning about "interpolation inside attributes" or unexpected text in the rendered hint.

### Pitfall 4: Ordering of system_prompt render vs context variable
**What goes wrong:** A refactor attempt defines `context` once before both renders, but the variable is named `context` — which collides with the existing `context` variable name inside the `user_prompt` try block.
**Why it happens:** Python `try` blocks don't create a new scope, so a `context` variable defined before both blocks is accessible inside them. But if the `user_prompt` block also defines `context`, the outer one is overwritten.
**How to avoid:** Keep the two rendering blocks fully self-contained (copy the 3-line context check into each). This is the safest approach given the "surgical changes" directive.

---

## Code Examples

Verified patterns from the actual codebase:

### Current state of llm_executor.py (lines 22-41)
```python
# Source: backend/app/services/llm_executor.py (read 2026-06-05)
system_prompt = props.get("system_prompt") or "You are a helpful assistant."
user_prompt_template = props.get("user_prompt") or "{{payload}}"
temperature = float(props.get("temperature", 0.7))
max_tokens = int(props.get("max_tokens", 1024))

if not url:
    return {"success": False, "error": "LLM Connection has no URL configured"}

# 1. Render User Prompt using Jinja2
try:
    if isinstance(ctx, dict) and "payload" in ctx:
        context = ctx
    else:
        context = {"payload": ctx, "data": ctx, "variables": {}}
        
    template = jinja2.Template(user_prompt_template)
    rendered_user_prompt = template.render(context)
except Exception as e:
    return {"success": False, "error": f"Failed to render user prompt: {str(e)}"}
```

### Target state after change (backend)
```python
# Source: designed from llm_executor.py pattern (2026-06-05)
system_prompt_template = props.get("system_prompt") or "You are a helpful assistant."
user_prompt_template = props.get("user_prompt") or "{{payload}}"
temperature = float(props.get("temperature", 0.7))
max_tokens = int(props.get("max_tokens", 1024))

if not url:
    return {"success": False, "error": "LLM Connection has no URL configured"}

# 1a. Render System Prompt using Jinja2
try:
    if isinstance(ctx, dict) and "payload" in ctx:
        context = ctx
    else:
        context = {"payload": ctx, "data": ctx, "variables": {}}
    rendered_system_prompt = jinja2.Template(system_prompt_template).render(context)
except Exception as e:
    return {"success": False, "error": f"Failed to render system prompt: {str(e)}"}

# 1b. Render User Prompt using Jinja2
try:
    if isinstance(ctx, dict) and "payload" in ctx:
        context = ctx
    else:
        context = {"payload": ctx, "data": ctx, "variables": {}}
    template = jinja2.Template(user_prompt_template)
    rendered_user_prompt = template.render(context)
except Exception as e:
    return {"success": False, "error": f"Failed to render user prompt: {str(e)}"}
```

**Downstream in the same function** — update line 54 to use `rendered_system_prompt`:
```python
# Line 54 before: {"role": "system", "content": system_prompt},
# Line 54 after:
{"role": "system", "content": rendered_system_prompt},
```

### Email hint pattern (existing, lines 716-723 — reference only)
```html
<!-- Source: FlowEditorCanvas.vue lines 716-723 (read 2026-06-05) -->
<p v-if="key === 'subject'" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Supports {"{{"}variable_insert{"}}"} template syntax
</p>
<p v-if="def.type === 'textarea' && ['subject', 'body'].includes(key)" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Supports {"{{"}variable_insert{"}}"} and {"{%"} for {"%}"} template syntax
</p>
```

### New LLM hint (to add after line 723)
```html
<!-- Source: designed from Email pattern above (2026-06-05) -->
<p v-if="selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)" class="fec-template-hint">
  <span class="msi" style="font-size:11px">info</span>
  Usa {"{{"}payload.campo{"}}"} y {"{{"}variables.nombre{"}}"}. Soporta filtros Jinja2 como | tojson
</p>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `system_prompt` used as raw string | `system_prompt` rendered as Jinja2 template | Phase 52 (this phase) | Unlocks dynamic system prompts using flow ctx |
| No UI hint on LLM textarea fields | `.fec-template-hint` shown below each textarea | Phase 52 (this phase) | Users discover the feature without docs |

**Deprecated/outdated:**
- None — no existing code is being replaced, only extended.

---

## Open Questions

1. **Variable name: `system_prompt` vs `system_prompt_template`**
   - What we know: The current code uses `system_prompt = props.get(...)` and passes it directly to the payload. After the change, the raw value becomes a template that needs rendering.
   - What's unclear: Whether to rename the variable to `system_prompt_template` for clarity (as shown in the target code above) or keep it as `system_prompt` and overwrite it with the rendered result.
   - Recommendation: Rename to `system_prompt_template` on line 22 and use `rendered_system_prompt` as the output variable name — matches the `user_prompt_template` / `rendered_user_prompt` pattern already in the file. This is clean and consistent at zero extra cost.

---

## Sources

### Primary (HIGH confidence)
- Direct read of `backend/app/services/llm_executor.py` — full file, confirmed Jinja2 already imported, user_prompt pattern verified
- Direct read of `dashboard-app/src/components/editor/FlowEditorCanvas.vue` — lines 700-780 (template hints area) and lines 2834-2856 (CSS definition)
- Direct read of `backend/alembic/versions/035_add_llm_tool.py` — confirms `system_prompt` and `user_prompt` are both `type: "textarea"` fields in the LLM tool's `prop_defs`
- Direct read of `backend/app/services/source_executor.py` — confirms ctx passed to `execute_llm_node` is `{"payload": input_payload, "variables": flow_data.get("variables", {})}` (lines 351-352)

### Secondary (MEDIUM confidence)
- Direct read of `backend/app/runtime/runner.ts` lines 225-265 — Email node reference confirms Nunjucks-based rendering is in Deno, NOT applicable to LLM node

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Jinja2 and Vue 3 already in place; verified from source files
- Architecture: HIGH — exact line numbers verified by direct file reads
- Pitfalls: HIGH — derived from actual code structure, not speculation

**Research date:** 2026-06-05
**Valid until:** 2026-07-05 (stable codebase; these files change infrequently)
