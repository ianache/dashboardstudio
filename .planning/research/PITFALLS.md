# ODS Execution Engine Pitfalls

**Domain:** PostgreSQL ODS Operations with Deno-Python Integration  
**Project:** Dashboard Studio v1.6 ODS Execution Engine  
**Researched:** 2026-05-16  
**Confidence:** HIGH (based on official PostgreSQL 18, Python 3.14, and Deno 2.x documentation)

---

## Executive Summary

The ODS Execution Engine must handle bulk data operations (Append, Overwrite, Upsert, SCD2 Merge) across a Deno-to-Python boundary. This boundary introduces serialization, process management, and timeout risks that compound with PostgreSQL's inherent concurrency complexities. **The most dangerous pitfall is underestimating transaction scope across the Deno-Python boundary**, where a Python executor failure mid-batch can leave PostgreSQL in an inconsistent state with no automated cleanup mechanism.

---

## Critical Pitfalls

### Pitfall 1: Deadlocks in Concurrent Upsert Operations

**What goes wrong:**
When multiple flows execute concurrent UPSERT operations on the same table with composite keys, PostgreSQL can enter a deadlock condition where two transactions each hold locks the other needs.

**Why it happens:**
- Rows are updated in different orders across concurrent transactions
- `ON CONFLICT DO UPDATE` acquires row-level locks that can conflict
- Per PostgreSQL documentation: "deadlocks can occur as the result of row-level locks (and thus, they can occur even if explicit locking is not used)"

**Consequences:**
- PostgreSQL automatically aborts one transaction (unpredictable which one)
- Flow execution fails with `deadlock detected` error
- Partial batch writes leave data in inconsistent state
- Client must retry entire batch

**Prevention:**
1. **Always order operations consistently**: Sort input data by conflict keys before upsert
2. **Use advisory locks** for serialized access to critical sections:
   ```sql
   SELECT pg_advisory_xact_lock(hashtext('ods_table_name'));
   ```
3. **Implement retry logic** with exponential backoff for deadlock errors (SQLSTATE '40P01')
4. **Limit batch sizes** to reduce lock contention surface area

**Phase to address:** Phase 1 (Core Executor) - Implement retry logic and consistent ordering  
**Severity:** HIGH - Will occur in production with concurrent flows

---

### Pitfall 2: Transaction Scope Violations Across Deno-Python Boundary

**What goes wrong:**
A batch operation spans multiple Python subprocess calls, but a failure in the middle leaves PostgreSQL with partial data committed or an orphaned transaction.

**Why it happens:**
- Each Deno `EXEC_ODS` signal spawns a new Python process
- Python process crash = lost transaction control
- No distributed transaction coordinator exists between Deno and Python
- Long-running transactions accumulate locks and WAL

**Consequences:**
- Data inconsistency: some batches committed, others lost
- PostgreSQL locks held indefinitely until `idle_in_transaction_session_timeout` kicks in
- WAL bloat from uncommitted transactions
- Subsequent flows may see partial data

**Prevention:**
1. **Never span transactions across subprocess calls** - each Python execution must be self-contained
2. **Use explicit transaction blocks** with proper error handling:
   ```python
   try:
       conn.execute("BEGIN")
       # ... all operations ...
       conn.execute("COMMIT")
   except Exception:
       conn.execute("ROLLBACK")
       raise
   ```
3. **Set aggressive timeouts**:
   ```sql
   SET idle_in_transaction_session_timeout = '30s';
   SET statement_timeout = '5min';
   ```
4. **Implement idempotency** - same batch can be safely retried

**Phase to address:** Phase 1 (Core Executor) - Transaction wrapper design  
**Severity:** CRITICAL - Can corrupt ODS data

---

### Pitfall 3: JSON Serialization Failures in Deno-Python Data Handoff

**What goes wrong:**
Data from Deno to Python fails to serialize/deserialize correctly, losing precision for special values or causing parse failures.

**Why it happens:**
- Python `json` module converts `NaN`, `Infinity`, `-Infinity` to JavaScript equivalents by default
- PostgreSQL `NaN` values become JSON `NaN` which is non-standard
- Date/time objects have no native JSON representation
- Large integers (> 2^53) lose precision in JavaScript
- Per Python docs: "malicious JSON string may cause the decoder to consume considerable CPU and memory"

**Consequences:**
- `JSONDecodeError` on Python side
- Silent data corruption for floating-point values
- Timestamp precision loss
- Flow execution halts

**Prevention:**
1. **Strict JSON validation** - use `allow_nan=False` in Python:
   ```python
   json.loads(data, parse_constant=lambda x: raise ValueError(f"Invalid: {x}"))
   ```
2. **Date serialization standard** - use ISO 8601 strings exclusively:
   ```typescript
   // Deno side
   date.toISOString()  // "2024-01-15T10:30:00.000Z"
   ```
3. **BigInt handling** - serialize as strings:
   ```typescript
   bigIntValue.toString()  // "9007199254740993"
   ```
4. **Null handling** - distinguish between SQL NULL and JSON null
5. **Size limits** - enforce maximum payload size before parsing

**Phase to address:** Phase 1 (Core Executor) - Data protocol design  
**Severity:** HIGH - Silent data corruption risk

---

### Pitfall 4: Memory Exhaustion with Large Batch Sizes

**What goes wrong:**
Loading millions of rows into memory for batch processing causes OOM (Out of Memory) errors on either Deno or Python side.

**Why it happens:**
- `Popen.communicate()` buffers all data in memory per Python docs: "data read is buffered in memory, so do not use this method if the data size is large or unlimited"
- PostgreSQL `COPY` from stdin requires streaming, not buffering
- Deno subprocess output buffering has limits
- Python JSON deserialization creates full object tree

**Consequences:**
- Process killed by OOM killer
- Flow execution fails mid-stream
- Partial data leaves ODS in inconsistent state
- System instability affecting other flows

**Prevention:**
1. **Streaming architecture** - use chunked processing:
   ```python
   # Process in configurable batches (default 1000 rows)
   for chunk in pd.read_csv(file, chunksize=batch_size):
       execute_batch(chunk)
   ```
2. **Memory-mapped files** for large data transfers between Deno and Python
3. **Backpressure handling** - pause Deno output if Python can't keep up
4. **Configurable batch size** with conservative defaults (1,000 - 10,000 rows)
5. **Monitor memory usage** and abort before OOM

**Phase to address:** Phase 1 (Core Executor) - Streaming implementation  
**Severity:** HIGH - Production stability issue

---

### Pitfall 5: SCD2 Implementation Errors

**What goes wrong:**
Slowly Changing Dimension Type 2 implementation creates overlapping date ranges, orphaned records, or incorrect current flags.

**Why it happens:**
- Race conditions between expire-old and insert-new operations
- Incorrect date boundary handling (inclusive vs exclusive)
- Multiple concurrent flows updating same dimension
- Missing proper transaction isolation

**Consequences:**
- Query results return multiple "current" records for same entity
- Historical reporting shows data from wrong time period
- Data warehouse integrity compromised
- Complex manual repair required

**Prevention:**
1. **Atomic SCD2 operation** - do expire and insert in single transaction:
   ```sql
   BEGIN;
   -- Expire existing record
   UPDATE dim_table 
   SET valid_to = CURRENT_TIMESTAMP, is_current = false
   WHERE business_key = %s AND is_current = true;
   
   -- Insert new record
   INSERT INTO dim_table (business_key, attributes, valid_from, valid_to, is_current)
   VALUES (%s, %s, CURRENT_TIMESTAMP, '9999-12-31', true);
   COMMIT;
   ```
2. **Use exclusion constraints** to prevent overlaps:
   ```sql
   ALTER TABLE dim_table 
   ADD CONSTRAINT no_overlapping_ranges 
   EXCLUDE USING gist (business_key WITH =, valid_during WITH &&);
   ```
3. **Advisory locks** per business key for serialized updates
4. **Validate after each batch** - query for overlaps and abort if found

**Phase to address:** Phase 2 (SCD2 Merge Mode) - SCD2-specific implementation  
**Severity:** HIGH - Data integrity risk

---

### Pitfall 6: ON CONFLICT Inference Failures

**What goes wrong:**
`INSERT ... ON CONFLICT` fails with "there is no unique or exclusion constraint matching the ON CONFLICT specification" even when indexes exist.

**Why it happens:**
- Index inference requires exact column match in order
- Partial indexes require matching WHERE clause in ON CONFLICT
- Expression indexes need explicit expression specification
- Concurrent index creation can cause transient failures per PostgreSQL docs: "While CREATE INDEX CONCURRENTLY or REINDEX CONCURRENTLY is running on a unique index, INSERT ... ON CONFLICT statements on the same table may unexpectedly fail"

**Consequences:**
- UPSERT falls back to INSERT and throws unique violation
- Flow execution fails
- No atomic upsert guarantee

**Prevention:**
1. **Explicit constraint naming** over inference:
   ```sql
   INSERT ... ON CONFLICT ON CONSTRAINT unique_constraint_name DO UPDATE
   ```
2. **Validate constraint exists** before execution via metadata query
3. **Avoid concurrent index creation** during flow execution windows
4. **Have fallback** to UPDATE-then-INSERT pattern if inference fails

**Phase to address:** Phase 1 (Core Executor) - Upsert implementation  
**Severity:** MEDIUM - Affects upsert reliability

---

### Pitfall 7: Statement Timeout Cascading Failures

**What goes wrong:**
A long-running batch operation hits `statement_timeout`, but the error handling doesn't properly clean up, causing subsequent operations to fail.

**Why it happens:**
- Default PostgreSQL `statement_timeout` is 0 (unlimited) - dangerous for production
- Batch operations with large data take unpredictable time
- Timeout error may leave transaction in aborted state
- Connection pool returns aborted transaction to pool

**Consequences:**
- All subsequent operations on same connection fail with "current transaction is aborted"
- Flow execution stops
- Partial batch data committed (if using autocommit per statement)

**Prevention:**
1. **Explicit timeout configuration** per operation type:
   ```python
   timeouts = {
       'append': '5min',
       'overwrite': '30min',
       'upsert': '10min',
       'merge': '20min'
   }
   ```
2. **Statement-level timeouts** using `SET LOCAL`:
   ```sql
   SET LOCAL statement_timeout = '5min';
   ```
3. **Proper cleanup on timeout**:
   ```python
   try:
       execute_batch()
   except psycopg2.errors.QueryCanceled:
       conn.rollback()  # Must rollback before reusing connection
       raise BatchTimeoutError()
   ```
4. **Monitor and alert** on timeouts per flow

**Phase to address:** Phase 1 (Core Executor) - Error handling  
**Severity:** MEDIUM - Operational stability

---

### Pitfall 8: Foreign Key Constraint Violations During Bulk Loads

**What goes wrong:**
Bulk UPSERT operations fail foreign key checks or cause trigger queue overflow.

**Why it happens:**
- Referenced table doesn't have matching keys for all incoming data
- Per PostgreSQL docs: "Loading many millions of rows can cause the trigger event queue to overflow available memory, leading to intolerable swapping or even outright failure of the command"
- FK checks run per-row during INSERT, not deferred to batch end
- Cascading updates trigger additional checks

**Consequences:**
- Batch operation fails mid-stream
- Complex partial rollback required
- Memory pressure on database server

**Prevention:**
1. **Pre-validate foreign keys** in Python before database operation:
   ```python
   missing_refs = input_data[~input_data['fk_column'].isin(reference_table['id'])]
   if not missing_refs.empty:
       raise ForeignKeyViolationError(f"Missing references: {missing_refs['fk_column'].tolist()}")
   ```
2. **Deferrable constraints** where possible:
   ```sql
   ALTER TABLE child_table 
   ALTER CONSTRAINT fk_name DEFERRABLE INITIALLY DEFERRED;
   ```
3. **Disable triggers temporarily** for known-good data (with caution):
   ```sql
   ALTER TABLE target_table DISABLE TRIGGER ALL;
   -- ... batch operation ...
   ALTER TABLE target_table ENABLE TRIGGER ALL;
   ```
4. **Process in smaller batches** to avoid trigger queue overflow

**Phase to address:** Phase 2 (Advanced Features) - Constraint handling  
**Severity:** MEDIUM - Affects data with FK relationships

---

### Pitfall 9: Index Maintenance Overhead During Large Upserts

**What goes wrong:**
UPSERT operations on indexed tables become progressively slower as table grows due to index maintenance overhead.

**Why it happens:**
- Each INSERT/UPDATE maintains all indexes (B-tree rebalancing)
- PostgreSQL updates index tuples for HOT (Heap-Only Tuple) updates but not for index key changes
- Per PostgreSQL docs: "Creating an index on pre-existing data is quicker than updating it incrementally as each row is loaded"

**Consequences:**
- Operation time increases non-linearly with table size
- Lock contention increases
- WAL generation saturates I/O

**Prevention:**
1. **For bulk loads**: Drop indexes, load data, recreate indexes (for overwrite mode)
2. **Partial indexes** for hot data only:
   ```sql
   CREATE INDEX idx_recent ON table (column) WHERE created_at > '2024-01-01';
   ```
3. **Fillfactor tuning** for update-heavy tables:
   ```sql
   ALTER TABLE table SET (fillfactor = 70);  -- Leave 30% for HOT updates
   ```
4. **Parallel index creation** using `CREATE INDEX CONCURRENTLY` (but see Pitfall 6)

**Phase to address:** Phase 3 (Performance Optimization) - Index strategy  
**Severity:** LOW-MEDIUM - Performance degradation over time

---

### Pitfall 10: Subprocess Communication Deadlocks

**What goes wrong:**
Deno process blocks waiting for Python output, Python blocks waiting for Deno input - classic deadlock.

**Why it happens:**
- OS pipe buffers have limited size (typically 64KB)
- If both processes write to pipes without reading, they block
- Per Python docs: "This will deadlock when using stdout=PIPE or stderr=PIPE and the child process generates enough output to a pipe such that it blocks waiting for the OS pipe buffer to accept more data"
- Order of stream operations matters

**Consequences:**
- Both processes hang indefinitely
- Flow execution never completes
- Must kill processes externally

**Prevention:**
1. **Use `communicate()` not direct stream access**:
   ```python
   proc = subprocess.Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
   stdout, stderr = proc.communicate(input=data)  # Atomic write+read
   ```
2. **Timeout all subprocess operations**:
   ```python
   try:
       stdout, stderr = proc.communicate(input=data, timeout=300)
   except TimeoutExpired:
       proc.kill()
       raise
   ```
3. **Stream large data via files** not pipes:
   ```typescript
   // Deno: write to temp file
   await Deno.writeTextFile('/tmp/batch.json', data);
   
   // Python: read from file
   with open('/tmp/batch.json') as f:
       data = json.load(f)
   ```
4. **Async I/O** for non-blocking operations

**Phase to address:** Phase 1 (Core Executor) - Subprocess management  
**Severity:** HIGH - Will deadlock on large outputs

---

## Phase-Specific Warnings

| Phase | Pitfall Risk | Mitigation |
|-------|--------------|------------|
| Phase 1: Core Executor | Deadlocks (P1), Transaction scope (P2), JSON serialization (P3), Memory (P4), Subprocess deadlock (P10) | Implement retry logic, transaction wrapper, streaming, proper subprocess handling |
| Phase 2: SCD2 Merge | SCD2 errors (P5), FK violations (P8) | Atomic operations, exclusion constraints, pre-validation |
| Phase 3: Performance | Index overhead (P9), Timeout handling (P7) | Index strategy, timeout configuration, fillfactor tuning |

---

## Detection Strategies

| Pitfall | Detection Method |
|---------|------------------|
| Deadlocks | Monitor PostgreSQL logs for `deadlock detected`, track SQLSTATE 40P01 errors |
| Transaction scope | Query `pg_stat_activity` for long-running transactions, set `idle_in_transaction_session_timeout` |
| JSON failures | Schema validation on Python side, strict JSON parsing |
| Memory exhaustion | Process memory monitoring, batch size metrics |
| SCD2 errors | Post-batch validation queries for overlaps, multiple current flags |
| ON CONFLICT failures | Error rate monitoring, constraint validation pre-execution |
| Timeouts | Query duration histograms, timeout error tracking |
| FK violations | Referential integrity checks, missing reference detection |
| Index overhead | Query performance degradation over time, index bloat monitoring |
| Subprocess deadlocks | Process liveness checks, subprocess timeout enforcement |

---

## Testing Recommendations

1. **Concurrency testing**: Run 10+ parallel flows hitting same table with UPSERT
2. **Large data testing**: Test with 1M+ row datasets
3. **Failure injection**: Kill Python subprocess mid-batch, verify cleanup
4. **Data validation**: Verify no precision loss for floats, dates, large integers
5. **Timeout testing**: Verify graceful handling of statement_timeout
6. **Memory testing**: Monitor heap usage during large batch operations

---

## Sources

- PostgreSQL 18.4 Documentation: Populating a Database (https://www.postgresql.org/docs/current/populate.html)
- PostgreSQL 18.4 Documentation: INSERT ... ON CONFLICT (https://www.postgresql.org/docs/current/sql-insert.html)
- PostgreSQL 18.4 Documentation: Transaction Isolation (https://www.postgresql.org/docs/current/transaction-iso.html)
- PostgreSQL 18.4 Documentation: Explicit Locking (https://www.postgresql.org/docs/current/explicit-locking.html)
- Python 3.14.5 Documentation: subprocess module (https://docs.python.org/3/library/subprocess.html)
- Python 3.14.5 Documentation: json module (https://docs.python.org/3/library/json.html)
- Deno Runtime Documentation: Node Compatibility (https://docs.deno.com/runtime/fundamentals/node/)

**Confidence Level:** HIGH - All findings verified against official documentation from PostgreSQL, Python, and Deno projects.
