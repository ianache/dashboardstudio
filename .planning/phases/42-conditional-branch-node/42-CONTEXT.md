# Phase 42: Conditional/Branch Node - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `conditional_branch` node that allows splitting flow execution into two distinct paths (True and False) based on a JavaScript expression.

### Core Value
Enable logical decision-making within flows without requiring complex Script nodes. This allows for workflows like "If data is empty, skip email" or "If status is 'error', notify admin".

### Success Criteria
- User can add a "Conditional" node with a single JS boolean expression.
- The node has **two output ports** (True/False) visually distinguished by color (Green/Red).
- Connections from these ports have a `fromHandle` property (`true` or `false`).
- The Deno runner evaluates the expression and only executes the downstream path matching the result.
- Cycles in the flow are detected and rejected by both the editor and the runner.
- The runner throws a clear "Cycle detected" error instead of producing silently wrong output.

</domain>

<requirements>
## v1.9 Requirements (Traceability)

- **BRNCH-01**: JS boolean expression evaluation.
- **BRNCH-02**: Multiple output ports (True/False).
- **BRNCH-03**: Hardened cycle detection in runner and editor.

</requirements>

<code_context>
## Relevant Files

- `dashboard-app/src/components/editor/FlowEditorCanvas.vue`: Node rendering, port logic, connection drawing.
- `backend/app/runtime/runner.ts`: Execution loop, topological sort, branching logic.
- `backend/alembic/versions/`: Migration to register the `conditional_branch` tool.

</code_context>

<deferred>
## Deferred Ideas

- Switch/Case node (multiple branches).
- Visual debugging of branch paths (highlighting the skipped path).

</deferred>

---

*Phase: 42-conditional-branch-node*
*Context gathered: 2026-05-31*
