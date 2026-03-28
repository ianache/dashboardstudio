# Store: ui

**Archivo:** `src/stores/ui.js`

Gestiona el estado de la interfaz de usuario: sidebar, breadcrumbs, sistema de alertas y dropdowns.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `sidebarCollapsed` | `boolean` | Si el sidebar está colapsado |
| `breadcrumbs` | `string[]` | Segmentos actuales de navegación |
| `alerts` | `array` | Cola de alertas/notificaciones activas |
| `openDropdown` | `string \| null` | ID del dropdown actualmente abierto |

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `isSidebarCollapsed` | `boolean` | Estado del sidebar |
| `currentBreadcrumbs` | `string[]` | Migas de pan actuales |
| `activeAlerts` | `array` | Alertas sin descartar |

## Acciones

### `toggleSidebar()`

Alterna el estado colapsado/expandido del sidebar y lo persiste en localStorage.

### `setSidebarCollapsed(value)`

Fuerza el sidebar a un estado específico.

### `setBreadcrumbs(segments)`

Actualiza la ruta de navegación mostrada en el `TopBar`.

```javascript
uiStore.setBreadcrumbs(['Modelos', 'Editor'])
// TopBar muestra: Modelos › Editor
```

### `notify({ message, type, duration? })`

Añade una notificación a la cola. Se auto-descarta después de `duration` ms (por defecto 3000).

```javascript
uiStore.notify({ message: 'Modelo guardado', type: 'success' })
uiStore.notify({ message: 'Error al conectar', type: 'error', duration: 5000 })
```

Tipos disponibles: `'success'` | `'error'` | `'warning'` | `'info'`

### `dismissAlert(id)`

Elimina una alerta específica de la cola.

### `openDropdownMenu(id)` / `closeDropdown()`

Controla qué dropdown está abierto. Solo uno puede estar abierto a la vez.

## Sidebar colapsado

Cuando el sidebar está colapsado (`isSidebarCollapsed = true`):
- Solo muestra iconos (anchura `--sidebar-collapsed-width: 56px`)
- Los labels y submenús se ocultan
- El contenido principal se expande

El estado persiste en `localStorage['sidebarCollapsed']`.
