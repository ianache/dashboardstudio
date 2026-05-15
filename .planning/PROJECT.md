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
- [ ] Gestión de conexiones (Email, DB, FTP, HTTP, JWT) con configuración JSON detallada.
- [ ] Centralización de credenciales con encriptación recursiva en el backend.
- [ ] Interfaz de administración (Listado, Creación, Edición, Eliminación, Test de conexión).
- [ ] Soporte para tipos de conexión: SMTP, SQL, FTP/SFTP, HTTP Basic y JWT Token.
- [ ] Integración en el SideMenu bajo el submenu "Data Integration".

