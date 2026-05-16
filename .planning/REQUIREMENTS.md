# Requirements: Graphical Visualization in Execution History

## Overview
Se requiere extender la funcionalidad de visualización de flujos para que sea accesible desde cualquier entrada del historial de ejecuciones, permitiendo ver el estado gráfico de nodos y conexiones para ejecuciones pasadas.

## Functional Requirements (FR)
- [x] **FR-01: Icono de Lupa en Historial:** Cada fila de la tabla de historial en `ExecutionHistoryModal.vue` debe tener un icono de lupa (`search`).
- [x] **FR-02: Visualización Gráfica Modal:** Al hacer clic en la lupa, se debe abrir el modal `FlowExecutionPopup.vue` cargando los datos específicos de esa ejecución (`execution_id`).
- [x] **FR-03: Icono de Detalles:** El botón actual "Ver" debe ser reemplazado por un icono de "detalles" (ej: `description` o `assignment`).
- [x] **FR-04: Persistencia de Contexto:** El modal de visualización debe recibir correctamente tanto el `execution_id` como el `flow_id` y `flowName` para asegurar que el diagrama y los logs coincidan.

## Technical Requirements (TR)
- [x] **TR-01: Reutilización de `FlowExecutionPopup`:** Utilizar el componente existente sin crear duplicados.
- [x] **TR-02: Manejo de Eventos:** Asegurar que el modal de historial (`ExecutionHistoryModal`) pueda emitir o manejar la apertura del popup de visualización.
- [x] **TR-03: Estilado de Acciones:** Agrupar los iconos en la columna "Acciones" con espaciado consistente y feedback visual al hacer hover.

## User Interface (UI)
- [x] Icono Lupa: `search` (Material Symbols).
- [x] Icono Detalles: `description` (Material Symbols).
- [x] Botones de acción: Estilo `btn-icon` o similar para consistencia con el resto de la aplicación.
