# Technology Stack: ODS Execution Engine

**Project:** Dashboard Studio - ODS Execution Engine  
**Researched:** 2026-05-16  
**Confidence:** HIGH  

## Executive Summary

The ODS Execution Engine requires additional Python libraries for efficient PostgreSQL bulk operations and SCD2 (Slowly Changing Dimensions Type 2) support. The existing stack already includes `asyncpg` which is well-suited for the task. No new major dependencies are required - the focus is on utilizing existing libraries more effectively and adding SCD2-specific SQL patterns.

**Key Decision:** Continue using `asyncpg` (already in dependencies) for all PostgreSQL operations due to its superior async performance and native PostgreSQL protocol implementation. Add `psycopg[binary]` (v3) as a secondary option for COPY operations if needed.

---

## Recommended Stack Additions

### Core PostgreSQL Driver (No Change Required)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **asyncpg** | ^0.30.0 | Async PostgreSQL driver | Already in stack; fastest Python PostgreSQL driver; native protocol implementation; excellent for bulk operations via `executemany()` |
| **psycopg** | ^3.2.0 | Alternative PostgreSQL driver | Consider adding for COPY operations if `COPY FROM` performance becomes critical; has superior COPY API |

**Decision Rationale:**
- `asyncpg` is already integrated (v0.29.0 in pyproject.toml)
- Upgrade to v0.30.0 recommended for latest bug fixes and Python 3.13 support
- Keep `psycopg2-binary` for existing SQLAlchemy sync operations but consider migrating to `psycopg` v3 for new code
- `asyncpg` outperforms psycopg2 by 2-5x for bulk inserts

### Batch Processing Libraries

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| **pandas** | ^2.2.0 | Data manipulation for SCD2 | Required for SCD2 merge operations; efficient column-wise operations |
| **numpy** | ^2.0.0 | Numerical operations | Comes with pandas; used for efficient data transformations |

**Decision Rationale:**
- Pandas provides efficient DataFrame operations needed for SCD2 logic (hash comparisons, date range management)
- For simple Append/Overwrite/Upsert operations, pandas is optional - pure asyncpg is sufficient
- SCD2 requires detecting changes between incoming and existing data - pandas simplifies this

### Connection Pooling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **asyncpg.Pool** | Built-in | Connection pooling | Native to asyncpg; production-ready; automatic reconnection |

**Decision Rationale:**
- No additional pooling library needed (asyncpg has built-in pool)
- Use `asyncpg.create_pool()` for ODS operations to handle concurrent batch processing

---

## Integration Patterns

### Deno-to-PPython Communication

Based on existing codebase analysis (`deno_service.py`, `destination_executor.py`):

```
┌─────────────┐     EXECUTE_FLOW      ┌─────────────────┐
│   Deno      │ ────────────────────► │  Python         │
│  Runner     │   (subprocess)        │  ODSExecutor    │
│             │                       │                 │
│  • Executes │◄──────────────────────│  • Receives     │
│    flow     │   NODE_LOG_JSON       │    JSON payload │
│  • Detects  │   signals             │  • Processes    │
│    ods_pg   │                       │    batches      │
│    nodes    │◄──────────────────────│  • Returns      │
│             │   progress updates    │    status       │
└─────────────┘                       └─────────────────┘
```

**Current Pattern (from `deno_service.py`):**

1. Deno runner executes flow via subprocess (`run_flow_stream`)
2. Python pre-executes source nodes before Deno (`source_executor.py`)
3. Python post-executes destination nodes after Deno (`destination_executor.py`)
4. Communication via stdout/stderr with prefixed messages:
   - `NODE_STATUS:node_id:status`
   - `NODE_LOG_JSON:{...}`
   - `FINAL_RESULT:{...}`

**Recommended Extension for ODS:**

Add new signal pattern for real-time ODS delegation:

```
EXEC_ODS:{
  "node_id": "...",
  "connection_config": {...},
  "operation": "upsert|append|overwrite|merge",
  "data": [...],
  "identity_fields": [...],
  "batch_size": 1000
}
```

Python side receives via stdin or websocket and streams back progress:
```
ODS_PROGRESS:node_id:batch_num:rows_processed
ODS_COMPLETE:node_id:total_rows
ODS_ERROR:node_id:error_message
```

### Batch Processing Strategy

**For Append/Overwrite Operations:**

```python
# Using asyncpg executemany (fastest)
async def batch_append(conn, table, columns, records, batch_size=1000):
    query = f'INSERT INTO {table} ({cols}) VALUES ({placeholders})'
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        values = [[r[c] for c in columns] for r in batch]
        await conn.executemany(query, values)
        yield len(batch)  # Progress update
```

**For Upsert with Multiple Identity Fields:**

```python
# Using ON CONFLICT with composite keys
conflict_cols = ", ".join(f'"{c}"' for c in identity_fields)
update_cols = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in columns if c not in identity_fields)

query = f'''
    INSERT INTO "{schema}"."{table}" ({cols_quoted}) 
    VALUES ({placeholders}) 
    ON CONFLICT ({conflict_cols}) 
    DO UPDATE SET {update_cols}
'''
await conn.executemany(query, vals)
```

**For SCD2 Merge:**

```python
# Requires multiple steps:
# 1. Identify existing active records
# 2. Hash compare with incoming data
# 3. Close expired records (set end_date)
# 4. Insert new records with start_date

# Pandas approach for change detection:
import pandas as pd

existing_df = await fetch_active_records(conn, table, identity_fields)
incoming_df = pd.DataFrame(records)

# Detect changes
merged = incoming_df.merge(
    existing_df, 
    on=identity_fields, 
    how='left', 
    suffixes=('', '_existing')
)

# Hash comparison for non-key fields
changes = merged[merged['hash'] != merged['hash_existing']]
```

---

## Architecture Recommendations

### File Structure

```
backend/app/services/
├── ods_executor.py          # Main entry point for ODS operations
├── ods_operations.py        # Operation implementations (Append, Overwrite, Upsert, Merge)
├── scd2_handler.py          # SCD2-specific logic
└── batch_processor.py       # Generic batch processing utilities
```

### Class Design

```python
# ods_operations.py
from abc import ABC, abstractmethod
import asyncpg

class ODSOperation(ABC):
    def __init__(self, connection_config: dict, batch_size: int = 1000):
        self.config = connection_config
        self.batch_size = batch_size
        self.pool = None
    
    async def __aenter__(self):
        self.pool = await asyncpg.create_pool(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            password=self.config['password'],
            database=self.config['database'],
            min_size=1, max_size=5
        )
        return self
    
    async def __aexit__(self, *args):
        await self.pool.close()
    
    @abstractmethod
    async def execute(self, table: str, records: list) -> dict:
        pass

class AppendOperation(ODSOperation):
    async def execute(self, schema: str, table: str, records: list) -> dict:
        # Implementation
        pass

class UpsertOperation(ODSOperation):
    def __init__(self, *args, identity_fields: list, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_fields = identity_fields
    
    async def execute(self, schema: str, table: str, records: list) -> dict:
        # Implementation with ON CONFLICT
        pass

class SCD2MergeOperation(ODSOperation):
    async def execute(self, schema: str, table: str, records: list) -> dict:
        # Complex SCD2 logic with transaction
        pass
```

---

## Performance Characteristics

### Throughput Benchmarks (Estimated)

| Operation | Method | Rows/sec | Notes |
|-----------|--------|----------|-------|
| Append | asyncpg executemany | 50K-100K | 1000-row batches optimal |
| Overwrite | TRUNCATE + executemany | 40K-80K | TRUNCATE is fast, bottleneck is insert |
| Upsert | ON CONFLICT executemany | 20K-40K | Index lookup overhead |
| SCD2 Merge | Multi-step pandas | 5K-15K | Complex joins and updates |
| Bulk Copy | COPY FROM | 100K-500K | If psycopg3 used |

**Recommendations:**
- Default batch size: **1000 rows** (good balance of memory/speed)
- For >100K rows: Use streaming/chunking to avoid memory issues
- For SCD2: Consider staging table approach for very large datasets

---

## Implementation Checklist

### Phase 1: Basic Operations (Append, Overwrite, Upsert)

- [ ] Upgrade asyncpg to ^0.30.0
- [ ] Create `ODSOperation` base class
- [ ] Implement `AppendOperation` with executemany
- [ ] Implement `OverwriteOperation` (TRUNCATE + insert)
- [ ] Implement `UpsertOperation` with ON CONFLICT
- [ ] Add batch size configuration
- [ ] Implement progress streaming via stdout
- [ ] Add error handling with partial batch rollback

### Phase 2: SCD2 Merge

- [ ] Add pandas dependency
- [ ] Design SCD2 table structure (start_date, end_date, is_current, hash)
- [ ] Implement hash generation for change detection
- [ ] Implement staging table approach
- [ ] Handle transaction boundaries
- [ ] Add SCD2 metadata columns automatically

### Phase 3: Deno Integration

- [ ] Extend deno runner with `EXEC_ODS` signal
- [ ] Create Python ODS executor entry point
- [ ] Implement streaming progress protocol
- [ ] Add timeout handling for large datasets
- [ ] Test concurrent ODS operations

---

## Dependencies Update

### pyproject.toml Changes

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "asyncpg>=0.30.0",        # Upgrade from 0.29.0
    "psycopg[binary]>=3.2.0", # Optional: for COPY if needed
    "pandas>=2.2.0",          # Required for SCD2
    "numpy>=2.0.0",           # Pandas dependency
]
```

### Installation Commands

```bash
# Core ODS dependencies
uv add "asyncpg>=0.30.0"
uv add "psycopg[binary]>=3.2.0"  # Optional
uv add "pandas>=2.2.0"
```

---

## Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| **psycopg3 only** | Unified sync/async API, better COPY | Slower bulk inserts than asyncpg | Not chosen - asyncpg superior for bulk |
| **SQLAlchemy Core** | ORM consistency, query builder | 2-3x slower than raw asyncpg | Not chosen for bulk ops, keep for metadata |
| **aiopg** | asyncio support | Unmaintained, slower | Rejected |
| **pgcopy** | Very fast binary COPY | External dependency, complex | Consider later if needed |
| **Apache Arrow** | High-performance columnar | Heavy dependency, complex | Overkill for current needs |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Memory exhaustion with large datasets | Medium | High | Implement streaming/chunking; configurable batch sizes |
| Deadlocks on Upsert (high concurrency) | Low | High | Use appropriate isolation level; retry logic |
| SCD2 performance with millions of rows | Medium | Medium | Implement staging table pattern; consider incremental loads |
| Deno-Python communication failures | Low | High | Add retry logic; fallback to synchronous execution |
| PostgreSQL connection pool exhaustion | Low | Medium | Proper pool sizing; connection timeouts |

---

## Sources

### Official Documentation

1. **asyncpg Documentation** - https://magicstack.github.io/asyncpg/current/
   - HIGH confidence: Native PostgreSQL protocol implementation
   - Used for: Connection pooling, executemany, transactions

2. **psycopg3 Documentation** - https://www.psycopg.org/psycopg3/docs/
   - HIGH confidence: Official PostgreSQL adapter for Python
   - Used for: COPY operations, alternative driver comparison

3. **PostgreSQL INSERT ON CONFLICT** - https://www.postgresql.org/docs/current/sql-insert.html
   - HIGH confidence: Official PostgreSQL documentation
   - Used for: Upsert syntax, DO UPDATE SET patterns

4. **SQLAlchemy PostgreSQL Dialect** - https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
   - HIGH confidence: Authoritative ORM documentation
   - Used for: Integration patterns, dialect features

### Existing Codebase References

5. **destination_executor.py** - Lines 1-119
   - Current implementation uses asyncpg executemany
   - Identity fields handling with ON CONFLICT

6. **source_executor.py** - Lines 1-214
   - asyncpg connection patterns
   - Pre-execution flow for data sources

7. **deno_service.py** - Lines 1-250
   - Subprocess execution patterns
   - Streaming output protocol

---

## Summary for Roadmap

**No new stack research required** - All necessary libraries are either:
1. Already in the project (asyncpg)
2. Standard choices (pandas for SCD2)
3. Optional additions (psycopg3 for COPY)

**Integration complexity: LOW-MEDIUM**
- Pattern already established (pre/post execution)
- Only need to extend existing Deno-Python protocol
- Most complexity is in SQL logic, not stack choices

**Recommended phase order:**
1. Upgrade asyncpg, implement Append/Overwrite/Upsert (1-2 days)
2. Implement SCD2 with pandas (2-3 days)
3. Integrate with Deno runner (1 day)

**Dependencies to add:** pandas, optional psycopg3
**Risk level:** Low - well-established patterns and libraries
