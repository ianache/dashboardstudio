# Componentes reutilizables — Dashboard Studio

Referencia completa de los 21 componentes Vue del proyecto, organizados por carpeta.

---

## `common/` — Genéricos

### `MIcon`
**Ruta:** `src/components/common/MIcon.vue`

Wrapper de **Material Symbols Outlined** con control completo de las variaciones de fuente.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `icon` | `String` | **requerido** | Nombre del ícono (ej. `"dashboard"`, `"add_circle"`) |
| `size` | `Number` | `24` | Tamaño óptico en px — también controla `font-size`. Valores: `20`, `24`, `40`, `48` |
| `fill` | `Number` | `0` | `0` = outlined, `1` = filled |
| `weight` | `Number` | `400` | Grosor del trazo: `100` – `700` |
| `grade` | `Number` | `0` | Énfasis visual: `-50`, `0`, `200` |

```vue
<MIcon icon="analytics" :size="20" :fill="1" :weight="600" />
```

---

### `KpiCard`
**Ruta:** `src/components/common/KpiCard.vue`

Tarjeta de métrica KPI para el **HomeView** — muestra icono, valor principal y tendencia.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `label` | `String` | **requerido** | Etiqueta de la métrica |
| `value` | `String\|Number` | **requerido** | Valor a mostrar |
| `icon` | `String` | `"dashboard"` | Nombre del ícono Material Symbols |
| `trend` | `String` | `""` | Texto de tendencia (ej. `"+12% este mes"`) |
| `iconColor` | `String` | `var(--primary)` | Color del ícono |
| `iconBg` | `String` | `rgba(0,88,190,0.1)` | Fondo del contenedor del ícono |
| `iconFill` | `Number` | `0` | Fill del ícono: `0` outlined, `1` filled |

```vue
<KpiCard label="Dashboards activos" value="12" icon="dashboard" trend="+3 este mes" />
```

---

### `QuickActionCard`
**Ruta:** `src/components/common/QuickActionCard.vue`

Tarjeta de acción rápida clickeable para el **HomeView**.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `title` | `String` | **requerido** | Título de la acción |
| `description` | `String` | `""` | Descripción breve |
| `icon` | `String` | `"add"` | Nombre del ícono Material Symbols |
| `variant` | `String` | `"default"` | Estilo visual: `"primary"` \| `"default"` \| `"secondary"` |

| Emit | Payload | Descripción |
|---|---|---|
| `click` | — | El usuario hizo clic en la tarjeta |

```vue
<QuickActionCard
  title="Nuevo dashboard"
  description="Crea y configura un nuevo dashboard"
  icon="add_circle"
  variant="primary"
  @click="router.push('/designer')"
/>
```

---

### `DashboardCard`
**Ruta:** `src/components/common/DashboardCard.vue`

Tarjeta de dashboard para el **DashboardViewerView** — muestra gradiente de portada, badge de estado y acciones.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `name` | `String` | **requerido** | Nombre del dashboard |
| `description` | `String` | `""` | Descripción breve |
| `widgetCount` | `Number` | `0` | Cantidad de widgets |
| `updatedLabel` | `String` | `""` | Texto de última actualización |
| `colorIndex` | `Number` | `0` | Índice del gradiente de portada (0–4) |
| `badge` | `Object` | `null` | `{ text, variant: 'active'\|'priority'\|'public' }` |

| Emit | Payload | Descripción |
|---|---|---|
| `open` | — | Abrir el dashboard |
| `share` | — | Compartir |
| `menu` | — | Abrir menú contextual |

```vue
<DashboardCard
  name="Ventas Q1"
  :widgetCount="8"
  updated-label="Hoy"
  :color-index="1"
  :badge="{ text: 'Activo', variant: 'active' }"
  @open="openDashboard(id)"
/>
```

---

### `PanelHeadBodyPieComponent`
**Ruta:** `src/components/common/PanelHeadBodyPieComponent.vue`

Panel colapsable con cabecera, cuerpo de contenido libre y gráfico de donut integrado.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `title` | `String` | **requerido** | Título de la cabecera |
| `subtitle` | `String` | `""` | Subtítulo |
| `icon` | `String` | `""` | Ícono Material Symbols en cabecera |
| `expanded` | `Boolean` | `false` | Estado inicial expandido/colapsado |

| Emit | Descripción |
|---|---|
| `expand` | Panel se expande |
| `collapse` | Panel se colapsa |
| `toggle` | Cambio de estado |
| `reset` | Usuario resetea filtros |
| `apply` | Usuario aplica selección |

---

## `layout/` — Shell de la aplicación

### `AppLayout`
**Ruta:** `src/components/layout/AppLayout.vue`

Shell principal de la app. Compone `SideMenu` + `TopBar` + `<router-view>`. No recibe props ni emite eventos — es el wrapper raíz de todas las vistas autenticadas.

---

### `SideMenu`
**Ruta:** `src/components/layout/SideMenu.vue`

Sidebar de navegación colapsable. Muestra las secciones de menú según el rol del usuario (`designer` ve "Diseño"; `viewer` solo ve sus dashboards). El estado de colapso se persiste en el store `ui`.

---

### `TopBar`
**Ruta:** `src/components/layout/TopBar.vue`

Barra superior fija. Incluye breadcrumbs dinámicos, dropdown de alertas del sistema y dropdown de usuario con cierre de sesión.

---

## `charts/` — Visualizaciones

### `EChartWrapper`
**Ruta:** `src/components/charts/EChartWrapper.vue`

Motor central de gráficos. Construye la `option` de Apache ECharts a partir del widget y renderiza el gráfico. Fusiona `chartOptions` libre del widget sobre la opción base (deep merge).

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Objeto widget completo con `chartType`, `cubeQuery`, `chartOptions`, etc. |
| `data` | `Array` | `[]` | Datos transformados: `[{ label, value, value2? }]` |
| `loading` | `Boolean` | `false` | Muestra skeleton de carga |
| `error` | `String` | `null` | Mensaje de error a mostrar |
| `chartType` | `String` | `"bar"` | Tipo: `bar` \| `line` \| `pie` \| `gauge` \| `radar` \| `combined` \| `table` \| `kpi` |
| `dashboardPalette` | `String` | `null` | ID de la paleta activa del dashboard |

**Tipos de gráfico soportados:**

| Tipo | Descripción |
|---|---|
| `bar` | Barras verticales, color por serie, borderRadius en el tope |
| `line` | Líneas suaves con área semitransparente |
| `pie` | Donut chart con labels de porcentaje |
| `gauge` | Semicírculo / círculo / progreso / velocímetro — configurable vía `gaugeOptions` |
| `radar` | Gráfico de araña con área rellena |
| `combined` | Barras (eje Y izquierdo) + Línea (eje Y derecho) |

---

### `KpiWidget`
**Ruta:** `src/components/charts/KpiWidget.vue`

Render especializado para `chartType: 'kpi'`. Muestra valor grande, label, ícono y color de acento. La apariencia se controla via `widget.kpiOptions`.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Widget con `kpiOptions: { icon, accentColor, prefix, suffix, showTrend }` |
| `data` | `Array` | `[]` | `[{ value }]` — usa el primer elemento |
| `loading` | `Boolean` | `false` | Skeleton de carga |
| `error` | `String` | `null` | Mensaje de error |

---

### `DataTableWidget`
**Ruta:** `src/components/charts/DataTableWidget.vue`

Render de tabla para `chartType: 'table'`. Incluye paginación, búsqueda por columna y exportación a CSV.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Widget con definición de columnas en `cubeQuery` |
| `data` | `Array` | `[]` | Filas de datos |
| `loading` | `Boolean` | `false` | Skeleton de tabla |
| `error` | `String` | `null` | Mensaje de error |

---

## `dashboard/` — Diseñador y viewer

### `DashboardWidget`
**Ruta:** `src/components/dashboard/DashboardWidget.vue`

Tarjeta-widget completa. Orquesta la cabecera de acciones, la ejecución de la query CubeJS y delega el render a `EChartWrapper`, `KpiWidget` o `DataTableWidget` según `chartType`.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Objeto widget |
| `isDesignMode` | `Boolean` | `false` | Activa handles de drag/resize y menú de acciones |
| `isSelected` | `Boolean` | `false` | Resalta el widget con borde de selección |
| `isMaximized` | `Boolean` | `false` | Modo pantalla completa |
| `dashboardFilters` | `Array` | `[]` | Filtros activos del dashboard |
| `dashboardPalette` | `String` | `null` | ID de la paleta de colores activa |

| Emit | Payload | Descripción |
|---|---|---|
| `configure` | `widgetId` | Abrir `ChartConfigModal` |
| `layout` | `widgetId` | Abrir `ChartLayoutModal` |
| `remove` | `widgetId` | Eliminar widget |
| `select` | `widgetId` | Seleccionar widget |
| `resize-start` | `{ widgetId, direction, event }` | Inicio de resize |
| `drag-start` | `{ widgetId, event }` | Inicio de drag |
| `toggle-maximize` | `widgetId` | Alternar maximización |

---

### `DashboardGrid`
**Ruta:** `src/components/dashboard/DashboardGrid.vue`

Canvas de posicionamiento libre con **12 columnas**, alto de fila de 90px y gap de 10px. Implementa drag-and-resize nativo con snap automático al soltar.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widgets` | `Array` | `[]` | Lista de widgets con `position: { x, y, w, h }` |
| `dashboardId` | `String` | **requerido** | ID del dashboard activo |
| `isDesignMode` | `Boolean` | `false` | Habilita drag/resize |
| `dashboardFilters` | `Array` | `[]` | Filtros activos |
| `dashboardPalette` | `String` | `null` | ID de la paleta activa |

| Emit | Payload | Descripción |
|---|---|---|
| `configure-widget` | `widgetId` | Propagar al padre para abrir config |
| `layout-widget` | `widgetId` | Propagar al padre para abrir layout |
| `remove-widget` | `widgetId` | Propagar al padre para eliminar |
| `widget-moved` | `{ id, position }` | Widget reposicionado o redimensionado |

---

### `DashboardFilterBar`
**Ruta:** `src/components/dashboard/DashboardFilterBar.vue`

Barra de filtros interactivos por dimensión CubeJS. En modo diseño permite añadir/quitar filtros; en modo viewer muestra los dropdowns con valores reales cargados desde CubeJS.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `dashboardId` | `String` | **requerido** | ID del dashboard |
| `filters` | `Array` | `[]` | Definición de filtros configurados |
| `modelValue` | `Object` | `{}` | Valores activos de filtros (`v-model`) |
| `isDesignMode` | `Boolean` | `false` | Muestra controles de edición |

| Emit | Payload | Descripción |
|---|---|---|
| `update:modelValue` | `filtersObject` | Nuevo estado de filtros (para `v-model`) |
| `refresh` | — | Solicita recarga de datos al padre |

---

### `ChartConfigModal`
**Ruta:** `src/components/dashboard/ChartConfigModal.vue`

Modal de configuración completa del widget. Organizado en 4 tabs:
1. **General** — título, tipo de gráfico, paleta
2. **Datos CubeJS** — measures, dimensions, time dimension, filtros, límite
3. **Visualización** — opciones por tipo (KPI, Pie, Gauge, ECharts JSON)
4. **Esquema** — JSON viewer del widget completo

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Widget a configurar |

| Emit | Payload | Descripción |
|---|---|---|
| `close` | — | Cerrar sin guardar |
| `save` | `widgetUpdates` | Guardar cambios |

---

### `ChartLayoutModal`
**Ruta:** `src/components/dashboard/ChartLayoutModal.vue`

Modal de **formato visual** del widget ("Formato del widget"). Controla título y opciones específicas por tipo:
- **KPI:** ícono, color acento, prefijo/sufijo, tendencia
- **Gauge:** variante, escala min/max/unidad, grosor arco, zonas de color, aguja, marcas
- **Pie:** mostrar valor/porcentaje/total
- **ECharts:** override JSON de opciones

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `widget` | `Object` | **requerido** | Widget a formatear |

| Emit | Payload | Descripción |
|---|---|---|
| `close` | — | Cerrar sin guardar |
| `save` | `{ title, kpiOptions? \| gaugeOptions? \| pieOptions? \| chartOptions? }` | Guardar formato |

---

### `DesignerCard`
**Ruta:** `src/components/dashboard/DesignerCard.vue`

Tarjeta de dashboard para el **DashboardDesignerView**. Muestra portada con gradiente, métricas de widgets, estado público/privado y usuarios asignados. Acciones completas de gestión.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `name` | `String` | **requerido** | Nombre del dashboard |
| `description` | `String` | `""` | Descripción |
| `widgetCount` | `Number` | `0` | Cantidad de widgets |
| `isPublic` | `Boolean` | `false` | Si el dashboard es público |
| `assignedUsersCount` | `Number` | `0` | Cantidad de usuarios asignados |
| `colorIndex` | `Number` | `0` | Índice del gradiente (0–5) |
| `categoryIcon` | `String` | `"dashboard"` | Ícono de categoría en portada |

| Emit | Descripción |
|---|---|
| `design` | Abrir en modo diseño |
| `assign` | Abrir modal de asignación de usuarios |
| `view` | Ver en modo viewer |
| `export` | Exportar dashboard como JSON |
| `delete` | Eliminar dashboard |

---

## `dimensional-model/` — Modelado dimensional

### `ModelCard`
**Ruta:** `src/components/dimensional-model/ModelCard.vue`

Tarjeta de modelo dimensional con edición inline de nombre y descripción. Muestra métricas de nodos (facts, dimensions, relaciones).

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `name` | `String` | **requerido** | Nombre del modelo |
| `description` | `String` | `""` | Descripción |
| `isGlobal` | `Boolean` | `false` | Indica si es un modelo global compartido |
| `factCount` | `Number` | `0` | Cantidad de tablas fact |
| `dimCount` | `Number` | `0` | Cantidad de tablas dimension |
| `relCount` | `Number` | `0` | Cantidad de relaciones |
| `colorIndex` | `Number` | `0` | Índice del gradiente de portada (0–5) |

| Emit | Payload | Descripción |
|---|---|---|
| `design` | — | Abrir editor del modelo |
| `edit` | — | Editar metadatos |
| `export` | — | Exportar como YAML |
| `delete` | — | Eliminar modelo |
| `update:name` | `string` | Nombre editado inline |
| `update:description` | `string` | Descripción editada inline |

---

### `DiagramTabBar`
**Ruta:** `src/components/dimensional-model/DiagramTabBar.vue`

Barra de tabs para navegar entre múltiples diagramas dentro de un modelo. Soporta rename inline con doble clic.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `diagrams` | `Array` | **requerido** | Lista de diagramas `[{ id, name }]` |
| `activeDiagramId` | `String` | **requerido** | ID del diagrama activo |

| Emit | Payload | Descripción |
|---|---|---|
| `update:activeDiagramId` | `id` | Cambio de tab activo (para `v-model`) |
| `create-diagram` | — | Crear nuevo diagrama |
| `delete-diagram` | `id` | Eliminar diagrama |
| `rename-diagram` | `{ id, name }` | Renombrar diagrama |

```vue
<DiagramTabBar
  :diagrams="model.diagrams"
  v-model:activeDiagramId="activeDiagramId"
  @create-diagram="addDiagram"
  @delete-diagram="removeDiagram"
/>
```

---

### `DiagramPropsPanel`
**Ruta:** `src/components/dimensional-model/DiagramPropsPanel.vue`

Panel lateral de propiedades del diagrama activo. Permite renombrar y editar la descripción con preview Markdown (vía `marked` + `DOMPurify`).

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `diagram` | `Object` | **requerido** | Diagrama activo `{ id, name, description }` |

| Emit | Payload | Descripción |
|---|---|---|
| `rename` | `string` | Nuevo nombre del diagrama |
| `update-description` | `string` | Nueva descripción |

---

### `AddNodeToDiagramModal`
**Ruta:** `src/components/dimensional-model/AddNodeToDiagramModal.vue`

Modal para seleccionar tablas (nodos) del modelo y añadirlas al diagrama activo. Solo muestra nodos que aún no están en el diagrama.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `model` | `Object` | **requerido** | Modelo dimensional con su lista de `nodes` |
| `activeDiagram` | `Object` | **requerido** | Diagrama activo con su lista de `diagramNodes` |

| Emit | Payload | Descripción |
|---|---|---|
| `close` | — | Cerrar sin añadir |
| `add-nodes` | `string[]` | Array de IDs de nodos seleccionados |

```vue
<AddNodeToDiagramModal
  :model="currentModel"
  :activeDiagram="activeDiagram"
  @close="showModal = false"
  @add-nodes="handleAddNodes"
/>
```
