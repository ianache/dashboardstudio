# Project: Visualizacion Design Improvements

## Context
Este proyecto consiste en una mejora del módulo de visualización del Dashboard Studio. El objetivo es proporcionar una interfaz de arrastrar y soltar (drag-and-drop) moderna e intuitiva para configurar gráficos y paneles a partir de cubos de información.

## Objective
Implementar un configurador de visualizaciones dinámico con:
- Selección de cubos y campos (Métricas/Dimensiones).
- Interfaz de tres paneles (Origen, Configuración, Preview).
- Renderizado en tiempo real con soporte para múltiples tipos de gráficos.
- Persistencia en el esquema del dashboard.

## Technical Stack
- **Frontend:** Vue 3 (Composition API), Vite, Vanilla CSS.
- **Backend:** FastAPI (Python), PostgreSQL (con Cube.js como middleware de datos).
- **Libraries to Research:** Drag-and-drop (dnd-kit, vue-draggable), Charting (ECharts/Chart.js).

## Visual Direction
- **Modern Refinement:** Refinar los patrones existentes para una estética más limpia y profesional (según `@images/diseño_visualizacion.jpeg`).

## Milestone: Integration Flows with JavaScript & Deno
**Objective:** Incorporar a los flujos de integración la capacidad de las herramientas para incorporar código JavaScript y permitir que los flujos se puedan ejecutar como funciones en Deno cuya ejecución sea gestionada desde la propia plataforma dashboardstudio.

### Success Criteria
- [x] Soporte para scripts de JavaScript en los nodos de los flujos de integración.
- [x] Ejecución de flujos completos como funciones de Deno.
- [x] Gestión de la ejecución (logs, estado, control) desde la UI de Dashboard Studio.
- [x] Integración de un editor de código en el Flow Editor.

## Milestone: Flow Execution Visualization
**Objective:** Proporcionar feedback visual en tiempo real en el canvas del Flow Editor durante la ejecución de los flujos de integración.

### Success Criteria
- [x] Visualización de nodo en ejecución (borde verde grueso).
- [x] Visualización de secuencias activadas (conexiones/flechas en verde al finalizar el nodo origen).
- [x] Badges de estado en los nodos (check para éxito, cross para fallo).
- [x] Sincronización precisa entre el motor de ejecución (Deno) y el canvas UI.

## Milestone: Connection Management & Centralized Credentials
**Objective:** Administrar de forma centralizada y reutilizable las conexiones a fuentes externas bajo el submenu "Data Integration".

### Success Criteria
- [x] Gestión de conexiones (Email, DB, FTP, HTTP, JWT) con configuración JSON detallada.
- [x] Centralización de credenciales con encriptación recursiva en el backend.
- [x] Interfaz de administración (Listado, Creación, Edición, Eliminación, Test de conexión).
- [x] Soporte para tipos de conexión: SMTP, SQL, FTP/SFTP, HTTP Basic y JWT Token.
- [x] Integración en el SideMenu bajo el submenu "Data Integration".

## Milestone: Background Scheduler & Detailed Execution History
**Objective:** Automatizar la ejecución de flujos de integración mediante cronjobs y mantener un historial detallado de ejecuciones por flujo y nodo.

### Success Criteria
- [x] Implementación de `APScheduler` para la gestión de cronjobs en background.
- [x] Esquema de base de datos para almacenar `ExecutionHistory` (Flow level) y `NodeExecutionLogs` (Node level).
- [ ] Interfaz de historial de ejecución (tabla paginable) accesible desde un nuevo icono "Log" en la vista de Integraciones.
- [ ] Visualización de detalles (inputs/outputs, estado, duración) por nodo en un panel lateral.
- [ ] Configuración configurable de nivel de detalle de logs (resumen vs detallado).

## Milestone: Resizable Properties Sidebar
**Objective:** Mejorar la usabilidad del editor permitiendo ajustar dinámicamente el ancho del panel de propiedades.

### Success Criteria
- [x] Tirador interactivo en el borde izquierdo de la barra lateral de propiedades.
- [x] Soporte para arrastrar y soltar para cambiar el ancho (min 272px, max 50% de la pantalla).
- [x] Persistencia del ancho durante la edición de diferentes nodos.
- [x] Integración fluida con la función de colapso existente.

## Milestone: Execution Console Improvements
**Objective:** Corregir la visualización de iconos y permitir el ajuste vertical del panel de la consola de ejecución (Terminal).

### Success Criteria
- [x] Visualización correcta de los iconos "delete_sweep" y "close" en la consola (sin textos superpuestos).
- [x] Panel de consola resizable verticalmente mediante arrastre de su borde superior.
- [x] Implementación de límites de altura (mín/máx) para mantener la estabilidad de la UI.
- [x] Integración de la clase de iconos `.msi` de forma global para consistencia.

## Milestone: ODS PostgreSQL Upsert & Dynamic Discovery
**Objective:** Potenciar el nodo "ODS PostgreSQL" con capacidades de descubrimiento dinámico de metadatos y soporte avanzado para operaciones de UPSERT con llaves compuestas.

### Success Criteria
- [ ] Inspección dinámica de tablas y columnas basada en la conexión seleccionada.
- [ ] Selector de tabla tipo combobox con botón de "Refresh" en el panel de propiedades.
- [ ] Soporte para selección de múltiples campos de identidad para el modo UPSERT.
- [ ] Motor de ejecución en Python para operaciones ODS (Append, Overwrite, Upsert).
- [ ] Visualización condicional de propiedades según el modo de escritura seleccionado.



