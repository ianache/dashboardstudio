/**
 * Dashboard Studio Integration Flow Runner
 * This script runs inside Deno and processes integration flows.
 */

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
}

interface FlowData {
  nodes: FlowNode[];
  connections: FlowConnection[];
  test_mode?: boolean;
  payload?: any;
  prefetched_outputs?: Record<string, any[]>;
}

async function readStdin(): Promise<string> {
  const decoder = new TextDecoder();
  let text = "";
  for await (const chunk of Deno.stdin.readable) {
    text += decoder.decode(chunk);
  }
  return text;
}

async function executeScriptNode(code: string, context: any) {
  try {
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const trimmed = code.trim();

    if (trimmed.startsWith("export default")) {
      // ES module style: export default async function(ctx) { ... }
      // Strip the "export default" prefix and invoke the remaining function expression.
      const funcExpr = trimmed.replace(/^export\s+default\s+/, "");
      const wrapper = new AsyncFunction("ctx", `return (${funcExpr})(ctx);`);
      return await wrapper(context);
    } else {
      // Function body style: the code IS the body of an async function.
      const userFunc = new AsyncFunction("ctx", code);
      return await userFunc(context);
    }
  } catch (err: any) {
    console.error(`[Script Error in Node]: ${err.message}`);
    throw err;
  }
}

function emitStatus(nodeId: string, status: 'running' | 'success' | 'error') {
  console.log(`NODE_STATUS:${nodeId}:${status}`);
}

/**
 * Calculates topological order for the nodes.
 * Simplified version: handles multiple paths and ensures nodes are executed after their inputs.
 */
function getTopologicalOrder(nodes: FlowNode[], connections: FlowConnection[]): FlowNode[] {
  const adj = new Map<string, string[]>();
  const inDegree = new Map<string, number>();

  nodes.forEach(n => {
    adj.set(n.id, []);
    inDegree.set(n.id, 0);
  });

  connections.forEach(c => {
    adj.get(c.from)?.push(c.to);
    inDegree.set(c.to, (inDegree.get(c.to) || 0) + 1);
  });

  const queue: string[] = [];
  inDegree.forEach((degree, id) => {
    if (degree === 0) queue.push(id);
  });

  const order: string[] = [];
  while (queue.length > 0) {
    const u = queue.shift()!;
    order.push(u);
    adj.get(u)?.forEach(v => {
      inDegree.set(v, inDegree.get(v)! - 1);
      if (inDegree.get(v) === 0) queue.push(v);
    });
  }

  // If order.length < nodes.length, there's a cycle, but we'll proceed for now
  return order.map(id => nodes.find(n => n.id === id)!).filter(Boolean) as FlowNode[];
}

async function main() {
  try {
    const input = await readStdin();
    if (!input) {
      console.error("No input received");
      Deno.exit(1);
    }

    const flow: FlowData = JSON.parse(input);

    if (flow.test_mode) {
      console.log("Deno Runtime: OK");
      console.log(`Deno Version: ${Deno.version.deno}`);
      if (flow.payload?.script) {
        const result = await executeScriptNode(flow.payload.script, { payload: flow.payload.data || {} });
        console.log("Execution Result:", JSON.stringify(result));
      }
      return;
    }

    console.log(`Starting flow execution. Nodes: ${flow.nodes.length}`);
    
    const sortedNodes = getTopologicalOrder(flow.nodes, flow.connections);
    const prefetchedOutputs = flow.prefetched_outputs || {};
    let currentPayload = flow.payload || {};
    const nodeOutputs = new Map<string, any>();
    const context = { payload: currentPayload, variables: {} };

    for (const node of sortedNodes) {
      // Source nodes resolved by Python before Deno – skip but keep success status
      if ((node as any).__pre_executed) {
        console.log(`[Flow] Nodo pre-ejecutado: ${node.label} (${node.toolType}) — omitiendo`);
        const p = prefetchedOutputs[node.id] || [];
        nodeOutputs.set(node.id, p);
        currentPayload = p;
        emitStatus(node.id, 'success');
        continue;
      }

      // Gather inputs from incoming connections
      const incoming = flow.connections.filter(c => c.to === node.id);
      if (incoming.length === 1) {
        currentPayload = nodeOutputs.get(incoming[0].from) || [];
      } else if (incoming.length > 1 && node.toolType !== 'join') {
        currentPayload = incoming.map(c => nodeOutputs.get(c.from) || []);
      }
      context.payload = currentPayload;

      emitStatus(node.id, 'running');
      console.log(`[Flow] Executing Node: ${node.label} (${node.toolType})`);
      
      if (node.toolType === 'join') {
        try {
          const joinType = node.props?.join_type || 'inner';
          const joinKey = node.props?.join_key;

          if (!joinKey) {
            throw new Error("Clave de unión (join_key) no especificada");
          }
          if (incoming.length < 2) {
            throw new Error("Un nodo Join requiere al menos 2 conexiones de entrada");
          }

          const left = nodeOutputs.get(incoming[0].from) || [];
          const right = nodeOutputs.get(incoming[1].from) || [];
          const result = [];

          if (joinType === 'inner') {
             for (const l of left) {
                for (const r of right) {
                   if (l[joinKey] === r[joinKey]) {
                       result.push({ ...l, ...r });
                   }
                }
             }
          } else if (joinType === 'left') {
             for (const l of left) {
                let matched = false;
                for (const r of right) {
                   if (l[joinKey] === r[joinKey]) {
                       result.push({ ...l, ...r });
                       matched = true;
                   }
                }
                if (!matched) {
                   result.push({ ...l });
                }
             }
          } else if (joinType === 'right') {
             for (const r of right) {
                let matched = false;
                for (const l of left) {
                   if (l[joinKey] === r[joinKey]) {
                       result.push({ ...l, ...r });
                       matched = true;
                   }
                }
                if (!matched) {
                   result.push({ ...r });
                }
             }
          } else if (joinType === 'full') {
             const rightMatched = new Set();
             for (const l of left) {
                let matched = false;
                for (let i = 0; i < right.length; i++) {
                   const r = right[i];
                   if (l[joinKey] === r[joinKey]) {
                       result.push({ ...l, ...r });
                       matched = true;
                       rightMatched.add(i);
                   }
                }
                if (!matched) {
                   result.push({ ...l });
                }
             }
             for (let i = 0; i < right.length; i++) {
                if (!rightMatched.has(i)) {
                   result.push({ ...right[i] });
                }
             }
          } else {
             throw new Error(`Tipo de join no soportado: ${joinType}`);
          }
          
          context.payload = result;
          emitStatus(node.id, 'success');
        } catch (err: any) {
          console.error(`[Join Error] Failed to join: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else if (node.toolType === 'js_script' && node.props?.code) {
        try {
          context.payload = await executeScriptNode(node.props.code, context);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          console.error(`[Flow Error] Node ${node.label} failed: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else if (node.toolType === 'csv_file' && node.props?.path) {
        try {
          const path = node.props.path;
          console.log(`[CSV] Reading file: ${path}`);
          const content = await Deno.readTextFile(path);
          
          // Simple CSV parser
          const delimiter = node.props.delimiter || ',';
          const hasHeader = node.props.has_header === 'true';
          const lines = content.split(/\r?\n/).filter(l => l.trim());
          
          if (lines.length === 0) {
            context.payload = [];
          } else {
            const rows = lines.map(line => line.split(delimiter));
            if (hasHeader) {
              const headers = rows[0].map(h => h.trim());
              context.payload = rows.slice(1).map(row => {
                const obj: any = {};
                headers.forEach((h, i) => obj[h] = row[i]?.trim());
                return obj;
              });
            } else {
              context.payload = rows;
            }
          }
          console.log(`[CSV] Loaded ${context.payload.length} rows`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          console.error(`[CSV Error] Failed to read ${node.props.path}: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else if (node.toolType === 'email') {
        try {
          const to = node.props?.to || 'admin@company.com';
          const subject = node.props?.subject || 'Flow Notification';
          const body = node.props?.body || `Flow execution result: ${JSON.stringify(context.payload, null, 2)}`;
          const triggerOn = node.props?.trigger_on || 'success';

          console.log(`[Email] 📧 Mock Sending Email...`);
          console.log(`[Email] To: ${to}`);
          console.log(`[Email] Subject: ${subject}`);
          console.log(`[Email] Trigger Condition: ${triggerOn}`);
          
          // In a real implementation, we would use an SMTP client here.
          // For now, we log the intent and the payload.
          console.log(`[Email] Content: ${body.substring(0, 100)}${body.length > 100 ? '...' : ''}`);
          
          console.log(`[Email] ✅ Message delivered to mail queue (simulated)`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          console.error(`[Email Error] Failed to send: ${err.message}`);
          emitStatus(node.id, 'error');
        }
      } else if (node.toolType === 'sql_source' || node.toolType === 'sql_destination') {
        try {
          const connectionId = node.props?.connection_id;
          const query = node.props?.query;

          if (!connectionId || !query) {
             throw new Error("Conexión o Query no especificada");
          }

          console.log(`[SQL] Executing query on connection: ${connectionId}`);
          
          // Emit a custom event that the backend runner (Python) can catch
          console.log(`EXEC_SQL:${connectionId}:${query}`);

          // Placeholder: in real integration the Python service handles the result
          emitStatus(node.id, 'success');
          context.payload = { status: 'executed' };
        } catch (err: any) {
          console.error(`[SQL Error]: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else {

      // Save output for downstream nodes
      nodeOutputs.set(node.id, context.payload);
      currentPayload = context.payload;
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
