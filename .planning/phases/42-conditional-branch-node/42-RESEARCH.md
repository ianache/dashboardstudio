# Phase 42: Conditional/Branch Node - Research

**Researched:** 2026-05-31
**Domain:** Flow Orchestration + UI Components
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `toolType`: `conditional_branch`, `category`: `transform` (or logic).
- Output ports: 2 (Green for True, Red for False).
- Logic: JS expression evaluation in Deno.
- Validation: Reject cycles in editor and runner.

### Claude's Discretion
- `fromHandle` values: `"true"` and `"false"`.
- Evaluation engine: Reuse `executeScriptNode` pattern but return boolean.
- Color constants: Green (`#22c55e`), Red (`#ef4444`).

</user_constraints>

---

## Summary

The Conditional/Branch node is a fundamental control-flow primitive. Unlike previous nodes which always pass data to all downstream connections, this node selectively enables/disables execution paths.

### Implementation Strategy

#### 1. UI: Multi-port Support
The current `FlowEditorCanvas.vue` assumes one input (left) and one output (right).
- **Modification**: When `node.toolType === 'conditional_branch'`, render two small circles on the right instead of one.
- **Connection Data**: Update `onPortMouseup` to store `fromHandle: "true"` or `"false"`.
- **Visuals**: Color-code the handles and the resulting connections if possible (or just use markers).

#### 2. Runner: Liveness Propagation
The runner will use a "Liveness" check for each node before execution:
- **Root Nodes**: Always live.
- **Other Nodes**: Live if at least one incoming connection is **active**.

A connection `C` (from `U` to `V`) is **active** if:
1. Upstream node `U` was executed successfully (not skipped).
2. AND, if `U` is a `conditional_branch`, `C.fromHandle` matches `U`'s result (converted to string "true" or "false").
3. OR, if `U` is NOT a branch node, it is always active if `U` ran.

**Algorithm at Node V**:
```typescript
const incoming = flow.connections.filter(c => c.to === V.id);
const hasActiveInput = (incoming.length === 0) || incoming.some(c => {
  const upstreamStatus = nodeExecStatus.get(c.from);
  if (upstreamStatus !== 'success') return false;

  const upstreamNode = nodes.find(n => n.id === c.from);
  if (upstreamNode.toolType === 'conditional_branch') {
    const result = nodeResults.get(c.from); // true or false
    return c.fromHandle === String(result);
  }
  return true;
});

if (!hasActiveInput) {
  skippedNodes.add(V.id);
  continue;
}
```


#### 3. Runner: Cycle Detection
Currently `getTopologicalOrder` ignores cycles.
- **Fix**: Check `order.length === nodes.length`. If not, throw "Cycle detected".

#### 4. Editor: Cycle Prevention
Add a check in `onPortMouseup` before creating a connection:
- If `isReachable(toNode, fromNode)`, then adding the connection would create a cycle.
- Reject the connection and show an error alert.

---

## Technical Details

### Handle Colors
| Handle | Color | Constant |
|--------|-------|----------|
| True | Green | `#22c55e` |
| False | Red | `#ef4444` |

### Connection Schema
```json
{
  "id": "c123",
  "from": "node-branch",
  "to": "node-target",
  "fromHandle": "true"
}
```

---

## Architecture Patterns

### Pattern 1: Conditional Evaluation in Runner
```typescript
} else if (node.toolType === 'conditional_branch') {
  const result = await evaluateBoolean(node.props.expression, context);
  // result is true or false
  const inactiveHandle = result ? 'false' : 'true';
  
  // Find nodes to skip
  const nodesToSkip = findNodesOnlyReachableFrom(node.id, inactiveHandle, flow);
  nodesToSkip.forEach(id => skippedNodes.add(id));
}
```

### Pattern 2: Cycle Detection Helper (Editor)
```javascript
function isReachable(startNodeId, targetNodeId, connections) {
  const visited = new Set();
  const queue = [startNodeId];
  while (queue.length > 0) {
    const curr = queue.shift();
    if (curr === targetNodeId) return true;
    visited.add(curr);
    connections
      .filter(c => c.from === curr)
      .forEach(c => { if (!visited.has(c.to)) queue.push(c.to); });
  }
  return false;
}
```

---

## Common Pitfalls

### Pitfall 1: Multi-input Nodes after a Branch
**Scenario**: Node C is connected to both the True and False paths of Node A.
**Risk**: If we skip the False path, Node C might still execute because the True path is active.
**Mitigation**: The runner must correctly handle "Join" nodes after branches. A node should execute if ANY active path reaches it.

### Pitfall 2: Expression Errors
**Risk**: User writes `payload.val == 1` but `payload` is undefined.
**Mitigation**: Wrap evaluation in try/catch, default to False or fail the flow with `[Branch Error]`.

---

## Sources
- `runner.ts` current `dsplit` logic for skipping.
- `FlowEditorCanvas.vue` mouse event handlers.
