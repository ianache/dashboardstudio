# Feature Landscape: ODS PostgreSQL Execution Engine

**Domain:** Data Integration / ETL Operations  
**Researched:** 2026-05-16  
**Context:** Dashboard Studio - ODS Execution Engine (Phase 31)

---

## Executive Summary

ODS (Operational Data Store) PostgreSQL execution engines handle the critical final step in data integration flows: persisting transformed data to PostgreSQL tables. Based on research of PostgreSQL capabilities (INSERT ON CONFLICT since 9.5, MERGE since 15), SQLAlchemy patterns, and industry ETL best practices, this document outlines table stakes versus differentiators for the Dashboard Studio ODS execution engine.

**Key Finding:** The four write modes (Append, Overwrite, Upsert, Merge/SCD2) form a complexity progression. Append and Overwrite are table stakes and straightforward. Upsert requires conflict resolution logic and is essential for most real-world use cases. Merge (SCD2) is the most complex, requiring versioning columns and historical tracking—suitable for v2 unless explicitly required.

---

## Table Stakes Features (Must-Have for v1)

Features users expect. Missing = product feels incomplete.

### 1. Append Mode
**What:** Insert all incoming rows without checking for existing data.

**Expected Behavior:**
- Simple `INSERT INTO table (...) VALUES (...)` for each batch
- No conflict checking or duplicate handling
- Fastest write mode, suitable for event logs, time-series data, append-only tables
- Row count returned for logging

**Complexity:** Low

**Dependencies:** 
- Batch size configuration (already exists)
- Connection management (already exists)

**PostgreSQL Implementation:**
```sql
INSERT INTO target_table (col1, col2, col3) 
VALUES (%s, %s, %s), (%s, %s, %s), ...
```

---

### 2. Overwrite Mode
**What:** Delete existing table contents before inserting new data.

**Expected Behavior:**
- **TRUNCATE** approach (fastest): `TRUNCATE TABLE` followed by INSERT
- Alternative: `DELETE FROM table` (slower, but works with FK constraints)
- Atomic operation: Either all old data is removed and new data inserted, or nothing changes
- Row counts: deleted count + inserted count

**Complexity:** Low-Medium

**Dependencies:**
- Transaction support for atomicity
- Batch size configuration

**PostgreSQL Implementation:**
```sql
BEGIN;
TRUNCATE TABLE target_table;
INSERT INTO target_table (...) VALUES (...), (...), ...;
COMMIT;
```

**Decision Point:** TRUNCATE vs DELETE
- Use TRUNCATE for speed (no row-by-row logging)
- Use DELETE if table has FK references or triggers that need firing
- **Recommendation:** Support both via configuration, default to TRUNCATE

---

### 3. Upsert Mode (Insert or Update)
**What:** Insert rows; if conflict on identity fields, update existing row with new values.

**Expected Behavior:**
- Uses PostgreSQL `ON CONFLICT DO UPDATE` syntax
- Identity fields (one or multiple columns) define uniqueness
- Update all non-identity columns when conflict detected
- Return counts: inserted rows vs updated rows

**Complexity:** Medium

**Dependencies:**
- Identity fields selection (already exists in UI)
- Unique constraint/index on identity fields (must exist in DB)
- Batch processing with conflict detection

**PostgreSQL Implementation:**
```sql
INSERT INTO target_table (id, name, email, updated_at)
VALUES (%s, %s, %s, %s), (%s, %s, %s, %s), ...
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    updated_at = EXCLUDED.updated_at;
```

**Critical Requirement:** 
- Target table MUST have a UNIQUE constraint or index on identity fields
- If missing, operation should fail with clear error message

**Multi-Column Identity Support:**
```sql
ON CONFLICT (col1, col2) DO UPDATE SET ...
```

---

### 4. Batch Processing
**What:** Process data in configurable batch sizes to manage memory and transaction size.

**Expected Behavior:**
- Configurable batch size (e.g., 100, 1000, 10000 rows)
- Each batch is a separate transaction or savepoint
- Progress tracking (batches completed/total)
- On error: option to fail immediately or continue with next batch

**Complexity:** Low (already exists in infrastructure)

**Dependencies:**
- Existing batch size configuration in node properties
- Execution history/logging infrastructure (already exists)

**Best Practices:**
- Default: 1000 rows per batch (balance between speed and memory)
- Large batches = faster overall, but higher memory usage
- Small batches = lower memory, more frequent commits

---

### 5. Execution Logging
**What:** Detailed logging of ODS operations for auditing and debugging.

**Expected Behavior:**
- Rows processed, inserted, updated, deleted counts
- Execution duration per batch and total
- Error messages with row context when possible
- Integration with existing execution history system

**Complexity:** Low (builds on existing infrastructure)

**Dependencies:**
- Execution history table (already exists)
- Node execution logs (already exists)

---

## Differentiators (Could be v2)

Features that set the product apart. Not expected, but valued.

### 1. Merge Mode (SCD Type 2 - Slowly Changing Dimension)
**What:** Track historical changes by versioning rows instead of overwriting.

**Expected Behavior:**
- When identity matches but data differs: expire old record, insert new active record
- Maintain effective_date, expiration_date, is_current flags
- Historical audit trail preserved
- Support for both "soft delete" (mark expired) and hard delete

**Complexity:** High

**Implementation Approach:**
```sql
-- Requires SCD2 columns: valid_from, valid_to, is_current

-- 1. Expire existing records that have changed
UPDATE target_table 
SET valid_to = CURRENT_TIMESTAMP, is_current = false
WHERE (id) IN (SELECT id FROM staging_data)
AND is_current = true
AND (col1, col2, col3) IS DISTINCT FROM (staging.col1, staging.col2, staging.col3);

-- 2. Insert new records (both new and changed)
INSERT INTO target_table (id, col1, col2, col3, valid_from, valid_to, is_current)
SELECT id, col1, col2, col3, CURRENT_TIMESTAMP, NULL, true
FROM staging_data
WHERE NOT EXISTS (
    SELECT 1 FROM target_table 
    WHERE target_table.id = staging_data.id 
    AND target_table.is_current = true
    AND target_table.col1 = staging_data.col1
    AND target_table.col2 = staging_data.col2
    AND target_table.col3 = staging_data.col3
);
```

**Requirements:**
- SCD2 metadata columns (valid_from, valid_to, is_current)
- Either: Auto-add columns OR require pre-existing schema
- Complex transaction handling (multi-statement)

**Recommendation:** v2 feature - requires significant schema design decisions

---

### 2. Incremental/Delta Detection
**What:** Only process rows that have actually changed.

**Expected Behavior:**
- Compare incoming data against existing data
- Skip rows that are identical to current state
- Reduce unnecessary writes and trigger executions
- Useful for large datasets with few actual changes

**Complexity:** Medium-High

**Implementation Options:**
1. **Hash comparison:** Store hash of row data, compare hashes
2. **Timestamp comparison:** Source provides `last_modified` timestamp
3. **Full comparison:** Compare all columns (expensive)

---

### 3. Pre/Post Execution Hooks
**What:** Allow custom SQL to run before or after main operation.

**Expected Behavior:**
- Pre-execution: Create temp tables, set session variables, validate data
- Post-execution: Update metadata tables, send notifications, run cleanup
- Custom SQL editor in node configuration

**Complexity:** Medium

**Use Cases:**
- Data validation before insert
- Foreign key resolution
- Custom audit logging
- Integration with external systems

---

### 4. Parallel Batch Execution
**What:** Execute multiple batches concurrently for faster processing.

**Expected Behavior:**
- Configurable parallelism (e.g., 4 concurrent batch workers)
- Connection pooling
- Ordering guarantees when needed
- Backpressure handling

**Complexity:** High

**Dependencies:**
- Asyncio or threading implementation
- Connection pool management
- Race condition handling

---

### 5. Conflict Handling Strategies (Upsert Variants)
**What:** Multiple strategies for handling conflicts beyond simple update.

**Expected Strategies:**
1. **Update:** Update existing row (current behavior)
2. **Skip:** Do nothing on conflict (keep existing data)
3. **Merge:** Update only specified columns, keep others
4. **Error:** Fail the operation on any conflict
5. **Custom:** User-defined merge logic

**Complexity:** Medium

---

## Anti-Features (Explicitly NOT Building)

Features to explicitly NOT build (and why).

### 1. Automatic Schema Creation
**Why Avoid:** Creating tables automatically based on incoming data leads to:
- Type inference errors (strings vs numbers vs dates)
- Missing constraints (primary keys, foreign keys, NOT NULL)
- Index management issues
- Version control problems

**What to Do Instead:**
- Require pre-existing tables
- Provide schema validation and helpful error messages
- Consider a separate "Schema Migration" node type for v2

---

### 2. Multi-Table Transactions
**Why Avoid:** Coordinating transactions across multiple tables in a single node adds significant complexity:
- Deadlock risks
- Long-running transaction issues
- Rollback complexity

**What to Do Instead:**
- One node = one table operation
- Use flow orchestration for multi-table operations
- Each node commits independently

---

### 3. Real-time Streaming
**Why Avoid:** Streaming semantics (continuous insertion) are fundamentally different from batch ETL:
- Different infrastructure requirements
- Different error handling needs
- Different user expectations

**What to Do Instead:**
- Keep focus on batch ETL workflows
- Consider a separate "Streaming Integration" product for v2

---

## Feature Dependencies

```
Core Infrastructure (already built)
    │
    ├── Flow Execution Engine (Deno runner)
    ├── Python Orchestrator
    ├── Connection Management
    ├── Execution History/Logging
    └── Batch Size Configuration
    │
    v
ODS Execution Engine
    │
    ├── Append Mode ←────────┐
    ├── Overwrite Mode ←─────┼── Table Stakes (v1)
    ├── Upsert Mode ←────────┤
    │   └── Requires: Identity fields, unique constraint
    └── Batch Processing ←───┘
    │
    └── Merge/SCD2 Mode ←──── Differentiator (v2)
        └── Requires: SCD2 schema design, versioning columns
```

---

## Write Mode Behavior Matrix

| Aspect | Append | Overwrite | Upsert | Merge (SCD2) |
|--------|--------|-----------|--------|--------------|
| **SQL Pattern** | `INSERT` | `TRUNCATE` + `INSERT` | `INSERT ON CONFLICT` | Multi-statement |
| **Identity Fields** | Not used | Not used | Required | Required |
| **Unique Constraint** | Not required | Not required | **Required** | Recommended |
| **History Preserved** | Yes (all rows) | No | No | Yes (versions) |
| **Row Count Output** | Inserted | Deleted + Inserted | Inserted + Updated | Inserted + Updated |
| **Complexity** | Low | Low | Medium | High |
| **Use Case** | Logs, events | Full refresh | Sync, replicate | Audit, history |

---

## Implementation Recommendations

### v1 Implementation (Current Milestone)

**Priority 1: Core Modes**
1. **Append** - Straightforward, essential
2. **Overwrite** - Straightforward, essential (use TRUNCATE)
3. **Upsert** - Critical for real-world use (INSERT ON CONFLICT)

**Priority 2: Operational Excellence**
- Clear error messages when unique constraint missing for Upsert
- Row count reporting for all modes
- Batch progress tracking
- Transaction safety (rollback on error)

### v2 Considerations

**Later Additions:**
1. **Merge (SCD2)** - Requires schema design decisions
2. **Conflict handling variants** (skip vs update vs error)
3. **Pre/post hooks** - Custom SQL execution
4. **Incremental/delta detection** - Reduce unnecessary writes

---

## Sources

| Source | Confidence | Relevance |
|--------|------------|-----------|
| PostgreSQL INSERT ON CONFLICT Documentation | HIGH | Core upsert mechanism |
| PostgreSQL MERGE Documentation (v15+) | HIGH | SCD2 implementation pattern |
| SQLAlchemy PostgreSQL Dialect Docs | HIGH | Python integration patterns |
| Python sqlite3 executemany docs | MEDIUM | Batch processing patterns |
| Industry ETL best practices | MEDIUM | Feature prioritization |

---

## Open Questions for Phase 31 Planning

1. **Upsert constraint validation:** Should we verify unique constraint exists before execution, or let PostgreSQL error?
2. **Overwrite safety:** Should TRUNCATE require explicit confirmation or be the default?
3. **Error handling:** Should partial batch failures rollback the entire operation or just the failed batch?
4. **RETURNING clause:** Should we use RETURNING to get accurate row counts, or rely on cursor.rowcount?
5. **Transaction boundaries:** One transaction per batch or one per entire operation?

---

**Confidence Assessment:**
- Stack recommendations: HIGH (PostgreSQL native features)
- Feature completeness: HIGH (standard ETL patterns)
- Architecture patterns: HIGH (well-established)
- Pitfalls: MEDIUM (some edge cases need testing)
