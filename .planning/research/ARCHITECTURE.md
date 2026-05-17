# ODS Execution Engine Architecture

**Project:** Dashboard Studio - ODS Execution Engine  
**Researched:** 2026-05-16  
**Confidence:** HIGH (based on existing codebase analysis)

## Executive Summary

The ODS Execution Engine extends the existing Deno-Python flow execution architecture to support real-time PostgreSQL write operations. The design leverages the established signal-based communication pattern while introducing a dedicated Python executor service for database operations.

**Key Design Decision:** Use a hybrid execution model where Deno continues to orchestrate flow control but delegates actual database writes to Python via a new `EXEC_ODS` signal. This maintains sandbox security while enabling efficient batch processing.

---

## 1. Integration with Existing Deno Runner

### Current Signal Types
The Deno runner (`runner.ts`) currently emits these signals via `console.log`:

| Signal | Format | Purpose |
|--------|--------|---------|
| `NODE_STATUS` | `NODE_STATUS:{node_id}:{status}` | Real-time execution status |
| `NODE_LOG_JSON` | `NODE_LOG_JSON:{json}` | Structured execution logs |
| `FINAL_RESULT` | `FINAL_RESULT:{json}` | Final flow output |
| `EXEC_SQL` | `EXEC_SQL:{conn_id}:{query}` | SQL execution request (placeholder) |

### New Signal: EXEC_ODS

**Format:**
```
EXEC_ODS:{node_id}:{operation}:{connection_id}:{batch_id}
```

**Payload Structure (JSON following signal):**
```json
{
  "node_id": "node-123",
  "operation": "upsert",
  "target": {
    "connection_id": "conn-456",
    "schema": "ods",
    "table": "fact_sales"
  },
  "config": {
    "write_mode": "upsert",
    "identity_fields": ["id", "date"],
    "batch_size": 1000
  },
  "data": [...],
  "metadata": {
    "execution_id": "exec-789",
    "flow_id": "flow-abc",
    "timestamp": "2026-05-16T12:00:00Z"
  }
}
```

### Deno Runner Modification Points

**File:** `backend/app/runtime/runner.ts`

Add new node handler in the main execution loop (around line 503):

```typescript
} else if (node.toolType === 'ods_pg') {
  try {
    const props = node.props || {};
    const connectionId = props.connection_id;
    const schema = props.schema || 'public';
    const table = props.table;
    const writeMode = props.write_mode || 'append';
    const identityFields = props.identity_fields || [];
    const batchSize = parseInt(props.batch_size || '1000', 10);

    if (!connectionId || !table) {
      throw new Error("ODS PostgreSQL requiere connection_id y table");
    }

    // Prepare data from upstream
    const records = Array.isArray(context.payload) ? context.payload : [context.payload];
    
    if (records.length === 0) {
      console.log(`[ODS] No data to write for node ${node.id}`);
      context.payload = { status: 'skipped', rows: 0 };
    } else {
      // Emit signal for Python to handle execution
      const batchId = `batch-${Date.now()}`;
      const odsPayload = {
        node_id: node.id,
        operation: writeMode,
        target: { connection_id: connectionId, schema, table },
        config: { write_mode: writeMode, identity_fields: identityFields, batch_size: batchSize },
        data: records,
        metadata: {
          execution_id: flow.execution_id, // needs to be passed in flow data
          flow_id: flow.flow_id,
          timestamp: new Date().toISOString()
        }
      };
      
      console.log(`EXEC_ODS:${node.id}:${writeMode}:${connectionId}:${batchId}`);
      console.log(`EXEC_ODS_PAYLOAD:${JSON.stringify(odsPayload)}`);
      
      // Python will process and return result via a response mechanism
      // For now, we mark as delegated
      context.payload = { status: 'delegated', operation: writeMode, rows: records.length };
    }
    
    const endMs = Date.now();
    const endTime = new Date(endMs).toISOString();
    console.log(`NODE_LOG_JSON:${JSON.stringify({node_id: node.id, status: 'success', input: currentPayload, output: context.payload, duration: endMs - startMs, start_time: startTime, end_time: endTime})}`);
    emitStatus(node.id, 'success');
  } catch (err: any) {
    // Error handling...
  }
}
```

---

## 2. Python Service Architecture

### New Component: `ods_executor.py`

**Location:** `backend/app/services/ods_executor.py`

**Responsibilities:**
1. Process EXEC_ODS signals from Deno
2. Manage database connections via asyncpg
3. Execute batch operations (Append, Overwrite, Upsert, Merge SCD2)
4. Handle transactions and rollback
5. Report progress and errors back to orchestrator

**Class Structure:**

```python
import asyncpg
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WriteMode(Enum):
    APPEND = "append"
    OVERWRITE = "overwrite"
    UPSERT = "upsert"
    MERGE_SCD2 = "merge"

@dataclass
class ODSConfig:
    connection_id: str
    schema: str
    table: str
    write_mode: WriteMode
    identity_fields: List[str]
    batch_size: int

@dataclass
class ODSResult:
    success: bool
    rows_affected: int
    rows_inserted: int
    rows_updated: int
    errors: List[str]
    duration_ms: int

class ODSExecutor:
    """
    Executes ODS PostgreSQL operations with batch processing,
    transaction management, and error handling.
    """
    
    def __init__(self):
        self._connection_cache: Dict[str, asyncpg.Connection] = {}
    
    async def execute(
        self, 
        config: ODSConfig, 
        records: List[Dict[str, Any]],
        db_session
    ) -> ODSResult:
        """Main entry point for ODS execution."""
        pass
    
    async def _execute_append(self, conn: asyncpg.Connection, config: ODSConfig, records: List[Dict]) -> int:
        """Execute append operation."""
        pass
    
    async def _execute_overwrite(self, conn: asyncpg.Connection, config: ODSConfig, records: List[Dict]) -> int:
        """Execute overwrite operation (truncate + insert)."""
        pass
    
    async def _execute_upsert(self, conn: asyncpg.Connection, config: ODSConfig, records: List[Dict]) -> Dict[str, int]:
        """Execute upsert with conflict resolution."""
        pass
    
    async def _execute_merge_scd2(self, conn: asyncpg.Connection, config: ODSConfig, records: List[Dict]) -> Dict[str, int]:
        """Execute SCD Type 2 merge."""
        pass

# Singleton instance
ods_executor = ODSExecutor()
```

### Integration with DenoService

**File:** `backend/app/services/deno_service.py`

Modify `run_flow_stream` to capture and process EXEC_ODS signals:

```python
async def run_flow_stream(self, flow_data: Dict[str, Any], payload: Optional[Dict] = None):
    # ... existing setup ...
    
    ods_results = {}  # Track ODS execution results
    
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        # Handle EXEC_ODS signal
        if line.startswith("EXEC_ODS:"):
            parts = line.split(":")
            if len(parts) >= 5:
                node_id = parts[1]
                operation = parts[2]
                connection_id = parts[3]
                batch_id = parts[4]
                
                # Next line should contain payload
                # (This requires buffering or lookahead)
                
        elif line.startswith("EXEC_ODS_PAYLOAD:"):
            try:
                ods_payload = json.loads(line[len("EXEC_ODS_PAYLOAD:"):])
                # Execute ODS operation
                result = await self._handle_ods_execution(ods_payload, db)
                ods_results[ods_payload['node_id']] = result
                
                # Emit result back to stream
                yield {"type": "ods_result", "node_id": ods_payload['node_id'], "result": result}
            except Exception as e:
                logger.error(f"ODS execution failed: {e}")
                yield {"type": "error", "message": f"ODS execution failed: {e}"}
                
        # ... existing handlers ...

async def _handle_ods_execution(self, payload: Dict, db) -> Dict:
    """Delegate to ods_executor."""
    from app.services.ods_executor import ODSExecutor, ODSConfig, WriteMode
    
    config = ODSConfig(
        connection_id=payload['target']['connection_id'],
        schema=payload['target']['schema'],
        table=payload['target']['table'],
        write_mode=WriteMode(payload['config']['write_mode']),
        identity_fields=payload['config']['identity_fields'],
        batch_size=payload['config']['batch_size']
    )
    
    executor = ODSExecutor()
    result = await executor.execute(config, payload['data'], db)
    
    return {
        "success": result.success,
        "rows_affected": result.rows_affected,
        "duration_ms": result.duration_ms,
        "errors": result.errors
    }
```

---

## 3. Data Flow Architecture

### Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLOW EXECUTION LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. TRIGGER (WebSocket / Scheduler / API)
   │
   ▼
┌─────────────────┐
│  Flow Endpoint  │  ← Load flow definition from DB
│  /scheduler     │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│  Source Executor         │  ← Pre-execute source nodes (PostgreSQL, MySQL)
│  (source_executor.py)    │     Fetches data, resolves credentials
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐     Signals: NODE_STATUS, NODE_LOG_JSON
│  Deno Runner             │ ──────────────────────────────────────────► UI
│  (runner.ts)             │
│                          │     EXEC_ODS:node-id:upsert:conn-123:batch-1
│  Processes nodes         │ ──────────────────────────────────────────┐
│  sequentially...         │                                         │
└────────┬─────────────────┘                                         │
         │                                                            │
         │ ODS Node Encountered                                       │
         ▼                                                            ▼
┌──────────────────────────┐                          ┌────────────────────────┐
│  Emit EXEC_ODS signal    │                          │  DenoService           │
│  with payload            │─────────────────────────►│  (deno_service.py)     │
│                          │   Intercept signal       │                        │
└──────────────────────────┘                          │  Parse EXEC_ODS        │
                                                      │  Delegate to executor  │
                                                      └────────┬───────────────┘
                                                               │
                                                               ▼
                                                      ┌────────────────────────┐
                                                      │  ODS Executor          │
                                                      │  (ods_executor.py)     │
                                                      │                        │
                                                      │  • Connect to PG       │
                                                      │  • Batch processing    │
                                                      │  • Transaction mgmt    │
                                                      │  • Error handling      │
                                                      └────────┬───────────────┘
                                                               │
                                                               ▼
                                                      ┌────────────────────────┐
                                                      │  PostgreSQL ODS        │
                                                      │  (Target Database)     │
                                                      └────────────────────────┘
                                                               │
                                                               │ Result
                                                               ▼
┌──────────────────────────┐                          ┌────────────────────────┐
│  Continue flow with      │◄─────────────────────────│  Return result to      │
│  result in context       │   Yield ods_result       │  DenoService           │
│  payload                 │                          │                        │
└────────┬─────────────────┘                          └────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Flow completes          │
│  FINAL_RESULT emitted    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Save Execution History  │
│  (ExecutionHistory,      │
│   NodeExecutionLogs)     │
└──────────────────────────┘
```

### Data Flow: Upstream → ODS Executor → PostgreSQL

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW DETAIL                                     │
└────────────────────────────────────────────────────────────────────────────┘

UPSTREAM NODE OUTPUT
│
│  Array of records: [{"id": 1, "name": "A", "value": 100}, ...]
│
▼
┌────────────────────────────────┐
│  Deno Runner Context           │
│  context.payload = records     │
└────────┬───────────────────────┘
         │
         │ ODS Node Execution
         ▼
┌────────────────────────────────┐
│  Prepare ODS Payload           │
│  • Extract records             │
│  • Resolve node props          │
│  • Build metadata              │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Emit EXEC_ODS Signal          │
│  console.log("EXEC_ODS:...")   │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  DenoService Interception      │
│  • Parse signal                │
│  • Extract payload             │
│  • Call ODSExecutor            │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  ODSExecutor.execute()         │
│  • Validate records            │
│  • Get connection config       │
│  • Split into batches          │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Batch Processing Loop         │
│  for batch in batches:         │
│    • Begin transaction         │
│    • Execute write operation   │
│    • Commit / Rollback         │
│    • Log progress              │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  PostgreSQL asyncpg            │
│  • executemany() for batches   │
│  • Conflict resolution         │
│  • RETURNING clause support    │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Return ODSResult              │
│  • rows_affected               │
│  • success/failure             │
│  • errors[]                    │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Yield to WebSocket Stream     │
│  {"type": "ods_result", ...}   │
└────────────────────────────────┘
```

---

## 4. Transaction and Error Handling Strategy

### Transaction Management

**Per-Batch Transactions (Recommended):**

```python
async def _execute_batch_with_transaction(
    self, 
    conn: asyncpg.Connection, 
    query: str, 
    batch: List[tuple],
    batch_number: int
) -> Dict[str, Any]:
    """
    Execute a single batch within a transaction.
    
    Strategy:
    - Each batch is atomic
    - Failed batch rolls back independently
    - Other batches continue processing
    - Partial success is possible
    """
    async with conn.transaction():
        try:
            result = await conn.executemany(query, batch)
            return {
                "batch": batch_number,
                "success": True,
                "rows_affected": result
            }
        except asyncpg.UniqueViolationError as e:
            logger.warning(f"Batch {batch_number}: Unique violation - {e}")
            raise  # Will rollback
        except asyncpg.ForeignKeyViolationError as e:
            logger.error(f"Batch {batch_number}: FK violation - {e}")
            raise  # Will rollback
        except Exception as e:
            logger.error(f"Batch {batch_number}: Unexpected error - {e}")
            raise  # Will rollback
```

**All-or-Nothing Transaction (Alternative):**

```python
async def _execute_all_or_nothing(
    self,
    conn: asyncpg.Connection,
    config: ODSConfig,
    records: List[Dict]
) -> ODSResult:
    """
    Execute all records in a single transaction.
    
    Strategy:
    - Entire operation is atomic
    - Any failure rolls back everything
    - Suitable for small datasets or when consistency is critical
    """
    async with conn.transaction():
        # Truncate if overwrite mode
        if config.write_mode == WriteMode.OVERWRITE:
            await conn.execute(f'TRUNCATE TABLE "{config.schema}"."{config.table}"')
        
        # Process all batches
        for i, batch in enumerate(batches):
            await self._execute_batch(conn, config, batch)
        
        # Single commit at end
```

### Error Handling Strategy

**Error Classification:**

| Error Type | Action | Retry? | Log Level |
|------------|--------|--------|-----------|
| Connection Error | Abort all, notify | Yes (3x) | ERROR |
| Unique Violation | Skip record, continue | No | WARNING |
| FK Violation | Skip record, continue | No | ERROR |
| Type Mismatch | Skip record, continue | No | ERROR |
| Timeout | Retry batch | Yes (3x) | WARNING |
| Unknown | Abort batch, continue | No | ERROR |

**Error Response Structure:**

```python
@dataclass
class ODSError:
    batch_number: int
    error_type: str
    message: str
    record_index: Optional[int]  # Index within batch
    record_preview: Optional[Dict]  # First few fields for identification
    
@dataclass
class ODSResult:
    success: bool  # True if at least one batch succeeded
    complete_success: bool  # True if all batches succeeded
    rows_affected: int
    rows_inserted: int
    rows_updated: int
    batches_total: int
    batches_successful: int
    batches_failed: int
    errors: List[ODSError]
    duration_ms: int
```

### Rollback Strategy

**Automatic (Transaction-Level):**
- Each batch runs in its own transaction
- Failed batch automatically rolls back
- Other batches unaffected

**Manual (Overwrite Mode):**
- For overwrite operations, truncation happens in transaction
- If subsequent insert fails, entire operation rolls back
- Preserves original table data

**Checkpoint Strategy (Future Enhancement):**
```python
# For very large datasets, implement checkpoints
async def _execute_with_checkpoints(...):
    checkpoint_every = 10  # batches
    for i, batch in enumerate(batches):
        await self._execute_batch(...)
        
        if i > 0 and i % checkpoint_every == 0:
            # Log checkpoint for potential resume
            await self._save_checkpoint(execution_id, i, conn)
```

---

## 5. New Components vs Modifications

### New Components (Create)

| Component | File | Purpose |
|-----------|------|---------|
| ODSExecutor | `backend/app/services/ods_executor.py` | Core execution engine for ODS operations |
| ODSResult | `backend/app/services/ods_executor.py` | Result data structure |
| ODSError | `backend/app/services/ods_executor.py` | Error data structure |
| WriteMode | `backend/app/services/ods_executor.py` | Enum for write modes |

### Modified Components (Update)

| Component | File | Changes |
|-----------|------|---------|
| Deno Runner | `backend/app/runtime/runner.ts` | Add `ods_pg` node handler, emit EXEC_ODS signal |
| DenoService | `backend/app/services/deno_service.py` | Capture EXEC_ODS, delegate to ODSExecutor |
| Destination Executor | `backend/app/services/destination_executor.py` | Deprecate or redirect to ODSExecutor |
| Scheduler | `backend/app/services/scheduler.py` | Ensure ODS execution in scheduled flows |
| Integration Flows API | `backend/app/api/endpoints/integration_flows.py` | Handle ODS results in WebSocket stream |

### Unchanged Components

| Component | Reason |
|-----------|--------|
| MetadataService | Already supports PostgreSQL schema inspection |
| SourceExecutor | Source nodes remain unchanged |
| Models | ODS node already defined in editor_tools |
| Frontend ODS Node UI | Already implemented in Phase 30 |

---

## 6. Suggested Build Order

### Phase 1: Foundation (Week 1)

**Objective:** Core ODSExecutor with basic operations

**Tasks:**
1. Create `ods_executor.py` with:
   - Class structure and data models
   - Database connection management
   - Append operation implementation
   - Basic error handling

2. Write unit tests for ODSExecutor:
   - Mock PostgreSQL with testing.postgresql
   - Test append operation
   - Test error scenarios

**Deliverable:** ODSExecutor service with append operation working

### Phase 2: Deno Integration (Week 1-2)

**Objective:** Connect Deno runner to ODSExecutor

**Tasks:**
1. Modify `runner.ts`:
   - Add `ods_pg` node handler
   - Emit EXEC_ODS signal
   - Format payload correctly

2. Modify `deno_service.py`:
   - Parse EXEC_ODS signal
   - Extract and validate payload
   - Call ODSExecutor
   - Yield results back to stream

3. Integration test:
   - End-to-end flow with simple append
   - WebSocket streaming verification

**Deliverable:** Full flow execution from Deno through to PostgreSQL

### Phase 3: Advanced Operations (Week 2)

**Objective:** Complete write mode implementations

**Tasks:**
1. Implement overwrite operation
2. Implement upsert with composite keys
3. Implement Merge SCD2 (if time permits, else Phase 4)

4. Enhance transaction management:
   - Per-batch transactions
   - All-or-nothing option
   - Rollback testing

**Deliverable:** All write modes functional

### Phase 4: Error Handling & Polish (Week 3)

**Objective:** Production-ready error handling and monitoring

**Tasks:**
1. Comprehensive error classification
2. Retry logic with backoff
3. Detailed logging per batch
4. Progress reporting for large datasets
5. Update ExecutionHistory with ODS-specific metadata

6. Deprecate legacy destination_executor.py

**Deliverable:** Production-ready ODS Execution Engine

### Phase 5: Performance & Scale (Future)

**Objective:** Handle large datasets efficiently

**Tasks:**
1. Connection pooling
2. Parallel batch processing
3. Checkpoint/resume capability
4. Streaming for very large datasets

---

## 7. API Contract

### Deno → Python (EXEC_ODS Signal)

**Signal Format:**
```
EXEC_ODS:{node_id}:{operation}:{connection_id}:{batch_id}
EXEC_ODS_PAYLOAD:{json_payload}
```

**Payload Schema:**
```typescript
interface ODSExecutionPayload {
  node_id: string;
  operation: 'append' | 'overwrite' | 'upsert' | 'merge';
  target: {
    connection_id: string;
    schema: string;
    table: string;
  };
  config: {
    write_mode: string;
    identity_fields: string[];
    batch_size: number;
  };
  data: any[];
  metadata: {
    execution_id: string;
    flow_id: string;
    timestamp: string;
  };
}
```

### Python → UI (WebSocket Response)

**Success Response:**
```json
{
  "type": "ods_result",
  "node_id": "node-123",
  "result": {
    "success": true,
    "complete_success": true,
    "rows_affected": 5000,
    "rows_inserted": 3000,
    "rows_updated": 2000,
    "batches_total": 5,
    "batches_successful": 5,
    "batches_failed": 0,
    "errors": [],
    "duration_ms": 1250
  }
}
```

**Partial Success Response:**
```json
{
  "type": "ods_result",
  "node_id": "node-123",
  "result": {
    "success": true,
    "complete_success": false,
    "rows_affected": 4800,
    "batches_total": 5,
    "batches_successful": 4,
    "batches_failed": 1,
    "errors": [
      {
        "batch_number": 3,
        "error_type": "UniqueViolationError",
        "message": "duplicate key value violates unique constraint",
        "record_count": 200
      }
    ]
  }
}
```

---

## 8. Testing Strategy

### Unit Tests

```python
# Test ODSExecutor operations
async def test_ods_executor_append():
    executor = ODSExecutor()
    config = ODSConfig(...)
    records = [{"id": 1, "name": "test"}]
    
    result = await executor.execute(config, records, mock_db)
    
    assert result.success
    assert result.rows_affected == 1
```

### Integration Tests

```python
# Test end-to-end flow execution
async def test_flow_with_ods_node():
    flow_data = {
        "nodes": [
            {"id": "source-1", "toolType": "sql_source", ...},
            {"id": "ods-1", "toolType": "ods_pg", ...}
        ],
        "connections": [{"from": "source-1", "to": "ods-1"}]
    }
    
    async for log in deno_service.run_flow_stream(flow_data):
        if log["type"] == "ods_result":
            assert log["result"]["success"]
```

---

## 9. Security Considerations

1. **SQL Injection Prevention:**
   - Use asyncpg parameterized queries exclusively
   - Quote identifiers using asyncpg's built-in methods
   - Never interpolate table/column names without validation

2. **Credential Security:**
   - Credentials resolved via existing DataSource mechanism
   - Decryption happens in source_executor.py pattern
   - No credentials in Deno payload

3. **Resource Limits:**
   - Batch size limits (max 10,000)
   - Connection timeouts (15s default)
   - Query timeout configuration

---

## 10. Migration Path

### From Legacy destination_executor.py

The existing `destination_executor.py` has basic ODS support. Migration strategy:

1. **Phase 1:** Keep destination_executor.py, add ods_executor.py alongside
2. **Phase 2:** Update deno_service.py to use ODSExecutor instead
3. **Phase 3:** Deprecate destination_executor.py ODS logic
4. **Phase 4:** Remove or repurpose destination_executor.py

---

## Sources

- Existing codebase analysis:
  - `backend/app/runtime/runner.ts` - Deno runner
  - `backend/app/services/deno_service.py` - Python Deno integration
  - `backend/app/services/source_executor.py` - Source node execution pattern
  - `backend/app/services/destination_executor.py` - Existing destination logic
  - `backend/app/services/metadata_service.py` - PostgreSQL connection pattern
  - `backend/app/api/endpoints/integration_flows.py` - Flow execution API
  - `backend/app/services/scheduler.py` - Background execution
  - `backend/alembic/versions/030_update_ods_pg_tool.py` - ODS node schema

**Confidence Level:** HIGH - Based on direct analysis of existing production codebase.

---

# Appendix: Email Node with Dynamic Templates Architecture

**Milestone:** v1.7 Email Node with Dynamic Templates  
**Scope:** Integration of full Email Node capabilities with Deno-Python architecture

## Email Node Executive Summary

The Email Node will integrate with the existing Deno-Python hybrid architecture using a **signal-based execution pattern** similar to the ODS PostgreSQL implementation. The Deno runner will emit an `EXEC_EMAIL` signal that the Python backend captures and processes using SMTP credentials from the encrypted DataSource system. Template resolution with `{{expression}}` syntax is already implemented in the Deno runner and will be reused for subject and body rendering.

**Key architectural decisions:**
1. **Signal-based execution** (not direct Deno SMTP) - credentials stay in Python, templates render in Deno
2. **HTML + Text dual format** - supporting both HTML emails with table generation and plain text fallback
3. **Template engine reuse** - leverage existing `resolveString()` in runner.ts
4. **Security-first** - HTML sanitization in Python before SMTP transmission

---

## Email Integration with Deno Runner

### Current State
The Deno runner (`backend/app/runtime/runner.ts`) already has an email stub (lines 475-502):

```typescript
} else if (node.toolType === 'email') {
  try {
    const to = node.props?.to || 'admin@company.com';
    const subject = node.props?.subject || 'Flow Notification';
    const body = node.props?.body || `Flow execution result: ${JSON.stringify(context.payload, null, 2)}`;
    const triggerOn = node.props?.trigger_on || 'success';
    
    console.log(`[Email] Mock Sending Email...`);
    // ... mock implementation
  }
}
```

### Proposed EXEC_EMAIL Signal Pattern

Use the **EXEC_ODS signal pattern** as a blueprint:

```
Deno Runner                              Python Backend
    |                                         |
    |-- EXEC_EMAIL:{node_id}:{batch_id} ---->|
    |-- EXEC_EMAIL_PAYLOAD:{json} ---------->|
    |                                         |-- Resolve SMTP creds
    |                                         |-- Render templates
    |                                         |-- Sanitize HTML
    |                                         |-- Send via SMTP
    |<----------------------------------------|-- Return result
```

### Signal Protocol

```typescript
// In runner.ts - Email node execution
const emailPayload = {
  node_id: node.id,
  target: {
    connection_id: props.connection_id,  // SMTP DataSource ID
    to: resolveString(props.to, context),
    cc: resolveString(props.cc || '', context),
    bcc: resolveString(props.bcc || '', context),
  },
  content: {
    subject: resolveString(props.subject, context),
    body: resolveString(props.body, context),  // HTML or text
    format: props.format || 'html',  // 'html' | 'text'
    generate_table: props.generate_table || false,
  },
  metadata: {
    execution_id: flow.execution_id,
    flow_id: flow.flow_id,
    node_label: node.label,
    timestamp: new Date().toISOString()
  }
};

console.log(`EXEC_EMAIL:${node.id}:${batchId}`);
console.log(`EXEC_EMAIL_PAYLOAD:${JSON.stringify(emailPayload)}`);
```

---

## Email Template Compilation and Rendering Flow

### Existing Template Engine

The runner.ts has `resolveString()` (lines 44-59):

```typescript
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
```

### Template Resolution Flow

```
Upstream Node Output
[{"customer": "ACME", "amount": 1500}, ...]
         |
         | context.payload
         v
Email Node Template Resolution

Subject: "Sales Report - {{date}}"
Body: "<h1>Top Customers</h1>{{table}}"

resolveString() -> "Sales Report - 2026-05-16"
         |
         v
Special Helper: Table Generation

If {{table}} placeholder detected and payload is array:
Auto-generate HTML table from first object's keys as headers
         |
         | EXEC_EMAIL_PAYLOAD
         v
Python Backend
- Resolve SMTP connection from DataSource
- Sanitize HTML content
- Send email via smtplib
```

### Template Syntax Support

| Syntax | Example | Output |
|--------|---------|--------|
| Simple property | `{{customer}}` | Value of customer field |
| Nested property | `{{order.total}}` | Nested object access |
| Array index | `{{items.0.name}}` | First item's name |
| Special helpers | `{{table}}` | Auto-generated HTML table |
| Fallback | `{{name or "Guest"}}` | Default value if undefined |

---

## Email Service Architecture

### New Components for Email

```
backend/
├── app/
│   ├── services/
│   │   ├── deno_service.py          (MODIFY) - Add EXEC_EMAIL handler
│   │   ├── email_executor.py        (NEW)    - SMTP execution service
│   │   └── connection_testing.py    (EXISTS) - Already has SmtpStrategy
│   ├── schemas/
│   │   └── email_schemas.py         (NEW)    - Email payload validation
│   └── runtime/
│       └── runner.ts                (MODIFY) - EXEC_EMAIL signal emission
```

### EmailExecutor Service

```python
# backend/app/services/email_executor.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

@dataclass
class EmailConfig:
    connection_id: str
    smtp_host: str
    smtp_port: int
    smtp_use_ssl: bool
    smtp_user: str
    smtp_password: str
    from_address: str

@dataclass
class EmailResult:
    success: bool
    message_id: Optional[str]
    error: Optional[str]
    recipients_count: int
    duration_ms: int

class EmailExecutor:
    async def execute(
        self,
        config: EmailConfig,
        to_addresses: List[str],
        cc_addresses: List[str],
        bcc_addresses: List[str],
        subject: str,
        body_html: Optional[str],
        body_text: Optional[str]
    ) -> EmailResult:
        """
        Execute email send via SMTP.
        - Sends both HTML and text parts (multipart/alternative)
        - Sanitizes HTML before sending
        - Handles SMTP authentication
        """
        pass
    
    def _sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML to prevent XSS in email clients.
        Uses bleach or similar library.
        """
        pass
    
    def _generate_table(self, data: List[Dict]) -> str:
        """
        Generate HTML table from array of objects.
        Called when {{table}} helper is used.
        """
        pass

email_executor = EmailExecutor()
```

### Signal Handler in DenoService

```python
# backend/app/services/deno_service.py - Add to run_flow_stream()

# Handle EXEC_EMAIL signal (similar to EXEC_ODS)
if line.startswith("EXEC_EMAIL:") and i + 1 < len(lines):
    parts = line.split(":")
    if len(parts) >= 3:
        node_id = parts[1]
        batch_id = parts[2]
        
        next_line = lines[i + 1].strip()
        if next_line.startswith("EXEC_EMAIL_PAYLOAD:"):
            i += 1
            try:
                email_payload = json.loads(next_line[len("EXEC_EMAIL_PAYLOAD:"):])
                
                # Yield status update
                yield {
                    "type": "node_log",
                    "node_id": node_id,
                    "status": "running",
                    "message": "Sending email..."
                }
                
                # Execute email if db session available
                if db is not None:
                    email_result = await self._handle_email_execution(email_payload, db)
                    
                    yield {
                        "type": "email_result",
                        "node_id": node_id,
                        "batch_id": batch_id,
                        "result": email_result
                    }
                    
                    if email_result["success"]:
                        yield {"type": "node_status", "node_id": node_id, "status": "success"}
                    else:
                        yield {"type": "node_status", "node_id": node_id, "status": "error"}
                else:
                    yield {
                        "type": "error",
                        "message": "No database session available for email execution"
                    }
            except Exception as e:
                logger.error(f"Email execution error: {e}")
                yield {"type": "error", "message": f"Email execution failed: {e}"}
```

---

## Email Security Considerations

### HTML Sanitization

**Threat:** HTML email can contain malicious scripts, tracking pixels, or phishing elements.

**Solution:**
```python
import bleach

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span', 'pre', 'code', 'blockquote'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing'],
    'th': ['colspan', 'rowspan'],
    'td': ['colspan', 'rowspan'],
}

def sanitize_html(html: str) -> str:
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Remove disallowed tags completely
    )
```

### Template Injection Prevention

**Threat:** Malicious templates with code execution attempts

**Mitigation:**
- Deno's `resolveString()` only does property access, no code execution
- Context isolation - template only accesses `context.payload` data
- No `eval()` or `new Function()` in template resolution

### SMTP Security

**Requirements:**
- Credentials stored encrypted in DataSource (already implemented)
- Use TLS/SSL for SMTP connections (`use_ssl` flag in SmtpConfig)
- Timeout on SMTP operations (10s default)
- No credential logging

---

## Email Node: New vs Modified Components

### New Components

| Component | Purpose | Lines Est. |
|-----------|---------|------------|
| `email_executor.py` | SMTP execution service | ~200 |
| `email_schemas.py` | Email payload Pydantic models | ~50 |
| Migration for tool update | Add connection_id, body, format props | ~30 |

### Modified Components

| Component | Changes | Lines Est. |
|-----------|---------|------------|
| `runner.ts` | Add EXEC_EMAIL signal emission | ~60 |
| `deno_service.py` | Add _handle_email_execution() method | ~80 |
| Tool definition (DB) | Add connection_id, body, format, cc, bcc props | ~20 |
| FlowEditorCanvas.vue | Add connection selector for email nodes | ~30 |

### No Changes Required

| Component | Why |
|-----------|-----|
| `connection_testing.py` | SmtpStrategy already exists |
| `connection_schemas.py` | SmtpConfig already exists |
| DataSource system | SMTP connections already supported |
| Template engine | `resolveString()` already handles `{{}}` syntax |

---

## Email Node Build Order

### Phase 1: Foundation (Week 1)

**Goal:** Get basic email sending working

1. **Update email tool definition** (DB migration)
   - Add `connection_id` prop (required)
   - Add `body` prop (textarea, supports HTML)
   - Add `format` prop (select: 'html' | 'text')
   - Add `cc`, `bcc` props (optional)

2. **Create email_schemas.py**
   - EmailPayload model
   - EmailResult model
   - EmailConfig model

3. **Create email_executor.py**
   - Basic SMTP sending
   - HTML sanitization
   - Error handling

### Phase 2: Deno Integration (Week 1-2)

**Goal:** Connect Deno runner to Python executor

4. **Update runner.ts**
   - Add EXEC_EMAIL signal emission
   - Template resolution for to/subject/body

5. **Update deno_service.py**
   - Add EXEC_EMAIL signal handler
   - Integrate with EmailExecutor

### Phase 3: Advanced Features (Week 2)

**Goal:** Add dynamic content generation

6. **Add table generation helper**
   - Detect `{{table}}` placeholder
   - Generate HTML table from array payload
   - Handle empty/null data gracefully

7. **Add FlowEditorCanvas.vue enhancements**
   - Connection selector for SMTP
   - Rich text editor for body (optional)
   - Preview template button

### Phase 4: Testing & Polish (Week 3)

8. **Security hardening**
   - HTML sanitization tests
   - Template injection tests
   - SMTP timeout tests

9. **Error handling**
   - Invalid connection ID
   - SMTP authentication failure
   - Template syntax errors

---

## Email Node Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SMTP credentials exposure | Low | High | Use existing encrypted DataSource system |
| HTML injection in emails | Medium | Medium | Bleach sanitization before send |
| Template syntax errors | High | Low | Graceful fallback (keep placeholder) |
| SMTP timeouts | Medium | Medium | 10s timeout, async execution |
| Large payload table generation | Medium | Medium | Limit table rows (100 max) |

---

## Email Node Sources

- `backend/app/runtime/runner.ts` - Deno execution model
- `backend/app/services/deno_service.py` - Signal handling pattern
- `backend/app/services/ods_executor.py` - Executor service pattern (follow same structure)
- `backend/app/services/connection_testing.py` - SMTP connection testing
- `backend/alembic/versions/008_add_integration_tables.py` - Tool definitions
- `backend/app/schemas/connection_schemas.py` - SMTP config schema
