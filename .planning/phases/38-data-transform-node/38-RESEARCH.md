# Phase 38: Data Transform Node - Research

**Researched:** 2026-05-31
**Domain:** Deno runner extension + Alembic migration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `toolType`: `data_transform`, `category`: `transform`
- Function signature: user writes a function body; runner wraps it as `async function(data, ctx) { <user code> }`
- `data` is the payload shortcut; `ctx` is the full context object (`ctx.variables`, `ctx.payload`)
- Async/await is allowed — reuses `executeScriptNode()` as-is, no synchronous restriction
- Default code template: `return data;`
- Property panel label: `Transform Function`
- Placeholder: `// receives data (payload) and ctx (context)\nreturn data;`
- Code editor uses `language: 'javascript'` via existing `CodeEditor.vue`
- No top-level ESM `import` statements — detect and reject with a clear error message
- Dynamic `import()` calls inside the function body are allowed
- Warning at `>10,000 rows` — condition: `Array.isArray(data) && data.length > 10000`
- Warning to ExecutionConsole only (zero frontend changes) — flow continues normally
- Warning message: `[Transform Warning] Input has N rows (>10,000). Large payloads may be slow.`
- Error format: `[Transform Error] NodeLabel: ErrorType: ErrorMessage`
- Uses existing red node state + ExecutionConsole log — no new frontend indicators
- Next migration: `033_add_data_transform_tool.py`
- Pure Deno addition — no Python backend changes

### Claude's Discretion
- None specified — all decisions are locked

### Deferred Ideas (OUT OF SCOPE)
- Visual schema mapper node with drag-and-drop field mapping — a future phase after v1.9
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRANS-01 | User can add a Data Transform node with a JS function body (CodeEditor) that receives `data` and returns the transformed payload | Covered by: DB migration inserting `editor_tools` row with `prop_defs.code` of type `code`; runner.ts `data_transform` branch using `executeScriptNode()` with wrapped signature |
| TRANS-02 | A warning appears in the execution console when the transform input payload exceeds 10,000 rows | Covered by: pre-execution array length check in the `data_transform` runner branch; `console.error()` or `console.log()` output visible in ExecutionConsole |
</phase_requirements>

---

## Summary

Phase 38 is the smallest possible new node type addition in this codebase. The two deliverables are:
1. A single Alembic migration (`033_add_data_transform_tool.py`) that inserts one row into `biportal.editor_tools`.
2. A new `else if (node.toolType === 'data_transform')` branch in `runner.ts:runNodeExecution()`, inserted after the `js_script` block at line 427.

No frontend code changes are required. The existing `prop_defs` rendering pipeline in `FlowEditorCanvas.vue` already handles `type: 'code'` fields (line 578–585). The existing `CodeEditor.vue` renders Monaco with `language: 'javascript'`. The `CAT_META.transform` category is already defined in `toolCatalog.js`.

The only design subtlety is the function wrapper: `js_script` uses `async function(ctx)` while `data_transform` must use `async function(data, ctx)`. `executeScriptNode()` always passes a single `context` argument to `mod.default`. The wrapper must therefore be written so that `data = context.payload` before calling the user function. The cleanest approach is to construct a thin function body wrapper that does NOT go through `executeScriptNode()` module-wrapping path, or to pass `data` via a modified context. The concrete pattern is described in Code Examples below.

**Primary recommendation:** Add the `data_transform` handler directly in `runner.ts` after `js_script`. Use a local wrapper function that builds `async function(data, ctx) { <code> }` as a base64 data URI module, then calls it as `mod.default(context.payload, context)`. This mirrors `executeScriptNode()` exactly but with the two-argument signature. No refactoring of `executeScriptNode` is needed.

---

## Standard Stack

### Core
| Library / File | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| `backend/app/runtime/runner.ts` | current | Deno flow executor — add new node branch here | Only execution engine in this project |
| `biportal.editor_tools` (PostgreSQL) | — | Tool registry consumed by frontend `toolCatalog` store | All node types live here; frontend is fully data-driven |
| Alembic (`backend/alembic/versions/`) | current | Schema/data migrations | Project convention — always use Alembic, never manual DB edits |

### Supporting
| File | Purpose | When to Use |
|------|---------|-------------|
| `executeScriptNode()` (runner.ts:65) | Base64 module loader for JS execution | Can be called directly OR the two-argument variant can be implemented inline |
| `CodeEditor.vue` | Monaco editor component | Already invoked automatically for any `prop_defs` field with `type: 'code'` |
| `FlowEditorCanvas.vue` (line 578–585) | Renders `code`-type prop as `<CodeEditor>` | Zero changes needed — it already handles `type: 'code'` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline wrapper in `data_transform` branch | Refactor `executeScriptNode()` to accept signature config | Refactoring is unnecessary complexity for this phase; inline is surgical |
| `executeScriptNode(wrappedCode, ...)` | Call `executeScriptNode` after manually prepending the outer signature | Works but wrapping code is cleaner and self-contained in the branch |

**Installation:** No new packages. No npm installs. No pip installs.

---

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── alembic/versions/
│   └── 033_add_data_transform_tool.py   ← NEW: inserts editor_tools row
└── app/runtime/
    └── runner.ts                          ← MODIFIED: add data_transform branch (~line 427)
```

No other files change.

### Pattern 1: Node Branch in runNodeExecution()
**What:** Every node type is a `else if (node.toolType === '...')` block inside `runNodeExecution()`.
**When to use:** All new Deno-native node types follow this pattern.
**Example:**
```typescript
// Insert after line 426 (closing brace of js_script block), before csv_file block
} else if (node.toolType === 'data_transform' && node.props?.code) {
  try {
    const inputPayload = context.payload;
    const data = inputPayload;

    // Detect top-level ESM import (not dynamic import() calls)
    const codeWithoutComments = node.props.code.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '').trim();
    const hasTopLevelImport = /^\s*import\s+/m.test(codeWithoutComments);
    if (hasTopLevelImport) {
      throw new TypeError(
        "Top-level import statements are not allowed in Data Transform. Use dynamic import() instead."
      );
    }

    // Large payload warning (TRANS-02)
    if (Array.isArray(data) && data.length > 10000) {
      console.log(`[Transform Warning] Input has ${data.length} rows (>10,000). Large payloads may be slow.`);
    }

    // Wrap user code as two-argument async function and execute
    const moduleContent = `export default async function(data, ctx) {\n${node.props.code}\n}`;
    const base64 = btoa(unescape(encodeURIComponent(moduleContent)));
    const dataUri = `data:text/javascript;base64,${base64}`;
    const mod = await import(dataUri);
    context.payload = await mod.default(data, context);

    const endMs = Date.now();
    const endTime = new Date(endMs).toISOString();
    console.log(`NODE_LOG_JSON:${JSON.stringify({
      node_id: node.id, status: 'success',
      input: inputPayload, output: context.payload,
      duration: endMs - startMs, start_time: startTime, end_time: endTime
    })}`);
    emitStatus(node.id, 'success');
  } catch (err: any) {
    const endMs = Date.now();
    const endTime = new Date(endMs).toISOString();
    console.log(`NODE_LOG_JSON:${JSON.stringify({
      node_id: node.id, status: 'error',
      input: context.payload, output: {},
      duration: endMs - startMs, start_time: startTime, end_time: endTime
    })}`);
    console.error(`[Transform Error] ${node.label}: ${err.constructor.name}: ${err.message}`);
    emitStatus(node.id, 'error');
    Deno.exit(1);
  }
```

### Pattern 2: Alembic Migration for editor_tools
**What:** Insert a single row into `biportal.editor_tools` defining the node's type, category, prop_defs, and default_props.
**When to use:** Every new tool/node type needs this migration.
**Example:**
```python
# 033_add_data_transform_tool.py
# revision: '033'
# down_revision: '032'
# Based exactly on 010_add_js_script_tool.py pattern

op.bulk_insert(tools_table, [{
    'id': 'tool-data-transform-001',
    'type': 'data_transform',
    'name': 'Data Transform',
    'description': 'Reshapes, filters, or maps the flow payload using a JavaScript function body',
    'subtitle': 'Transform payload',
    'icon': 'transform',
    'category': 'transform',
    'applicable_diagram_types': ['data-integration', 'process-flow'],
    'prop_defs': {
        'code': {
            'label': 'Transform Function',
            'type': 'code',
            'language': 'javascript',
            'placeholder': '// receives data (payload) and ctx (context)\nreturn data;'
        }
    },
    'default_props': {
        'code': 'return data;'
    },
    'created_at': NOW,
    'updated_at': NOW,
}])
```

### Anti-Patterns to Avoid
- **Modifying `executeScriptNode()`:** The function was designed for `async function(ctx)` signature. Don't modify it. Build the two-argument wrapper inline in the `data_transform` branch.
- **Checking `import` after wrapping:** The top-level import check must run on the RAW user code (before wrapping), not on the module content string.
- **Stack trace in error message:** The error format `[Transform Error] NodeLabel: ErrorType: ErrorMessage` does NOT include the stack trace — see CONTEXT.md. Match `[HTTP Error]`, `[Join Error]`, etc. which only log `err.message`.
- **Frontend changes for this phase:** The property panel, toolCatalog, and canvas all work data-driven from the DB row. No Vue component edits are needed.
- **`prop_defs.code.language` field:** The `js_script` migration omits the `language` key from `prop_defs.code`. The `FlowEditorCanvas.vue` at line 581 does `def.language || 'javascript'` so it defaults correctly. However, to be explicit and match the CONTEXT.md decision, include `'language': 'javascript'` in the `data_transform` prop_def.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JS code execution in Deno | Custom eval/sandbox | `import()` on a base64 data URI | Already proven pattern in `executeScriptNode()` — Deno's native module system handles scope correctly |
| Monaco editor for the code field | New editor widget | `CodeEditor.vue` (already wired via `prop_defs`) | The `FlowEditorCanvas` already renders CodeEditor for any `type: 'code'` prop_def |
| Tool registration | Static frontend catalog | `biportal.editor_tools` DB row via Alembic | The `toolCatalog` Pinia store fetches from `/api/v1/editor-tools` — it is fully data-driven |

**Key insight:** Every piece of infrastructure this node needs already exists. The only new code is a 35-line runner branch and a 50-line Alembic migration.

---

## Common Pitfalls

### Pitfall 1: Error Message Format Divergence
**What goes wrong:** Logging `err.stack` or using a different prefix breaks the consistent `[Type Error]` convention.
**Why it happens:** The `js_script` error block (line 420–425) omits the `console.error` call entirely — it only emits NODE_LOG_JSON and Deno.exit(1). Data Transform DOES need a `console.error` with the formatted message for the ExecutionConsole.
**How to avoid:** Always emit: `console.error(\`[Transform Error] ${node.label}: ${err.constructor.name}: ${err.message}\`)` before `Deno.exit(1)`.
**Warning signs:** ExecutionConsole shows no error message when the transform fails.

### Pitfall 2: Top-Level Import Detection Fires on Dynamic Imports
**What goes wrong:** A regex like `/import\s+/m` catches `const x = await import('...')` and incorrectly rejects it.
**Why it happens:** The rule is "no top-level ESM `import` statements" but dynamic `import()` is allowed.
**How to avoid:** Use `/^\s*import\s+/m` — anchored to the start of a line, which catches `import {x} from 'y'` but not `await import(...)`. Also strip comments first (copy the pattern from `executeScriptNode()` line 84).
**Warning signs:** A flow with `const mod = await import('https://...')` inside a transform fails with "Top-level import statements are not allowed."

### Pitfall 3: User Returns Undefined
**What goes wrong:** User writes a transform that has no explicit `return` statement. `context.payload` becomes `undefined`, breaking downstream nodes.
**Why it happens:** `async function(data, ctx) { /* no return */ }` returns `undefined`.
**How to avoid:** After `mod.default(data, context)`, check: `if (result === undefined) { result = data; }` — pass through the input payload silently. This is a quality-of-life guard. Alternatively, document this clearly but let it fail explicitly (matching the "fail explicitly" principle in REQUIREMENTS.md).
**Warning signs:** Downstream nodes receive `null`/`undefined` payload when transform has no return.

### Pitfall 4: Alembic Revision Chain Mismatch
**What goes wrong:** Setting `down_revision = '032'` when the actual latest revision head is a different value.
**Why it happens:** Migration `032_add_email_tool.py` has `down_revision: Union[str, Sequence[str], None] = '202fd2be6265'` — meaning revision 032 itself descends from `202fd2be6265`, not from `011`. The chain is not sequential by filename.
**How to avoid:** Run `uv run alembic heads` to confirm the current head before writing `033`. The `033` migration's `down_revision` must be `'032'` (the string revision ID, which IS `'032'` per that file's `revision = '032'`).
**Warning signs:** `alembic upgrade head` fails with "Can't locate revision identified by '033'".

### Pitfall 5: `inputPayload` vs `context.payload` in Error Log
**What goes wrong:** The NODE_LOG_JSON `input` field in the error path logs `context.payload` (which may have been mutated) instead of `inputPayload` (the pre-transform snapshot).
**Why it happens:** The `js_script` error block uses `input: context.payload` — this was acceptable because the payload was not mutated before the error. Data Transform may partially mutate context before throwing.
**How to avoid:** Capture `const inputPayload = context.payload` before ANY mutation, then use `inputPayload` in both success and error NODE_LOG_JSON emissions.

---

## Code Examples

Verified patterns from codebase inspection:

### How FlowEditorCanvas renders code-type prop (FlowEditorCanvas.vue:578)
```html
<!-- Already in production — no change needed -->
<CodeEditor
  v-if="def.type === 'code'"
  v-model="selectedNode.props[key]"
  :language="def.language || 'javascript'"
  height="413px"
  @change="checkDirty"
  @update:model-value="checkDirty"
/>
```

### How js_script migration defines prop_defs (010_add_js_script_tool.py)
```python
'prop_defs': {
    'code': {
        'label': 'Código JS',
        'type': 'code',
        'placeholder': 'export default async function(ctx) { ... }'
    }
},
'default_props': {
    'code': 'export default async function(ctx) {\n  ...\n}'
},
```

### How executeScriptNode builds the base64 module (runner.ts:65–110)
```typescript
// The key mechanic — base64 data URI module import
const base64 = btoa(unescape(encodeURIComponent(moduleContent)));
const dataUri = `data:text/javascript;base64,${base64}`;
const mod = await import(dataUri);
if (typeof mod.default === 'function') {
  return await mod.default(context);   // <-- js_script passes full context
}
```
For `data_transform`, the last line changes to: `await mod.default(data, context)` where `data = context.payload`.

### Complete migration skeleton
```python
"""add data_transform tool

Revision ID: 033
Revises: 032
Create Date: 2026-05-31
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision: str = '033'
down_revision: Union[str, None] = '032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'
NOW = datetime.utcnow()

def upgrade() -> None:
    tools_table = sa.table(
        'editor_tools',
        sa.column('id', sa.String), sa.column('type', sa.String),
        sa.column('name', sa.String), sa.column('description', sa.Text),
        sa.column('subtitle', sa.String), sa.column('icon', sa.String),
        sa.column('category', sa.String),
        sa.column('applicable_diagram_types', sa.JSON),
        sa.column('prop_defs', sa.JSON), sa.column('default_props', sa.JSON),
        sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime),
        schema=SCHEMA,
    )
    op.bulk_insert(tools_table, [{
        'id': 'tool-data-transform-001',
        'type': 'data_transform',
        'name': 'Data Transform',
        'description': 'Reshapes, filters, or maps the flow payload using a JS function body',
        'subtitle': 'Transformar payload',
        'icon': 'transform',
        'category': 'transform',
        'applicable_diagram_types': ['data-integration', 'process-flow'],
        'prop_defs': {
            'code': {
                'label': 'Transform Function',
                'type': 'code',
                'language': 'javascript',
                'placeholder': '// receives data (payload) and ctx (context)\nreturn data;'
            }
        },
        'default_props': {
            'code': 'return data;'
        },
        'created_at': NOW,
        'updated_at': NOW,
    }])

def downgrade() -> None:
    op.execute(f"DELETE FROM {SCHEMA}.editor_tools WHERE type = 'data_transform'")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| js_script: user writes full module | data_transform: user writes function body | Phase 38 (new) | Simpler UX — no need for `export default async function(ctx)` boilerplate |
| js_script: `async function(ctx)` | data_transform: `async function(data, ctx)` | Phase 38 (new) | `data` shortcut makes transforms more ergonomic |

**No deprecated patterns apply to this phase.**

---

## Open Questions

1. **undefined return behavior**
   - What we know: If user writes `// some transform` with no `return`, `mod.default()` returns `undefined`.
   - What's unclear: Should we silently pass through the original payload, or let `undefined` propagate?
   - Recommendation: Silently pass through `data` when result is `undefined` (matches the "lite script" intent). Add: `context.payload = (result !== undefined) ? result : data;`

2. **Node placed with no code**
   - What we know: The branch condition is `node.toolType === 'data_transform' && node.props?.code`. A node with empty `code` string falls through to the `else` pass-through block.
   - What's unclear: Is silent pass-through on empty code correct, or should it warn?
   - Recommendation: A node with empty code silently passes through (matches the `js_script` guard pattern). The default `return data;` template ensures it is never truly empty on creation.

---

## Sources

### Primary (HIGH confidence)
- `backend/app/runtime/runner.ts` — full source read; `executeScriptNode()` at line 65, `js_script` handler at line 412–426, `runNodeExecution()` structure
- `backend/alembic/versions/010_add_js_script_tool.py` — exact migration pattern for tool insertion
- `backend/alembic/versions/032_add_email_tool.py` — confirms `down_revision = '032'` is the current migration head to chain from
- `dashboard-app/src/components/editor/FlowEditorCanvas.vue` — confirmed `code`-type prop rendering at line 578–585
- `dashboard-app/src/stores/toolCatalog.js` — confirmed `CAT_META.transform` exists with color/icon metadata
- `.planning/phases/38-data-transform-node/38-CONTEXT.md` — all locked implementation decisions
- `.planning/REQUIREMENTS.md` — TRANS-01, TRANS-02 definitions

### Secondary (MEDIUM confidence)
- N/A — all findings verified from source code directly

### Tertiary (LOW confidence)
- N/A

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified from source files
- Architecture: HIGH — exact insertion point confirmed at runner.ts:427, migration chain confirmed from 032 file
- Pitfalls: HIGH — derived from direct code inspection of existing handler patterns

**Research date:** 2026-05-31
**Valid until:** 2026-07-31 (stable codebase — no fast-moving external dependencies)
