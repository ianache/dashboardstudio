# Requirements: ODS PostgreSQL Upsert & Dynamic Discovery

## Overview
Este hito se enfoca en mejorar el nodo "ODS PostgreSQL" para permitir a los usuarios finales descubrir tablas y columnas de forma dinámica desde el editor, y configurar operaciones de escritura avanzadas como el UPSERT con múltiples campos de identidad.

## Functional Requirements (FR)
- [x] **FR-01: Descubrimiento de Tablas:** El panel de propiedades del nodo ODS PostgreSQL debe permitir seleccionar una tabla desde un dropdown/combobox cuyos valores se obtengan en tiempo real de la base de datos conectada.
- [x] **FR-02: Botón de Refresh:** Incluir un botón al costado del selector de tabla para forzar la actualización del listado desde el backend.
- [x] **FR-03: Selección de Campos de Identidad:** Cuando el modo de escritura sea "UPSERT", se debe habilitar un campo de selección múltiple para elegir las columnas que conforman la llave primaria o de identidad.
- [x] **FR-04: Descubrimiento de Columnas:** El selector de campos de identidad debe poblarse automáticamente con las columnas de la tabla seleccionada en FR-01.
- [ ] **FR-05: Soporte para Upsert Compuesto:** El motor de ejecución debe ser capaz de generar sentencias SQL `ON CONFLICT (...) DO UPDATE` considerando uno o múltiples campos de identidad.
- [ ] **FR-06: Operaciones ODS robustas:** Implementar en Python (Backend) el procesamiento de los modos "Append", "Overwrite" y "Upsert" para garantizar el manejo correcto de transacciones y tipos de datos.

## Technical Requirements (TR)
- [x] **TR-01: API de Inspección:** Crear endpoints en FastAPI para:
    - Listar tablas para una conexión y esquema específico.
    - Listar columnas para una tabla específica.
- [x] **TR-02: Componente DynamicSelect:** Extender `FlowEditorCanvas.vue` para soportar un tipo de propiedad que sepa cómo pedir datos al backend para llenar sus opciones.
- [x] **TR-03: Lógica de Visibilidad Condicional:** Implementar en el editor la capacidad de mostrar/ocultar propiedades basándose en el valor de otra (ej: `identity_fields` depende de `write_mode == 'upsert'`).
- [ ] **TR-04: Delegación Deno -> Python:** El runner de Deno debe emitir una instrucción especial al encontrar un nodo de tipo `ods_pg`, permitiendo que el backend de Python tome el control para realizar la escritura en BD.

## User Interface (UI)
- **Combobox de Tabla:** Un selector con capacidad de búsqueda y edición manual.
- **Botón Refresh:** Icono `refresh` de Material Symbols al lado del selector.
- **Multi-select de Identidad:** Lista de checkboxes o chips con los nombres de las columnas detectadas.
- **Jerarquía Visual:** Agrupación clara de campos de configuración de tabla y campos de modo de escritura.

---

# Requirements: ODS Execution Engine (Milestone v1.6)

**Defined:** 2026-05-17
**Core Value:** User can execute integration flows that write data to PostgreSQL ODS with various strategies (append, overwrite, upsert, merge)

## v1 Requirements

### Core Operations (EXEC)

- [x] **EXEC-01**: Executor can perform Append operations (INSERT without conflict checking)
- [x] **EXEC-02**: Executor can perform Overwrite operations (TRUNCATE + INSERT)
- [x] **EXEC-03**: Executor can perform Upsert operations (INSERT ON CONFLICT DO UPDATE)
- [x] **EXEC-04**: Upsert supports single and composite identity fields
- [x] **EXEC-05**: All operations support configurable batch sizes (default: 1000 rows)

### Deno Integration (EXEC)

- [ ] **EXEC-06**: Deno runner emits EXEC_ODS signal when encountering ods_pg node
- [ ] **EXEC-07**: EXEC_ODS payload includes node_id, operation, connection_config, data, identity_fields
- [ ] **EXEC-08**: Python DenoService intercepts EXEC_ODS signals and delegates to ODSExecutor
- [ ] **EXEC-09**: Execution results flow back through WebSocket to UI

### Data & Connection Management (EXEC)

- [x] **EXEC-10**: ODSExecutor resolves connection credentials from DataSource manager
- [x] **EXEC-11**: Connection pooling via asyncpg for concurrent operations
- [x] **EXEC-12**: Batch processing with per-batch transaction isolation
- [x] **EXEC-13**: Automatic retry with exponential backoff for connection/timeout errors

### Error Handling & Logging (EXEC)

- [x] **EXEC-14**: Detailed error classification (Connection, UniqueViolation, FKViolation, TypeMismatch, Timeout)
- [x] **EXEC-15**: Row counts returned for all operations (inserted, updated, affected)
- [x] **EXEC-16**: Execution duration tracking per batch and total
- [ ] **EXEC-17**: Errors logged to NodeExecutionLogs with batch context

### Validation & Safety (EXEC)

- [ ] **EXEC-18**: Schema and table existence validation before execution
- [ ] **EXEC-19**: Upsert validates unique constraint exists on identity fields
- [ ] **EXEC-20**: JSON payload validation with strict parsing (no NaN/Infinity)
- [ ] **EXEC-21**: Configurable statement timeouts per operation type

## v2 Requirements (Deferred)

### Advanced Operations

- **EXEC-22**: Merge (SCD2) operation support with versioning columns
- **EXEC-23**: Incremental/delta detection to skip unchanged rows
- **EXEC-24**: Pre/post execution hooks for custom SQL

### Performance & Scale

- **EXEC-25**: Parallel batch execution for faster processing
- **EXEC-26**: Checkpoint/resume capability for large datasets
- **EXEC-27**: Streaming for datasets exceeding memory limits

### Enhanced Features

- **EXEC-28**: Conflict handling variants (skip, update, merge, error)
- **EXEC-29**: Index optimization strategies (drop/recreate for bulk loads)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic schema creation | Risk of type inference errors, missing constraints, version control issues. Require pre-existing tables with explicit schema. |
| Real-time streaming | Different infrastructure requirements (streaming vs batch ETL). Separate product consideration. |
| Multi-table transactions | Deadlock risks, long-running transaction issues. One node = one table operation. |
| Cross-database operations | Complexity exceeds v1 scope. PostgreSQL ODS only. |
| Data transformation in executor | Keep executor focused on write operations. Transformations happen in upstream nodes. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FR-01 | Phase 29 | ✓ Complete |
| FR-02 | Phase 30 | ✓ Complete |
| FR-03 | Phase 30 | ✓ Complete |
| FR-04 | Phase 29 | ✓ Complete |
| FR-05 | Phase 31 | Pending |
| FR-06 | Phase 31 | Pending |
| TR-01 | Phase 29 | ✓ Complete |
| TR-02 | Phase 30 | ✓ Complete |
| TR-03 | Phase 30 | ✓ Complete |
| TR-04 | Phase 31 | Pending |
| EXEC-01 | Phase 31 | Complete |
| EXEC-02 | Phase 31 | Complete |
| EXEC-03 | Phase 31 | Complete |
| EXEC-04 | Phase 31 | Complete |
| EXEC-05 | Phase 31 | Complete |
| EXEC-06 | Phase 31 | Pending |
| EXEC-07 | Phase 31 | Pending |
| EXEC-08 | Phase 31 | Pending |
| EXEC-09 | Phase 31 | Pending |
| EXEC-10 | Phase 31 | Complete |
| EXEC-11 | Phase 31 | Complete |
| EXEC-12 | Phase 31 | Complete |
| EXEC-13 | Phase 31 | Complete |
| EXEC-14 | Phase 31 | Complete |
| EXEC-15 | Phase 31 | Complete |
| EXEC-16 | Phase 31 | Complete |
| EXEC-17 | Phase 31 | Pending |
| EXEC-18 | Phase 31 | Pending |
| EXEC-19 | Phase 31 | Pending |
| EXEC-20 | Phase 31 | Pending |
| EXEC-21 | Phase 31 | Pending |

**Coverage:**
- v1 requirements: 21 total (EXEC-01 through EXEC-21)
- Mapped to Phase 31: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-17*
*Last updated: 2026-05-17 after research synthesis*
