# Feature: Dashboards

## Descripción general

Los dashboards son colecciones de widgets visuales organizados en un canvas de 12 columnas. Los **designers** los crean y configuran; los **viewers** los visualizan (si son públicos o les fueron asignados).

## Vistas involucradas

| Vista | Ruta | Rol |
|---|---|---|
| `DashboardDesignerView` | `/designer`, `/designer/:id` | Designer |
| `DashboardViewerView` | `/dashboard/:id` | Todos |

---

## Modo lista (`DashboardDesignerView` sin ID)

### Crear dashboard

1. Clic en **"+ Nuevo Dashboard"**
2. Modal con campos: nombre (obligatorio), descripción, visibilidad pública
3. Al confirmar → se crea el dashboard y navega al editor

### Tarjeta de dashboard

Muestra:
- Nombre y descripción (editables inline con doble clic)
- Badges: nº de widgets, estado público/privado
- Acciones: Editar, Duplicar, Asignar usuarios, Eliminar

### Asignación de usuarios

Botón "Asignar" → modal con lista de viewers. Clic para toggle de acceso. Guarda en `dashboard.assignedUsers` y en `authStore.allUsers[].assignedDashboards`.

---

## Modo editor (`DashboardDesignerView` con `:id`)

### Toolbar del editor

```
[← Volver]  [Nombre del dashboard ✏]  [Modo: Diseño | Preview]  [+ Añadir widget]  [💾 Guardar]
```

- **Editar nombre**: doble clic sobre el título
- **Modo Diseño/Preview**: alterna entre canvas editable y vista final
- **Guardar**: la persistencia es inmediata, el botón emite una notificación de confirmación

### Añadir widget

1. Clic en **"+ Añadir widget"**
2. Se crea un widget vacío tipo `bar` en la posición `{ x: 0, y: 0, w: 6, h: 3 }`
3. Se abre automáticamente el modal de configuración

### Configurar widget

Doble clic o clic en ⚙️ abre `ChartConfigModal` con 4 pestañas (ver [Componentes de Dashboard](../components/dashboard.md)).

### Drag & resize

- **Drag**: mantener pulsado en el header del widget, arrastrar a nueva posición
- **Resize E**: arrastrar handle derecho para cambiar ancho
- **Resize S**: arrastrar handle inferior para cambiar alto
- **Resize SE**: arrastrar esquina inferior derecha

Los cambios se guardan en tiempo real en el store.

### Filtros de dashboard

En modo Diseño se puede gestionar la barra de filtros:
1. Clic en **"Filtros"** → panel de definición de filtros
2. Añadir filtro: seleccionar dimensión CubeJS, tipo y operador
3. Los filtros se muestran en la `DashboardFilterBar` al visualizar

---

## Vista de visualización (`DashboardViewerView`)

### Control de acceso

El dashboard es accesible si:
- `dashboard.isPublic === true`, **o**
- `authStore.user.id` está en `dashboard.assignedUsers`

Si no cumple, redirige a `/`.

### Interfaz

```
[← Volver]  [Nombre del dashboard]    [🔄 Actualizar todo] [✏ Editar (designer)]
[Filtro: Estado ▾] [Filtro: Fecha desde/hasta]
┌────────────────────────────────────┐
│ Widget 1          │ Widget 2        │
│ (EChartWrapper)   │ (EChartWrapper) │
└───────────────────┴─────────────────┘
```

### Filtros activos

Los valores de los filtros del usuario se combinan con `useDashboardFilters` y se pasan a todos los widgets como `dashboardFilters`. Cada widget los incorpora a su query CubeJS.

### Actualizar todo

Botón que fuerza `fetchData()` en todos los widgets simultáneamente.

---

## Flujo completo de datos en un widget

```
DashboardWidget
  └── useCubeQuery(widget, filtersRef)
        ├── Si useMockData || !cubeStore.isConfigured
        │     └── generateMockData(chartType) → data
        └── cubeStore.executeQuery(buildQuery(widget, filters))
              └── ResultSet.tablePivot() → data
                    └── transformData(data) → [{ label, value }]
                          └── EChartWrapper recibe data
```

---

## Persistencia

Los dashboards se persisten en `localStorage['dashboards']`. No hay backend — todos los cambios son locales al navegador.

Para compartir dashboards entre usuarios se necesitaría un backend real (fuera del scope actual).
