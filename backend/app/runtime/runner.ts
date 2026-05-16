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
  notes?: any[]; // New separate layer for documentation
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

/**
 * Replaces {{path.to.val}} placeholders with values from context.
 */
function resolveString(str: string, context: any): string {
  if (!str || typeof str !== 'string') return str;
  return str.replace(/\{\{([\s\S]+?)\}\}/g, (match, path) => {
    const parts = path.trim().split('.');
    let val: any = context;
    for (const part of parts) {
      if (val && typeof val === 'object' && part in val) {
        val = val[part];
      } else {
        return match; // Not found, keep placeholder
      }
    }
    if (val === undefined || val === null) return "";
    return typeof val === 'object' ? JSON.stringify(val) : String(val);
  });
}

async function executeScriptNode(code: string, imports: string, context: any) {
  try {
    // ── Node.js built-in shim: Deno requires 'node:' prefix ──────────────────
    const NODE_BUILTINS = [
      'https', 'http', 'fs', 'path', 'crypto', 'stream', 'url',
      'util', 'os', 'buffer', 'events', 'querystring', 'net',
      'tls', 'zlib', 'child_process', 'readline', 'assert',
    ];
    let normalizedCode = code;
    let normalizedImports = imports || "";
    for (const mod of NODE_BUILTINS) {
      const fromRegex = new RegExp(`from\\s+['"]${mod}['"]`, 'g');
      const importRegex = new RegExp(`import\\(['"\`]${mod}['"\`]\\)`, 'g');
      
      normalizedCode = normalizedCode.replace(fromRegex, `from 'node:${mod}'`).replace(importRegex, `import('node:${mod}')`);
      normalizedImports = normalizedImports.replace(fromRegex, `from 'node:${mod}'`).replace(importRegex, `import('node:${mod}')`);
    }

    // ── Detect export default (may appear after import statements) ────────────
    const withoutComments = normalizedCode.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '').trim();
    const hasExportDefault = /\bexport\s+default\b/.test(withoutComments);
    const hasTopLevelImport = /^\s*import\s+/m.test(withoutComments);

    let moduleContent = '';
    if (hasExportDefault || hasTopLevelImport) {
      // Code is already module style — use as-is
      moduleContent = normalizedImports ? `${normalizedImports}\n\n${normalizedCode}` : normalizedCode;
    } else {
      // Wrap function body in an async function export
      moduleContent = `${normalizedImports ? normalizedImports + '\n\n' : ''}export default async function(ctx) {\n${normalizedCode}\n}`;
    }

    // Convert to base64 data URI so Deno treats it as a module
    const base64 = btoa(unescape(encodeURIComponent(moduleContent)));
    const dataUri = `data:text/javascript;base64,${base64}`;

    const mod = await import(dataUri);
    if (typeof mod.default === 'function') {
      return await mod.default(context);
    }
    return mod.default ?? context.payload;
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
        const result = await executeScriptNode(flow.payload.script, "", { payload: flow.payload.data || {} });
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
      const startMs = Date.now();
      const startTime = new Date(startMs).toISOString();

      // Source nodes resolved by Python before Deno – skip but keep success status
      if ((node as any).__pre_executed) {
        console.log(`[Flow] Nodo pre-ejecutado: ${node.label} (${node.toolType}) — omitiendo`);
        const prefetched = prefetchedOutputs[node.id] || { rows: [], duration: 0 };
        // Support both old (array) and new (object) format for robustness
        const p = Array.isArray(prefetched) ? prefetched : (prefetched.rows || []);
        const pythonDuration = Array.isArray(prefetched) ? 0 : (prefetched.duration || 0);

        nodeOutputs.set(node.id, p);
        currentPayload = p;
        
        const endMs = Date.now();
        const endTime = new Date(endMs).toISOString();
        const totalDuration = pythonDuration + (endMs - startMs);

        // Emit status AND log json so history catches it
        console.log(`NODE_LOG_JSON:${JSON.stringify({
          node_id: node.id, 
          status: 'success', 
          input: {}, 
          output: p, 
          duration: totalDuration, 
          start_time: startTime, 
          end_time: endTime
        })}`);
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
      
      if (['http_rest', 'graphql_api', 'graphql', 'rest_api', 'http'].includes(node.toolType)) {
        try {
          const rawUrl = node.props?.url || "";
          const url = resolveString(rawUrl, context);
          
          let method = node.props?.method || 'GET';
          const rawHeaders = node.props?.headers || '{}';
          let headers: any = {};
          try { 
            headers = JSON.parse(resolveString(rawHeaders, context)); 
          } catch(e) {}

          // Auth handling (using credentials resolved by Python)
          const authType = node.props?.auth_type;
          if (authType === 'bearer' && node.props?.api_key) {
            headers['Authorization'] = `Bearer ${node.props.api_key}`;
          } else if (authType === 'basic' && node.props?.username) {
             const auth = btoa(`${node.props.username}:${node.props.password || ''}`);
             headers['Authorization'] = `Basic ${auth}`;
          }

          const fetchOptions: any = { method, headers };

          if (node.toolType === 'graphql_api' || node.toolType === 'graphql') {
            method = 'POST';
            fetchOptions.method = 'POST';
            
            const rawQuery = node.props?.query || node.props?.graphql_query || "";
            const resolvedQuery = resolveString(rawQuery, context);
            
            let gqlBody: any = {};
            
            // Check if user provided a full JSON object in the query field
            const trimmedQuery = resolvedQuery.trim();
            if (trimmedQuery.startsWith('{') && trimmedQuery.endsWith('}')) {
              try {
                const parsed = JSON.parse(trimmedQuery);
                if (parsed.query) {
                  gqlBody = parsed;
                } else {
                  gqlBody = { query: resolvedQuery };
                }
              } catch {
                gqlBody = { query: resolvedQuery };
              }
            } else {
              gqlBody = { query: resolvedQuery };
            }

            // Handle variables
            const rawVars = node.props?.variables || node.props?.graphql_variables;
            if (rawVars) {
              try {
                const resolvedVars = resolveString(rawVars, context);
                gqlBody.variables = typeof resolvedVars === 'string' 
                  ? JSON.parse(resolvedVars) 
                  : resolvedVars;
              } catch (e: any) {
                console.warn(`[GraphQL] Invalid variables JSON: ${e.message}`);
              }
            } else if (!gqlBody.variables && context.payload && !Array.isArray(context.payload)) {
              // Auto-inject payload as variables if not explicitly defined
              gqlBody.variables = context.payload;
            }

            fetchOptions.body = JSON.stringify(gqlBody);
            if (!headers['Content-Type']) headers['Content-Type'] = 'application/json';
          } else {
            // REST / Generic HTTP logic
            if (method !== 'GET' && method !== 'HEAD') {
              if (node.props?.body) {
                fetchOptions.body = resolveString(node.props.body, context);
              } else if (context.payload) {
                fetchOptions.body = JSON.stringify(context.payload);
              }
              if (!headers['Content-Type']) headers['Content-Type'] = 'application/json';
            }
          }

          console.log(`[HTTP] ${method} ${url}`);
          const response = await fetch(url, fetchOptions);
          
          if (!response.ok) {
            const errText = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errText}`);
          }

          // Try to parse JSON, fallback to text if not possible
          let data;
          const contentType = response.headers.get("content-type") || "";
          if (contentType.includes("application/json")) {
            data = await response.json();
          } else {
            data = { text: await response.text() };
          }
          
          context.payload = data;
          
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: currentPayload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          console.error(`[HTTP Error] Failed to fetch: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else if (node.toolType === 'join') {
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
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: currentPayload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          console.error(`[Join Error] Failed to join: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else if (node.toolType === 'js_script' && node.props?.code) {
        try {
          const inputPayload = context.payload;
          context.payload = await executeScriptNode(node.props.code, node.props.imports || "", context);
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: inputPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: context.payload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
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
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: currentPayload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
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
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: currentPayload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
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
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: { status: 'executed' }, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          emitStatus(node.id, 'success');
          context.payload = { status: 'executed' };
        } catch (err: any) {
          const endMs = Date.now();
          const endTime = new Date(endMs).toISOString();
          console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'error', input: currentPayload, output: {}, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
          console.error(`[SQL Error]: ${err.message}`);
          emitStatus(node.id, 'error');
          Deno.exit(1);
        }
      } else {
        console.log(`[Flow Info] Node ${node.label} (${node.toolType}) is a system node. Passing through data.`);
        const endMs = Date.now();
        const endTime = new Date(endMs).toISOString();
        console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
        emitStatus(node.id, 'success');
      }

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
