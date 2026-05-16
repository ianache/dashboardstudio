# Requirements: ODS PostgreSQL Upsert & Dynamic Discovery

## Overview
Este hito se enfoca en mejorar el nodo "ODS PostgreSQL" para permitir a los usuarios finales descubrir tablas y columnas de forma dinámica desde el editor, y configurar operaciones de escritura avanzadas como el UPSERT con múltiples campos de identidad.

## Functional Requirements (FR)
- [ ] **FR-01: Descubrimiento de Tablas:** El panel de propiedades del nodo ODS PostgreSQL debe permitir seleccionar una tabla desde un dropdown/combobox cuyos valores se obtengan en tiempo real de la base de datos conectada.
- [ ] **FR-02: Botón de Refresh:** Incluir un botón al costado del selector de tabla para forzar la actualización del listado desde el backend.
- [ ] **FR-03: Selección de Campos de Identidad:** Cuando el modo de escritura sea "UPSERT", se debe habilitar un campo de selección múltiple para elegir las columnas que conforman la llave primaria o de identidad.
- [ ] **FR-04: Descubrimiento de Columnas:** El selector de campos de identidad debe poblarse automáticamente con las columnas de la tabla seleccionada en FR-01.
- [ ] **FR-05: Soporte para Upsert Compuesto:** El motor de ejecución debe ser capaz de generar sentencias SQL `ON CONFLICT (...) DO UPDATE` considerando uno o múltiples campos de identidad.
- [ ] **FR-06: Operaciones ODS robustas:** Implementar en Python (Backend) el procesamiento de los modos "Append", "Overwrite" y "Upsert" para garantizar el manejo correcto de transacciones y tipos de datos.

## Technical Requirements (TR)
- [x] **TR-01: API de Inspección:** Crear endpoints en FastAPI para:
    - Listar tablas para una conexión y esquema específico.
    - Listar columnas para una tabla específica.
- [ ] **TR-02: Componente DynamicSelect:** Extender `FlowEditorCanvas.vue` para soportar un tipo de propiedad que sepa cómo pedir datos al backend para llenar sus opciones.
- [ ] **TR-03: Lógica de Visibilidad Condicional:** Implementar en el editor la capacidad de mostrar/ocultar propiedades basándose en el valor de otra (ej: `identity_fields` depende de `write_mode == 'upsert'`).
- [ ] **TR-04: Delegación Deno -> Python:** El runner de Deno debe emitir una instrucción especial al encontrar un nodo de tipo `ods_pg`, permitiendo que el backend de Python tome el control para realizar la escritura en BD.

## User Interface (UI)
- **Combobox de Tabla:** Un selector con capacidad de búsqueda y edición manual.
- **Botón Refresh:** Icono `refresh` de Material Symbols al lado del selector.
- **Multi-select de Identidad:** Lista de checkboxes o chips con los nombres de las columnas detectadas.
- **Jerarquía Visual:** Agrupación clara de campos de configuración de tabla y campos de modo de escritura.
