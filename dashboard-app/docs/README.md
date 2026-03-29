# Dashboard Studio — Documentación

Dashboard Studio es una aplicación web para **diseñar y ejecutar dashboards** analíticos conectados a CubeJS como capa semántica. Permite modelar datos dimensionales, crear visualizaciones interactivas y asignar dashboards a usuarios.

## Índice

| Documento | Descripción |
|---|---|
| [Arquitectura](./architecture.md) | Estructura general, patrones y flujo de datos |
| [Guía de inicio](./getting-started.md) | Instalación, configuración y primeros pasos |
| [Rutas y navegación](./routing.md) | Sistema de rutas, guards y roles |
| **Stores (Estado global)** | |
| [auth](./stores/auth.md) | Autenticación y gestión de usuarios |
| [dashboard](./stores/dashboard.md) | CRUD de dashboards y widgets |
| [cubejs](./stores/cubejs.md) | Cliente CubeJS y meta-schema |
| [ui](./stores/ui.md) | Estado de interfaz (sidebar, alertas, breadcrumbs) |
| [dataTypes](./stores/dataTypes.md) | Tipos de datos SQL personalizados |
| [dimensionalModel](./stores/dimensionalModel.md) | Modelos dimensionales (star schema) |
| [colorPalettes](./stores/colorPalettes.md) | Gestión de paletas de colores y predeterminada del sistema |
| **Componentes** | |
| [Layout](./components/layout.md) | AppLayout, SideMenu, TopBar |
| [Dashboard](./components/dashboard.md) | DashboardGrid, DashboardWidget, ChartConfigModal, DashboardFilterBar |
| [Charts](./components/charts.md) | EChartWrapper — tipos de gráfico |
| **Features** | |
| [Dashboards](./features/dashboards.md) | Diseño, visualización y filtros de dashboards |
| [Modelos Dimensionales](./features/dimensional-models.md) | Editor de modelos, canvas, relaciones y exportación |
| [Tipos de Datos](./features/data-types.md) | Biblioteca de tipos SQL |
| [Integración CubeJS](./features/cubejs-integration.md) | Consultas, mock data y exportación |

## Stack tecnológico

| Tecnología | Versión | Uso |
|---|---|---|
| Vue 3 | ^3.4 | Framework principal, Composition API + `<script setup>` |
| Pinia | ^2.1 | Estado global (7 stores) |
| Vue Router | ^4.3 | SPA con guards de rol |
| Apache ECharts | ^5.4 | Renderizado de gráficos |
| vue-echarts | ^6.6 | Wrapper Vue para ECharts |
| @cubejs-client/core | ^0.35 | Cliente CubeJS |
| js-yaml | ^4.1 | Import/Export YAML de modelos |
| jszip | ^3.10 | Exportación ZIP de esquemas CubeJS |
| Vite | ^5.2 | Bundler y dev server |

## Roles de usuario

| Rol | Email demo | Capacidades |
|---|---|---|
| `designer` | admin@demo.com / admin123 | Crear/editar dashboards y modelos, configurar widgets, gestionar usuarios |
| `viewer` | viewer@demo.com / viewer123 | Ver dashboards asignados o públicos |

## Comandos esenciales

```bash
npm run dev      # Servidor de desarrollo → http://localhost:3000
npm run build    # Build de producción
npm run preview  # Vista previa del build
```
