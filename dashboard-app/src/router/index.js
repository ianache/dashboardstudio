import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true }
  },
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
        path: 'models/:id',
        name: 'ModelEditor',
        component: () => import('@/views/DimensionalModelEditorView.vue'),
        meta: { requiresDesigner: true, breadcrumbs: ['Modelos', 'Editor'] }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { breadcrumbs: ['Configuración'] }
      }
    ]
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

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.public) return next()

  if (!authStore.isAuthenticated) return next('/login')

  if (to.meta.requiresDesigner && !authStore.isDesigner) {
    return next('/')
  }

  next()
})

export default router
