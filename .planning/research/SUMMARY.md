# Research Summary: ODS Execution Engine

**Project:** Dashboard Studio v1.6  
**Milestone:** ODS Execution Engine (Phase 31)  
**Research Date:** 2026-05-16  
**Confidence:** HIGH

---

## Key Findings

### 1. Stack Requirements: Minimal Additions Needed

**Existing stack is sufficient:**
- `asyncpg` (v0.29.0 → upgrade to 0.30.0) for PostgreSQL bulk operations
- `pandas` (^2.2.0) only required for SCD2 merge operations
- No new major dependencies required

**Integration Pattern:** Deno subprocess → EXEC_ODS signal → Python ODSExecutor → PostgreSQL

### 2. Feature Complexity Progression

| Mode | Complexity | Implementation | Priority |
|------|-----------|----------------|----------|
| **Append** | Low | Simple `INSERT` | v1 (Table stakes) |
| **Overwrite** | Low | `TRUNCATE` + `INSERT` | v1 (Table stakes) |
| **Upsert** | Medium | `INSERT ON CONFLICT` | v1 (Table stakes) |
| **Merge (SCD2)** | High | Multi-statement versioning | v2 (Differentiator) |

### 3. Critical Architecture Decisions

**EXEC_ODS Signal Protocol:**
```
EXEC_ODS:{node_id}:{operation}:{connection_id}:{batch_id}
EXEC_ODS_PAYLOAD:{json_payload}
```

**Transaction Strategy:** Per-batch transactions (each batch atomic, failures isolated)

**Error Handling:** Classified errors with retry logic (connection, timeout) vs skip (unique violation, FK)

### 4. Top 5 Pitfalls to Address

1. **Deadlocks in concurrent upserts** → Consistent key ordering + retry logic
2. **Transaction scope violations** → Self-contained Python executions, no cross-subprocess transactions
3. **JSON serialization failures** → Strict validation, ISO 8601 dates, BigInt as strings
4. **Memory exhaustion** → Streaming/chunked processing, configurable batch sizes (default 1000)
5. **SCD2 overlapping ranges** → Atomic expire+insert, exclusion constraints

---

## Implementation Recommendations

### Phase Ordering

**Phase 1: Core Executor** (Days 1-3)
- Create `ods_executor.py` with Append, Overwrite, Upsert
- Implement batch processing with asyncpg
- Add transaction wrapper and error handling

**Phase 2: Deno Integration** (Days 4-5)
- Extend Deno runner with EXEC_ODS signal
- Modify `deno_service.py` to capture and delegate
- End-to-end integration testing

**Phase 3: Production Hardening** (Days 6-8)
- Comprehensive error classification
- Retry logic with backoff
- Performance optimization (connection pooling)
- Deprecate legacy destination_executor.py

**Phase 4: SCD2 Merge** (Future / v2)
- Complex versioning logic
- Exclusion constraints
- Historical tracking

### Performance Expectations

| Operation | Throughput | Notes |
|-----------|-----------|-------|
| Append | 50K-100K rows/sec | Fastest, no conflict checking |
| Overwrite | 40K-80K rows/sec | TRUNCATE is fast |
| Upsert | 20K-40K rows/sec | Index lookup overhead |
| SCD2 | 5K-15K rows/sec | Complex multi-step |

**Recommended batch size:** 1,000 rows (balance of memory/speed)

### Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Memory exhaustion (large datasets) | Medium-High | Streaming, configurable batches |
| Deadlocks (concurrent upserts) | Medium | Consistent ordering, retry logic |
| JSON serialization errors | Medium | Strict validation, standard formats |
| Transaction scope violations | Medium | Self-contained execution model |
| SCD2 complexity | Medium | Defer to v2, implement core first |

---

## Files Generated

| File | Purpose |
|------|---------|
| `.planning/research/STACK.md` | Technology stack recommendations |
| `.planning/research/FEATURES.md` | Feature landscape (table stakes vs differentiators) |
| `.planning/research/ARCHITECTURE.md` | Integration architecture and data flow |
| `.planning/research/PITFALLS.md` | Critical pitfalls with prevention strategies |

---

## Dependencies to Add

```bash
uv add "asyncpg>=0.30.0"    # Upgrade
uv add "pandas>=2.2.0"      # For SCD2 (Phase 4)
```

---

## Open Questions for Requirements Phase

1. Should unique constraints be validated before Upsert execution?
2. TRUNCATE or DELETE for Overwrite mode default?
3. Error handling: rollback entire operation or just failed batch?
4. Batch size limits and memory thresholds?
5. SCD2 table schema: auto-add columns or require pre-existing?

---

**Next Step:** Define requirements based on this research → Create ROADMAP.md
