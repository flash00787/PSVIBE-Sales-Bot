import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/products', name: 'Products', component: () => import('../views/Products.vue'), meta: { requiresAuth: true } },
  { path: '/sales', name: 'Sales', component: () => import('../views/Sales.vue'), meta: { requiresAuth: true } },
  { path: '/purchases', name: 'Purchases', component: () => import('../views/Purchases.vue'), meta: { requiresAuth: true } },
  { path: '/customers', name: 'Customers', component: () => import('../views/Customers.vue'), meta: { requiresAuth: true } },
  { path: '/suppliers', name: 'Suppliers', component: () => import('../views/Suppliers.vue'), meta: { requiresAuth: true } },
  { path: '/payment-accounts', name: 'PaymentAccounts', component: () => import('../views/PaymentAccounts.vue'), meta: { requiresAuth: true } },
  { path: '/reports', name: 'Reports', component: () => import('../views/Reports.vue'), meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory('/akt-clothing-shop/'), routes })

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) return next('/login')
  if (to.meta.guest && auth.token) return next('/')
  next()
})

export default router