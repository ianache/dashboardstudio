# Componentes de Layout

## AppLayout.vue

**Archivo:** `src/components/layout/AppLayout.vue`

Shell principal de la aplicación. Estructura la página con el sidebar fijo, el topbar y el área de contenido principal.

```
┌─────────────────────────────────────────────────┐
│  TopBar (56px alto, fijo)                        │
├──────────┬──────────────────────────────────────┤
│ SideMenu │  <router-view> (área principal)       │
│ (240px   │                                       │
│  o 56px  │                                       │
│  colaps) │                                       │
└──────────┴──────────────────────────────────────┘
```

### Props

Ninguna. El layout obtiene su estado de los stores `auth` y `ui`.

### Comportamiento

- Escucha clics fuera del sidebar para cerrar dropdowns abiertos
- Aplica clase `.sidebar-collapsed` al shell cuando `uiStore.isSidebarCollapsed`
- El área principal (`main`) tiene `padding-left` que varía según el estado del sidebar usando transición CSS

---

## SideMenu.vue

**Archivo:** `src/components/layout/SideMenu.vue`

Sidebar de navegación colapsable con secciones por rol.

### Estructura de navegación

```
─ Inicio                         (todos los roles)

DISEÑO (solo designers)
─ Mis Dashboards
  • Nombre del dashboard (×n)
  • + Nuevo dashboard

─ Modelos
  • Ver todos
  • Nuevo modelo
  • Tipos de datos

─ Configuración                  (todos los roles)
```

### Props

Ninguna. Lee de `authStore`, `dashboardStore`, y `uiStore`.

### Estado local

| Ref | Tipo | Descripción |
|---|---|---|
| `openSections` | `object` | Qué secciones están expandidas (`{ dashboards: true, models: true }`) |

### Comportamiento colapsado

Cuando `isSidebarCollapsed`:
- Solo se muestran iconos SVG de cada item
- Las secciones colapsables y los sub-items se ocultan
- Los tooltips (`data-tooltip`) aparecen al hacer hover

### Navegación activa

Se compara `$route.name` contra nombres de rutas para marcar el item activo con la clase `.active`.

```javascript
const isModelRoute = computed(() =>
  ['ModelList', 'ModelEditor', 'DataTypes'].includes(router.currentRoute.value.name)
)
```

### Crear desde sidebar

- **"+ Nuevo dashboard"**: navega a `/designer?new=1` (el view detecta la query y abre el modal)
- **"Nuevo modelo"**: navega a `/models?new=1`

---

## TopBar.vue

**Archivo:** `src/components/layout/TopBar.vue`

Barra superior fija con breadcrumbs, alertas y menú de usuario.

### Secciones

```
┌──────────────────────────────────────────────────────────┐
│ ☰  Inicio › Modelos › Editor    [🔔 alertas] [AV ▾ user]│
└──────────────────────────────────────────────────────────┘
```

**Izquierda:**
- Botón hamburguesa → `uiStore.toggleSidebar()`
- Breadcrumbs separados con `›`

**Derecha:**
- **Campana de alertas**: dropdown con la cola de `uiStore.activeAlerts`; badge numérico si hay activas
- **Avatar de usuario**: dropdown con nombre, rol, y botón "Cerrar sesión"

### Cierre de dropdowns

Al hacer clic fuera de un dropdown, se llama `uiStore.closeDropdown()`. `AppLayout` tiene un listener global para esto.
