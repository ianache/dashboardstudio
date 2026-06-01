# Phase 48: Theme Alignment - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Reemplazar todos los colores hardcodeados (`#fff`, `#0f172a`, `#2563eb`, rgba oscuros, etc.) en el SideMenu, TopBar, componentes comunes y todas las views del producto (excepto FlowEditor y su view de Integrations) con las variables CSS del System Design. El tema toggle ya existe (phase 47); esta fase hace que todo el producto responda correctamente a ese toggle.

**Fuera de scope:** FlowEditor canvas, IntegrationsView y FlowEditorView (quedan para una fase futura).

</domain>

<decisions>
## Implementation Decisions

### Alcance de archivos
- Todas las views: HomeView, ConnectionsView, DashboardDesignerView, DashboardViewerView, SettingsView, LoginView, DataTypesView, DiagramTypesView, DimensionalModelEditorView, DimensionalModelListView, ToolCatalogView, VisualizationConfiguratorView, KnowledgeSpacesView
- Todos los componentes: SideMenu, TopBar, AppLayout, DashboardCard, KpiCard, ConfirmModal, PanelHeadBodyPieComponent, QuickActionCard, PageHeader, MIcon
- **Excluidos:** FlowEditorView, IntegrationsView, FlowEditorCanvas — dejarlos para fase futura

### Logo del SideMenu
- Reemplazar `background: #2563eb` por `background: var(--primary-container)`
- El ícono y texto usan `var(--on-primary-container)` para adaptarse al tema

### Bloque de usuario (footer del SideMenu)
- Reemplazar `background: #1e293b` por `background: var(--surface-container-high)`
- Nombre de usuario: `var(--on-surface)`
- Rol/cargo: `var(--on-surface-variant)`

### Nav-item activo
- `background: var(--primary-container)`
- `color: var(--on-primary-container)`
- `border-left-color: var(--primary)`
- Sub-item activo: `color: var(--primary)`

### Nav-item hover
- Reemplazar `background: rgba(15,23,42,0.6)` por `background: var(--surface-container-high)`
- Texto en hover: `var(--on-surface)`
- Sub-item hover: `background: var(--surface-container)`

### Cards en views
- Fondo: `var(--card-bg)` (reemplaza `#fff` y `background: white`)
- Texto principal: `var(--on-surface)` (reemplaza `#0f172a`, `#191c1e`)
- Texto secundario/descripción: `var(--on-surface-variant)` (reemplaza `#64748b`, `#94a3b8`, `#475569`)
- Borde: `var(--outline-variant)` (reemplaza `#e2e8f0`)

### Textos de labels/hints/monospace
- Labels técnicos (host, código): `var(--on-surface-variant)`

### Inline styles en templates
- Eliminar todos los `style="color:#..."` del HTML
- Crear clases semánticas en `<style scoped>` con variables CSS: `.icon-muted`, `.icon-primary`, `.text-secondary`, etc.

### TopBar dropdowns y paneles
- Fondos de dropdown: `var(--surface-container-lowest)`
- Bordes: `var(--outline-variant)`
- Texto: `var(--on-surface)` y `var(--on-surface-variant)`
- Botones de peligro hover: `var(--error-container)`

### Claude's Discretion
- Orden exacto de migración dentro de cada archivo
- Decisión sobre colores de estado (success/warning/error) que ya usan variables legacy (`--success`, `--warning`) — mantener como están si ya funcionan en ambos temas
- Colores específicos de badges, chips y estados de conexión si usan variables del sistema correctamente

</decisions>

<specifics>
## Specific Ideas

- El objetivo es que cambiar el toggle (sun/moon) transforme visualmente TODA la app sin excepción en las views incluidas
- No se introducen nuevos componentes ni layouts — solo migración de valores hardcodeados a tokens
- Los tokens `--card-bg`, `--on-surface`, `--on-surface-variant`, `--surface-container-high`, `--primary-container`, `--on-primary-container`, `--outline-variant` son los más usados — todos ya definidos en `:root` y `[data-theme="light"]`

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `main.css` `:root` + `[data-theme="light"]`: Todos los tokens necesarios ya existen — no hace falta agregar variables nuevas
- `uiStore.setTheme()` / `initTheme()`: El sistema de toggle ya está listo (phase 47)
- `MIcon.vue`: Componente de íconos — cuando recibe color via clase, hereda el color del padre

### Established Patterns
- Todos los componentes usan `<style scoped>` — los cambios son aislados por archivo
- Las variables CSS en `var(--nombre)` se resuelven en cascade desde `[data-theme]` en `<html>`
- No hay TypeScript — JS puro, sin interfaces que cambiar

### Integration Points
- `AppLayout.vue` envuelve todo — si sus fondos usan variables, el shell base queda alineado
- `SideMenu.vue` tiene la mayor densidad de colores hardcodeados (~15 instancias)
- Cada view es independiente — se pueden migrar en paralelo por el executor

</code_context>

<deferred>
## Deferred Ideas

- FlowEditorView + IntegrationsView + canvas de nodos — fase siguiente (FlowEditor tiene su propio sistema visual)
- Animaciones de transición entre temas (fade suave al cambiar) — nueva capacidad, fase separada
- Modo "auto" que siga el sistema operativo (`prefers-color-scheme`) — nueva capacidad

</deferred>

---

*Phase: 48-theme-alignment*
*Context gathered: 2026-06-01*
