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

# Requirements: Email Node with Dynamic Templates (Milestone v1.7)

**Defined:** 2026-05-17
**Core Value:** User can send emails from integration flows with dynamic content generated from templates and input data

## v1 Requirements

### Core Functionality (EMAIL)

- [ ] **EMAIL-01**: Email node can send emails using SMTP connections from DataSource
- [ ] **EMAIL-02**: User can configure recipient(s), CC, BCC email addresses
- [ ] **EMAIL-03**: Subject field supports template syntax with {{expression}} markers
- [ ] **EMAIL-04**: Body field supports template syntax with {{expression}} markers
- [ ] **EMAIL-05**: Body can be either plain text or HTML format
- [ ] **EMAIL-06**: Template engine supports nested object access ({{user.profile.name}})
- [ ] **EMAIL-07**: Template engine supports iteration with {% for %} for table/list generation
- [ ] **EMAIL-08**: Template engine supports conditionals with {% if %}/{% else %}
- [ ] **EMAIL-09**: Variables are auto-escaped by default for XSS prevention
- [x] **EMAIL-10**: Input data from upstream nodes is available as template context

### Integration (EMAIL)

- [x] **EMAIL-11**: Deno runner emits EXEC_EMAIL signal when encountering email node
- [x] **EMAIL-12**: EXEC_EMAIL payload includes connection_id, recipients, subject_template, body_template
- [x] **EMAIL-13**: Python EmailExecutor renders templates and sends via SMTP
- [x] **EMAIL-14**: Execution results flow back through WebSocket to UI
- [ ] **EMAIL-15**: Email addresses are validated before sending

### Security & Validation (EMAIL)

- [ ] **EMAIL-16**: Templates use SandboxedEnvironment to prevent code injection
- [ ] **EMAIL-17**: HTML body is sanitized with nh3 to remove dangerous tags
- [ ] **EMAIL-18**: SMTP credentials are resolved from encrypted DataSource
- [ ] **EMAIL-19**: Invalid template syntax produces clear error messages
- [ ] **EMAIL-20**: Missing template variables can be configured to fail or render empty

### UI/UX (EMAIL)

- [ ] **EMAIL-21**: Node properties panel includes connection selector (SMTP DataSource)
- [ ] **EMAIL-22**: Subject field is a text input with template support
- [ ] **EMAIL-23**: Body field supports both text and HTML modes
- [ ] **EMAIL-24**: Recipients, CC, BCC fields support comma-separated email lists

## v2 Requirements (Deferred)

### Enhanced Templating

- **EMAIL-25**: Built-in filters for date/number formatting
- **EMAIL-26**: Custom helper functions for common operations
- **EMAIL-27**: Template preview mode in UI
- **EMAIL-28**: MJML integration for responsive email templates

### Advanced Features

- **EMAIL-29**: Attachment support with template-based filenames
- **EMAIL-30**: Inline image embedding
- **EMAIL-31**: Email queuing for high-volume sends
- **EMAIL-32**: Delivery tracking and bounce handling

## Out of Scope

| Feature | Reason |
|---------|--------|
| Custom SMTP library | Python smtplib is sufficient, DataSource handles connection mgmt |
| Rich text editor (Quill, etc.) | Plain textarea with HTML syntax highlighting sufficient for v1 |
| Email scheduling | Already covered by Background Scheduler milestone (cron) |
| Email threading/conversations | Complex state management, not core to integration flows |
| Advanced template inheritance | Adds complexity, loops/conditionals sufficient for v1 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EMAIL-01 | Phase 32 | Pending |
| EMAIL-02 | Phase 32 | Pending |
| EMAIL-03 | Phase 32 | Pending |
| EMAIL-04 | Phase 32 | Pending |
| EMAIL-05 | Phase 32 | Pending |
| EMAIL-06 | Phase 32 | Pending |
| EMAIL-07 | Phase 32 | Pending |
| EMAIL-08 | Phase 32 | Pending |
| EMAIL-09 | Phase 32 | Pending |
| EMAIL-10 | Phase 32 | Complete |
| EMAIL-11 | Phase 32 | Complete |
| EMAIL-12 | Phase 32 | Complete |
| EMAIL-13 | Phase 32 | Complete |
| EMAIL-14 | Phase 32 | Complete |
| EMAIL-15 | Phase 32 | Pending |
| EMAIL-16 | Phase 32 | Pending |
| EMAIL-17 | Phase 32 | Pending |
| EMAIL-18 | Phase 32 | Pending |
| EMAIL-19 | Phase 32 | Pending |
| EMAIL-20 | Phase 32 | Pending |
| EMAIL-21 | Phase 32 | Pending |
| EMAIL-22 | Phase 32 | Pending |
| EMAIL-23 | Phase 32 | Pending |
| EMAIL-24 | Phase 32 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to Phase 32: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-17*
*Last updated: 2026-05-17 after research synthesis*
