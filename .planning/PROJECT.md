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

## ✅ Milestone: v1.8 — BFF Service Architecture (SHIPPED 2026-05-31)
**Goal:** Introducir una capa BFF en Node.js + Express entre el SPA y los servicios backend, concentrando auth Keycloak, sesiones server-side y proxy de APIs en un único punto de entrada. El browser nunca ve un token.

**Key Deliverables:**
- BFF Express 5 en `bff/` — containerizado, dockerizado con Redis session store
- OIDC PKCE auth flow completo: login → Keycloak → callback → session (openid-client v6)
- tokenRefresh middleware con coordinación de refreshes concurrentes
- FastAPI proxy con Bearer injection + CORS ownership exclusivo en BFF
- CubeJS proxy con JWT HS256 signing server-side (24h tokens)
- Network isolation: backend y cubejs removidos de red pública
- Frontend migrado: keycloak-js eliminado, auth por /bff/auth/me + cookie HttpOnly

**Key Decisions:**
- Redis elegido sobre PostgreSQL para session store (latencia + TTL nativo)
- PKCE obligatorio incluso para server-side (defensa en profundidad)
- activeRefreshes Map previene race conditions en token refresh concurrente
- Transient Keycloak failures no destruyen sesión si token aún válido

**Archive:** `.planning/milestones/v1.8-ROADMAP.md`

---

## ✅ Milestone: v1.6 ODS PostgreSQL Upsert & Dynamic Discovery (SHIPPED 2026-05-17)
**Objective:** Potenciar el nodo "ODS PostgreSQL" con capacidades de descubrimiento dinámico de metadatos y soporte avanzado para operaciones de UPSERT con llaves compuestas.

### Success Criteria
- [x] Inspección dinámica de tablas y columnas basada en la conexión seleccionada.
- [x] Selector de tabla tipo combobox con botón de "Refresh" en el panel de propiedades.
- [x] Soporte para selección de múltiples campos de identidad para el modo UPSERT.
- [x] Visualización condicional de propiedades según el modo de escritura seleccionado.
- [x] Motor de ejecución en Python para operaciones ODS (Append, Overwrite, Upsert).

**Key Deliverables:**
- ODSExecutor con operaciones Append, Overwrite, Upsert (1029 líneas)
- Deno-to-Python EXEC_ODS signal protocol
- 55 unit tests con cobertura completa
- Per-batch transaction isolation y deadlock prevention

**Archive:** `.planning/milestones/v1.6-ROADMAP.md`

## ✅ Milestone: v1.7 Email Node with Dynamic Templates (SHIPPED 2026-05-17)
**Goal:** Implementar un nodo de tipo Email que permita el envío de correos electrónicos usando conexiones SMTP configuradas, con soporte para plantillas dinámicas usando marcadores `{{expresion}}` en asunto y cuerpo del mensaje.

**Target features:**
- Nodo Email en el editor de flujos con configuración de conexión SMTP
- Soporte para plantillas de texto con marcadores `{{expresion}}` en el asunto del correo
- Cuerpo del mensaje en formato HTML o texto plano con marcadores `{{expresion}}`
- Generación dinámica de contenido complejo (tablas) a partir de arreglos de objetos
- Motor de templating que evalúe expresiones contra el input del nodo
- Integración con el sistema existente de conexiones (DataSource) para SMTP

**Key Deliverables:**
- EmailExecutor con Jinja2 SandboxedEnvironment (630 líneas)
- EXEC_EMAIL signal protocol (Deno-Python integration)
- 44 unit tests (26 executor + 18 schema tests)
- HTML sanitization with nh3 library
- Template syntax hints in UI

**Archive:** `.planning/milestones/v1.7-ROADMAP.md`

## Current Milestone: v1.9 — TBD

**Status:** Planning — run `/gsd:new-milestone` to start the next cycle.



