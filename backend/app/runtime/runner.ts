/**
 * Dashboard Studio Integration Flow Runner
 * This script runs inside Deno and processes integration flows.
 */

import nunjucks from "npm:nunjucks";

interface FlowNode {
  id: string;
  toolType: string;
  category: string;
  label: string;
  props: {
    code?: string;
    [key: string]: any;
  };
}

interface FlowConnection {
  id: string;
  from: string;
  to: string;
  fromHandle?: string; // e.g. "true", "false"
}

interface FlowData {
  nodes: FlowNode[];
  connections: FlowConnection[];
  notes?: any[];
  metadata?: {
    variables?: Array<{ name: string; type: string; value: any }>;
    [key: string]: any;
  };
  test_mode?: boolean;
  payload?: any;
  prefetched_outputs?: Record<string, any>;
}

async function readStdin(): Promise<string> {
  const decoder = new TextDecoder();
  let text = "";
  for await (const chunk of Deno.stdin.readable) {
    text += decoder.decode(chunk);
  }
  return text;
}

function emitStatus(nodeId: string, status: 'running' | 'success' | 'error') {
  console.log(`NODE_STATUS:${nodeId}:${status}`);
}

/**
 * Validates that the flow has no cycles using topological sort (Kahn's algorithm)
 */
function validateNoCycles(nodes: FlowNode[], connections: FlowConnection[]) {
  const inDegree: Record<string, number> = {};
  const adj: Record<string, string[]> = {};
  
  nodes.forEach(n => {
    inDegree[n.id] = 0;
    adj[n.id] = [];
  });

  connections.forEach(c => {
    if (adj[c.from]) {
      adj[c.from].push(c.to);
      inDegree[c.to]++;
    }
  });

  const queue: string[] = [];
  Object.keys(inDegree).forEach(id => {
    if (inDegree[id] === 0) queue.push(id);
  });

  let count = 0;
  while (queue.length > 0) {
    const u = queue.shift()!;
    count++;
    adj[u].forEach(v => {
      inDegree[v]--;
      if (inDegree[v] === 0) queue.push(v);
    });
  }

  if (count < nodes.length) {
    throw new Error("Cycle detected in integration flow. Circular connections are not allowed.");
  }
}

async function executeScriptNode(code: string, imports: string, context: any) {
  try {
    const moduleContent = `export default async function(ctx) {\n${code}\n}`;
    const base64 = btoa(unescape(encodeURIComponent(moduleContent)));
    const dataUri = `data:text/javascript;base64,${base64}`;
    const mod = await import(dataUri);
    return await mod.default(context);
  } catch (err: any) {
    console.error(`[Script Error]: ${err.message}`);
    throw err;
  }
}

async function main() {
  try {
    const input = await readStdin();
    if (!input) Deno.exit(1);

    const flow: FlowData = JSON.parse(input);
    const { nodes, connections, payload, variables: metadataVars, prefetched_outputs = {} } = flow;

    // 1. Hardened Cycle Detection
    validateNoCycles(nodes, connections);

    // 2. Initialize Context
    const variables: Record<string, any> = {};
    if (metadataVars && Array.isArray(metadataVars)) {
      metadataVars.forEach(v => {
        let val = v.value;
        if (v.type === 'number') val = Number(v.value);
        if (v.type === 'boolean') val = String(v.value).toLowerCase() === 'true';
        if (v.type === 'json') try { val = JSON.parse(v.value); } catch(e){}
        variables[v.name] = val;
      });
    }

    const context = { payload: JSON.parse(JSON.stringify(payload || {})), variables };
    const nodeOutputs = new Map<string, any>();
    const completed = new Set<string>();
    
    // 3. Execution Queue (BFS-like traversal of the DAG)
    const queue: string[] = nodes.filter(n => !connections.some(c => c.to === n.id)).map(n => n.id);

    while (queue.length > 0) {
      const nodeId = queue.shift()!;
      if (completed.has(nodeId)) continue;

      const node = nodes.find(n => n.id === nodeId);
      if (!node) continue;

      // Ensure predecessors are done (respect branching)
      const incoming = connections.filter(c => c.to === nodeId);
      // For now, if ANY predecessor connected to this node in the graph is NOT completed, 
      // and it hasn't been branched away, we might need to wait.
      // Simplification: In a standard DAG, we just follow the flow.
      
      // Resolve input payload from predecessors
      if (incoming.length === 1) {
        context.payload = nodeOutputs.get(incoming[0].from) || [];
      } else if (incoming.length > 1) {
        context.payload = incoming.map(c => nodeOutputs.get(c.from) || []);
      }

      const startMs = Date.now();
      const startTime = new Date(startMs).toISOString();
      emitStatus(node.id, 'running');

      let branchToTake: string | null = null;

      try {
        if ((node as any).__pre_executed) {
          const prefetched = prefetched_outputs[node.id] || { rows: [] };
          const data = Array.isArray(prefetched) ? prefetched : (prefetched.rows || []);
          context.payload = data;
          if (prefetched.warning) console.log(`[Model Warning] ${node.label}: ${prefetched.warning}`);
        } 
        else if (node.toolType === "js_script") {
          context.payload = await executeScriptNode(node.props.code || "", "", context);
        }
        else if (node.toolType === "nunjucks_template") {
          context.payload = nunjucks.renderString(node.props.template || "", context);
        }
        else if (node.toolType === "conditional_branch") {
          const expression = node.props.expression || "true";
          const fn = new Function("payload", "variables", `return (${expression});`);
          const result = !!fn(context.payload, context.variables);
          branchToTake = result ? "true" : "false";
          console.log(`[Flow] Node ${node.id} branch decided: ${branchToTake}`);
        }

        const endMs = Date.now();
        console.log(`NODE_LOG_JSON:${JSON.stringify({
          node_id: node.id, status: 'success', 
          input: {}, output: context.payload, 
          duration: endMs - startMs, start_time: startTime, end_time: new Date(endMs).toISOString()
        })}`);
        emitStatus(node.id, 'success');
        
        nodeOutputs.set(node.id, context.payload);
        completed.add(nodeId);

        // Queue next nodes
        const outgoing = connections.filter(c => c.from === nodeId);
        for (const conn of outgoing) {
          if (node.toolType === 'conditional_branch') {
            if (conn.fromHandle === branchToTake) queue.push(conn.to);
          } else {
            queue.push(conn.to);
          }
        }
      } catch (err: any) {
        emitStatus(node.id, 'error');
        throw err;
      }
    }

    console.log("Flow completed successfully.");
    console.log("FINAL_RESULT:" + JSON.stringify(context.payload));

  } catch (err: any) {
    console.error(`Fatal error: ${err.message}`);
    Deno.exit(1);
  }
}

if (import.meta.main) {
  main();
}
