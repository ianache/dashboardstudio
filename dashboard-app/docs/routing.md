# Rutas y navegación

## Definición de rutas (`src/router/index.js`)

| Ruta | Nombre | Componente | Requiere |
|---|---|---|---|
| `/login` | `Login` | `LoginView` | Pública |
| `/` | `Home` | `HomeView` | Auth |
| `/designer` | `DesignerList` | `DashboardDesignerView` | Designer |
| `/designer/:id` | `DesignerEdit` | `DashboardDesignerView` | Designer |
| `/dashboard/:id` | `DashboardView` | `DashboardViewerView` | Auth |
| `/models` | `ModelList` | `DimensionalModelListView` | Designer |
| `/models/data-types` | `DataTypes` | `DataTypesView` | Designer |
| `/models/:id` | `ModelEditor` | `DimensionalModelEditorView` | Designer |
| `/settings` | `Settings` | `SettingsView` | Auth |

> **Nota:** La ruta `/models/data-types` está definida **antes** de `/models/:id` para evitar que el segmento `data-types` sea interpretado como un ID dinámico.

## Guards de navegación

El guard global `router.beforeEach` aplica las siguientes reglas en orden:

```
1. ¿La ruta es pública? → Pasar
2. ¿El usuario no está autenticado? → Redirigir a /login
3. ¿La ruta requiere designer y el usuario es viewer? → Redirigir a /
4. Pasar
```

## Meta de rutas

| Meta | Tipo | Descripción |
|---|---|---|
| `public` | boolean | La ruta no requiere autenticación |
| `requiresAuth` | boolean | Requiere usuario autenticado (implícito en hijos de `/`) |
| `requiresDesigner` | boolean | Solo accesible para rol `designer` |
| `breadcrumbs` | string[] | Texto de migas de pan (usado por `TopBar`) |

## Navegación programática

```javascript
// Ejemplos comunes en los views
router.push('/models')
router.push(`/models/${model.id}`)
router.push(`/models?new=1`)   // Abre el modal de nuevo modelo
router.push(`/designer/${dashboard.id}`)
```

## Redirección post-login

Después de un login exitoso, `LoginView` redirige a `/` (Home). No hay redirección a la ruta original pendiente — comportamiento intencional para la demo.

## Módulo de layout

Todas las rutas autenticadas son hijos de `/` cuyo componente es `AppLayout.vue`. Esto garantiza que el sidebar y el topbar estén presentes en todas las páginas protegidas sin duplicar el shell.

```javascript
{
  path: '/',
  component: AppLayout,       // shell siempre presente
  meta: { requiresAuth: true },
  children: [
    { path: '', component: HomeView },
    { path: 'designer', component: DashboardDesignerView, meta: { requiresDesigner: true } },
    // ...
  ]
}
```
