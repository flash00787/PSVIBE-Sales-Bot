<template>
  <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
    <div class="p-5 border-b border-gray-100">
      <h1 class="text-lg font-bold text-primary-700">👕 AKT Clothing</h1>
      <p class="text-xs text-gray-400 mt-0.5">ERP System</p>
    </div>
    <nav class="flex-1 p-3 space-y-1">
      <router-link v-for="item in menu" :key="item.path" :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
        :class="$route.path===item.path?'bg-primary-50 text-primary-700':'text-gray-600 hover:bg-gray-50'">
        <span class="text-lg">{{ item.icon }}</span>{{ item.label }}
      </router-link>
    </nav>
    <div class="p-3 border-t border-gray-100">
      <button @click="logout" class="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-500 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors">
        <span>🚪</span> Logout
      </button>
    </div>
  </aside>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const router = useRouter(); const auth = useAuthStore()
const menu = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/sales', label: 'Sales', icon: '🛒' },
  { path: '/products', label: 'Products', icon: '📦' },
  { path: '/purchases', label: 'Purchases', icon: '📥' },
  { path: '/customers', label: 'Customers', icon: '👥' },
  { path: '/suppliers', label: 'Suppliers', icon: '🏭' },
  { path: '/payment-accounts', label: 'Payment Accounts', icon: '💰' },
  { path: '/reports', label: 'Reports', icon: '📈' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
]
function logout() { auth.logout(); router.push('/login') }
</script>