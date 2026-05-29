import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/HomeView.vue'),
        meta: { breadcrumbs: ['Inicio'] }
      },
      {
        path: 'designer',
        name: 'DesignerList',
        component: () => import('@/views/DashboardDesignerView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Diseño', 'Mis Dashboards'] }
      },
      {
        path: 'designer/:id',
        name: 'DesignerEdit',
        component: () => import('@/views/DashboardDesignerView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Diseño', 'Editor'] }
      },
      {
        path: 'designer/:dashboardId/configure',
        name: 'VisualizationConfigurator',
        component: () => import('@/views/VisualizationConfiguratorView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Diseño', 'Configurador'] }
      },
      {
        path: 'designer/:dashboardId/configure/:widgetId',
        name: 'VisualizationConfiguratorEdit',
        component: () => import('@/views/VisualizationConfiguratorView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Diseño', 'Configurador'] }
      },
      {
        path: 'dashboard/:id',
        name: 'DashboardView',
        component: () => import('@/views/DashboardViewerView.vue'),
        meta: { breadcrumbs: ['Dashboards'] }
      },
      {
        path: 'models',
        name: 'ModelList',
        component: () => import('@/views/DimensionalModelListView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Modelos'] }
      },
      {
        path: 'models/data-types',
        name: 'DataTypes',
        component: () => import('@/views/DataTypesView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Modelos', 'Tipos de datos'] }
      },
      {
        path: 'models/knowledge-spaces',
        name: 'KnowledgeSpaces',
        component: () => import('@/views/KnowledgeSpacesView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Modelos', 'Knowledge Spaces'] }
      },
      {
        path: 'models/:id',
        name: 'ModelEditor',
        component: () => import('@/views/DimensionalModelEditorView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Modelos', 'Editor'] }
      },
      {
        path: 'integrations',
        name: 'Integrations',
        component: () => import('@/views/IntegrationsView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Data Integration', 'Integrations'] }
      },
      {
        path: 'integrations/diagram-types',
        name: 'DiagramTypes',
        component: () => import('@/views/DiagramTypesView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Data Integration', 'Tipos de Diagrama'] }
      },
      {
        path: 'integrations/tool-catalog',
        name: 'ToolCatalog',
        component: () => import('@/views/ToolCatalogView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Data Integration', 'Catálogo de Herramientas'] }
      },
      {
        path: 'integrations/connections',
        name: 'Connections',
        component: () => import('@/views/ConnectionsView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Data Integration', 'Conexiones'] }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        // Only admin and designer can access settings
        meta: { requiresDesigner: true, breadcrumbs: ['Configuración'] }
      }
    ]
  },
  {
    path: '/integrations/:id/editor',
    name: 'IntegrationEditor',
    component: () => import('@/views/FlowEditorView.vue'),
    meta: { requiresAuth: true, requiresDesigner: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // App only mounts after BFF session is verified in main.js.
  // If we reach this guard and not initialized, it means something bypassed the main.js flow.
  if (!authStore.initialized) {
    await authStore.initialize()
  }

  // If after initialization we still have no user and route requires auth, 
  // redirect to BFF login.
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    authStore.login()
    return
  }

  // Role-based protection
  if (to.meta.requiresDesigner && !authStore.isDesigner) {
    return next('/')
  }

  next()
})

export default router
