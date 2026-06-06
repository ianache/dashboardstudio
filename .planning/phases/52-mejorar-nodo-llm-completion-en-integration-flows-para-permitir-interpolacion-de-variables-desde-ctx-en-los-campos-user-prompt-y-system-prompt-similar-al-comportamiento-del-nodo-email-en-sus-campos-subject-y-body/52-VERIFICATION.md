---
phase: 52-mejorar-nodo-llm-completion
verified: 2026-06-05T22:40:00Z
status: human_needed
score: 5/5 must-haves verified
human_verification:
  - test: "Open Flow Editor, select an LLM Completion node, confirm hint appears below both User Prompt and System Prompt textareas"
    expected: "A styled blue-left-border info bar reads: Usa {{payload.campo}} y {{variables.nombre}}. Soporta filtros Jinja2 como | tojson"
    why_human: "Visual rendering of Vue template hint — cannot verify DOM output from static analysis"
  - test: "Select an Email node in the Flow Editor, confirm the LLM Jinja2 hint does NOT appear under its fields"
    expected: "Only the existing Email hints (Supports {{variable_insert}} and {% for %}) are visible — no LLM hint"
    why_human: "Node-type scoping of hints requires interactive UI inspection"
  - test: "Select any non-LLM, non-Email node (e.g., ODS, Script) and confirm no template hint of any kind appears"
    expected: "No hint element visible under any field"
    why_human: "Requires interactive UI inspection"
  - test: "Execute a flow with an LLM node whose system_prompt contains {{ variables.nombre }} — confirm the rendered string (not the template literal) is sent to the LLM API"
    expected: "The LLM receives a resolved system prompt string; variables.nombre is substituted or blanked if missing"
    why_human: "Requires a live flow execution with network inspection or backend logging"
---

# Phase 52: LLM Completion Jinja2 system_prompt + UI Hints Verification Report

**Phase Goal:** Habilitar interpolacion Jinja2 en el campo system_prompt del nodo LLM Completion, y agregar hints visuales en ambos campos (user_prompt y system_prompt) del editor de flujos.
**Verified:** 2026-06-05T22:40:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | system_prompt se renderiza como template Jinja2 con el mismo contexto {payload, variables} que user_prompt | VERIFIED | `llm_executor.py` line 36: `rendered_system_prompt = jinja2.Template(system_prompt_template).render(context)` — identical context-building logic as user_prompt block (lines 43-46) |
| 2 | Un error de sintaxis en system_prompt devuelve un error de nodo claro (no una excepcion Python no controlada) | VERIFIED | Lines 31-38: try/except wraps the rendering call; returns `{"success": False, "error": "Failed to render system prompt: {str(e)}"}` |
| 3 | Variables inexistentes en system_prompt renderizan como string vacio (no excepcion) | VERIFIED | No `StrictUndefined` configured; Jinja2 default `Undefined` silently renders missing variables as empty string |
| 4 | El hint de template Jinja2 aparece debajo de los campos user_prompt y system_prompt en el editor de flujos | VERIFIED (automated) / NEEDS HUMAN (visual) | `FlowEditorCanvas.vue` line 724: `v-if="selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)"` — element exists with correct condition and reuses `.fec-template-hint` class |
| 5 | El hint NO aparece en campos de otros tipos de nodo ni en campos de diferente nombre | VERIFIED (automated) / NEEDS HUMAN (visual) | Condition is strictly `toolType === 'llm'` AND key in `['user_prompt', 'system_prompt']`; scoped to LLM nodes only |

**Score:** 5/5 truths verified (4 require human confirmation for visual/runtime behavior)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/llm_executor.py` | system_prompt Jinja2 rendering block with `rendered_system_prompt` variable | VERIFIED | Line 22: `system_prompt_template = props.get(...)`, line 36: `rendered_system_prompt = jinja2.Template(...).render(context)`, line 64: `"content": rendered_system_prompt` in messages array |
| `dashboard-app/src/components/editor/FlowEditorCanvas.vue` | LLM field template hints at line 724 | VERIFIED | `<p v-if="selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)" class="fec-template-hint">` — substantive, positioned inside the prop-group div |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `llm_executor.py line 22 (system_prompt_template)` | `llm_payload messages[0].content` | `rendered_system_prompt` variable | WIRED | Line 22 sets template, line 36 renders it, line 64 uses `rendered_system_prompt` in messages array |
| `FlowEditorCanvas.vue v-if hint (line 724)` | `user_prompt and system_prompt textareas` | `selectedNode.toolType === 'llm' && ['user_prompt', 'system_prompt'].includes(key)` | WIRED | Exact condition string found at line 724; `.fec-template-hint` CSS class present at lines 2843-2858 |

---

### Requirements Coverage

No requirement IDs were declared for this phase (requirements: [] in PLAN frontmatter). Not applicable.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TODO/FIXME/stub returns/empty handlers found in the two modified files.

---

### Human Verification Required

#### 1. LLM hint appears in Flow Editor UI

**Test:** Open the Flow Editor, add or select an LLM Completion node, open its properties panel, and inspect both "User Prompt" and "System Prompt" fields.
**Expected:** A styled info bar (blue left border, info icon) reading "Usa {{payload.campo}} y {{variables.nombre}}. Soporta filtros Jinja2 como | tojson" appears below each of the two textareas.
**Why human:** Vue template conditional rendering — the `v-if` condition is correct but visual appearance and DOM mounting require browser rendering.

#### 2. Hint absent from Email nodes

**Test:** Select an Email node, inspect its Subject and Body fields.
**Expected:** Only the two existing Email hints appear (one under subject, one under body). The LLM Jinja2 hint does not appear anywhere.
**Why human:** Node-type isolation requires interactive inspection with a live selectedNode state.

#### 3. Hint absent from all other node types

**Test:** Select an ODS node, Script node, or Templating node and inspect their fields.
**Expected:** No template hint element of any kind appears.
**Why human:** Requires interactive UI inspection with varied node selections.

#### 4. Live system_prompt interpolation during flow execution

**Test:** Create a flow with an LLM node. Set system_prompt to `You are analyzing data for {{ variables.nombre }}.` and set variables.nombre = `Acme Corp` in the flow context. Execute the flow.
**Expected:** The LLM API receives the system message `You are analyzing data for Acme Corp.` — not the raw template string.
**Why human:** Requires live flow execution with backend log inspection or network traffic capture.

---

### Gaps Summary

No gaps found. All five observable truths are implemented correctly:

- `llm_executor.py` has been surgically modified with the system_prompt rendering block (1a) inserted before the existing user_prompt block (1), using identical context-building logic and error handling. The messages array uses `rendered_system_prompt`. The naming convention (`_template` suffix for input, `rendered_` prefix for output) is consistent with the user_prompt pattern.

- `FlowEditorCanvas.vue` has the new `<p v-if>` hint element at line 724, immediately after the two Email hints (lines 716-723) and before the closing `</div>` at line 728, exactly as specified. The condition is precisely scoped to LLM nodes and the two relevant field names. No new CSS was added — reuses the existing `.fec-template-hint` class.

- Both commits exist in git history (`819d9bc` for backend, `526dbe9` for frontend) with correct attribution and descriptive messages.

Four items are flagged for human verification because they require browser rendering or live execution — all automated checks pass.

---

_Verified: 2026-06-05T22:40:00Z_
_Verifier: Claude (gsd-verifier)_
