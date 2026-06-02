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
    let moduleContent = code;
    
    // Heuristic: If user code already has 'export default', don't wrap it.
    // This allows advanced users to include imports or custom logic outside the main function.
    const hasExportDefault = /\bexport\s+default\b/.test(code);
    
    if (!hasExportDefault) {
      moduleContent = `export default async function(ctx) {\n${code}\n}`;
    }

    const base64 = btoa(unescape(encodeURIComponent(moduleContent)));
    const dataUri = `data:text/javascript;base64,${base64}`;
    const mod = await import(dataUri);
    
    if (typeof mod.default !== 'function') {
      throw new Error("Script execution failed: The script must have a default export that is a function.");
    }

    return await mod.default(context);
  } catch (err: any) {
    // Provide cleaner error messages for common parsing/execution issues
    const errorPrefix = (err.name === 'SyntaxError' || err.message.includes('could not be parsed')) 
      ? "[Script Syntax Error]" 
      : "[Script Error]";
    
    console.error(`${errorPrefix}: ${err.message}`);
    throw err;
  }
}

function resolveTemplates(obj: any, context: any): any {
  if (typeof obj === 'string') {
    try {
      return nunjucks.renderString(obj, context);
    } catch (e) {
      return obj;
    }
  }
  if (Array.isArray(obj)) {
    return obj.map(item => resolveTemplates(item, context));
  }
  if (obj !== null && typeof obj === 'object') {
    const res: any = {};
    for (const key in obj) {
      res[key] = resolveTemplates(obj[key], context);
    }
    return res;
  }
  return obj;
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

      // Ensure predecessors are done
      const incoming = connections.filter(c => c.to === nodeId);
      if (incoming.length > 0 && !incoming.every(c => completed.has(c.from))) {
        // Not ready yet, skip for now (it will be queued again when predecessors finish)
        continue;
      }
      
      // Resolve input payload from predecessors
      let currentPayload: any = [];
      if (incoming.length === 1) {
        currentPayload = nodeOutputs.get(incoming[0].from) || [];
      } else if (incoming.length > 1) {
        // Multi-input: default behavior is array of payloads
        currentPayload = incoming.map(c => nodeOutputs.get(c.from) || []);
      }

      const startMs = Date.now();
      const startTime = new Date(startMs).toISOString();
      emitStatus(node.id, 'running');

      let branchToTake: string | null = null;
      let outputPayload = currentPayload;

      try {
        if ((node as any).__pre_executed) {
          const prefetched = prefetched_outputs[node.id] || { rows: [] };
          outputPayload = Array.isArray(prefetched) ? prefetched : (prefetched.rows || []);
          if (prefetched.warning) console.log(`[Model Warning] ${node.label}: ${prefetched.warning}`);
        } 
        else if (node.toolType === "js_script") {
          outputPayload = await executeScriptNode(node.props.code || "", "", { payload: currentPayload, variables });
        }
        else if (node.toolType === "data_transform") {
          // data_transform expects async function(payload, ctx) { ... }
          outputPayload = await executeScriptNode(node.props.code || "", "", { payload: currentPayload, variables });
        }
        else if (node.toolType === "nunjucks_template") {
          // Prepare context: avoid spreading arrays
          const templateData = {
            ...variables,
            payload: currentPayload,
            variables: variables
          };
          // Only spread if it's a plain object (not array, not null)
          if (typeof currentPayload === 'object' && currentPayload !== null && !Array.isArray(currentPayload)) {
            Object.assign(templateData, currentPayload);
          }
          outputPayload = nunjucks.renderString(node.props.template || "", templateData);
        }
        else if (node.toolType === "email") {
          const connectionId = node.props.connection_id;
          if (!connectionId) throw new Error("Email node requires connection_id");

          const parseRecipients = (val: any): string[] => {
            if (!val) return [];
            const resolved = resolveTemplates(val, { payload: currentPayload, variables });
            if (typeof resolved !== 'string') return [String(resolved)];
            return resolved.split(',').map(s => s.trim()).filter(s => s);
          };

          const batchId = `batch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          const emailPayload = {
            node_id: node.id,
            target: {
              connection_id: connectionId,
              to: parseRecipients(node.props.to),
              cc: parseRecipients(node.props.cc),
              bcc: parseRecipients(node.props.bcc),
            },
            content: {
              subject: resolveTemplates(node.props.subject || "Flow Notification", { payload: currentPayload, variables }),
              body: resolveTemplates(node.props.body || "", { payload: currentPayload, variables }),
              format: node.props.format || "html"
            },
            template_context: currentPayload || {},
            metadata: {
              execution_id: (flow.metadata as any)?.execution_id || "unknown",
              node_label: node.label,
              timestamp: new Date().toISOString()
            }
          };

          console.log(`EXEC_EMAIL:${node.id}:${batchId}`);
          console.log(`EXEC_EMAIL_PAYLOAD:${JSON.stringify(emailPayload)}`);
          outputPayload = { status: "delegated", operation: "send_email" };
        }
        else if (node.toolType === "ods_pg") {
          const { connection_id, table, write_mode = "append", schema = "public" } = node.props;
          if (!connection_id || !table) throw new Error("ODS PostgreSQL requires connection_id and table");

          const records = Array.isArray(currentPayload) ? currentPayload : [currentPayload];
          const batchId = `batch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          const odsPayload = {
            node_id: node.id,
            operation: write_mode,
            target: { connection_id, schema, table },
            config: { write_mode, identity_fields: node.props.identity_fields || [], batch_size: node.props.batch_size || 1000 },
            data: records,
            metadata: {
              execution_id: (flow as any).metadata?.execution_id || "unknown",
              node_label: node.label,
              timestamp: new Date().toISOString()
            }
          };

          console.log(`EXEC_ODS:${node.id}:${write_mode}:${connection_id}:${batchId}`);
          console.log(`EXEC_ODS_PAYLOAD:${JSON.stringify(odsPayload)}`);
          outputPayload = { status: "delegated", operation: write_mode, rows: records.length };
        }
        else if (['http_rest', 'rest_api', 'http', 'webhook'].includes(node.toolType)) {
          const nodeContext = { payload: currentPayload, variables };
          const url = resolveTemplates(node.props.url, nodeContext);
          const method = (node.props.method || "GET").toUpperCase();
          const headers = resolveTemplates(node.props.headers || {}, nodeContext);
          const body = (method !== "GET" && method !== "HEAD") ? resolveTemplates(node.props.body, nodeContext) : undefined;

          const response = await fetch(url, {
            method,
            headers,
            body: typeof body === 'object' ? JSON.stringify(body) : body
          });

          if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}: ${await response.text()}`);
          }

          const contentType = response.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            outputPayload = await response.json();
          } else {
            outputPayload = await response.text();
          }
        }
        else if (['join', 'djoin'].includes(node.toolType)) {
          // Aggregation logic for DJoin/Join
          if (Array.isArray(currentPayload) && incoming.length > 1) {
             // currentPayload is [[results1], [results2], ...]
             outputPayload = currentPayload.flat();
          } else {
             outputPayload = currentPayload;
          }
        }
        else if (node.toolType === "conditional_branch") {
          const expression = node.props.expression || "true";
          const fn = new Function("payload", "variables", `return (${expression});`);
          const result = !!fn(currentPayload, variables);
          branchToTake = result ? "true" : "false";
          console.log(`[Flow] Node ${node.id} branch decided: ${branchToTake}`);
          outputPayload = currentPayload;
        }

        const endMs = Date.now();
        console.log(`NODE_LOG_JSON:${JSON.stringify({
          node_id: node.id, status: 'success', 
          input: (typeof currentPayload === 'object' && currentPayload !== null && JSON.stringify(currentPayload).length < 2000) ? currentPayload : {}, 
          output: outputPayload, 
          duration: endMs - startMs, start_time: startTime, end_time: new Date(endMs).toISOString()
        })}`);
        emitStatus(node.id, 'success');
        
        nodeOutputs.set(node.id, outputPayload);
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

    // Resolve final result (output of nodes with no outgoing connections)
    const leafNodes = nodes.filter(n => !connections.some(c => c.from === n.id));
    const finalResult = leafNodes.length === 1 
      ? nodeOutputs.get(leafNodes[0].id) 
      : Object.fromEntries(leafNodes.map(n => [n.label || n.id, nodeOutputs.get(n.id)]));

    console.log("Flow completed successfully.");
    console.log("FINAL_RESULT:" + JSON.stringify(finalResult));

  } catch (err: any) {
    console.error(`Fatal error: ${err.message}`);
    Deno.exit(1);
  }
}

if (import.meta.main) {
  main();
}
