<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Sidebar -->
    <aside class="fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform -translate-x-full lg:translate-x-0 transition-transform duration-200"
           :class="{ 'translate-x-0': sidebarOpen }">
      <!-- Brand -->
      <div class="flex items-center gap-3 px-6 py-5 border-b border-gray-200 dark:border-gray-700">
        <img :src="logoIcon" alt="PS VIBE" class="w-[60px] h-[60px]" />
        <div>
          <h1 class="text-sm font-bold text-gray-900 dark:text-white">PS VIBE</h1>
          <p class="text-xs text-gray-500 dark:text-gray-400">Dashboard</p>
        </div>
      </div>

      <!-- Branch Selector -->
      <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <div class="relative">
          <button
            @click="branchDropdownOpen = !branchDropdownOpen"
            class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-150 border border-gray-200 dark:border-gray-600"
          >
            <div class="flex items-center gap-2 min-w-0">
              <svg class="w-4 h-4 flex-shrink-0 text-vibe-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span class="truncate text-gray-700 dark:text-gray-300 font-medium">
                {{ branchStore.currentBranch?.name || 'PS VIBE Main' }}
              </span>
            </div>
            <svg class="w-4 h-4 flex-shrink-0 text-gray-400 transition-transform" :class="branchDropdownOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            v-if="branchDropdownOpen"
            class="absolute left-0 right-0 top-full mt-1 z-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg overflow-hidden"
          >
            <div v-if="branchStore.loading" class="px-3 py-2 text-xs text-gray-400 text-center">
              Loading...
            </div>
            <div v-else-if="branchStore.error" class="px-3 py-2 text-xs text-red-400 text-center">
              {{ branchStore.error }}
            </div>
            <button
              v-for="branch in branchStore.branches"
              :key="branch.id"
              @click="selectBranch(branch.id)"
              class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors"
              :class="branch.id === branchStore.currentBranchId
                ? 'bg-vibe-purple/10 text-vibe-purple font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
            >
              <span class="w-5 h-5 flex-shrink-0 rounded bg-vibe-purple/10 text-vibe-purple text-[10px] font-bold flex items-center justify-center">
                {{ branch.code?.charAt(0) || 'M' }}
              </span>
              <div class="min-w-0 text-left">
                <div class="truncate text-sm">{{ branch.name }}</div>
                <div class="text-[10px] opacity-60">{{ branch.code }}</div>
              </div>
              <svg v-if="branch.id === branchStore.currentBranchId" class="w-4 h-4 ml-auto flex-shrink-0 text-vibe-purple" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="p-4 space-y-1 overflow-y-auto" style="max-height: calc(100vh - 260px);">
        <template v-for="item in navItems" :key="item.path || item.label">
          <!-- Submenu -->
          <div v-if="item.children">
            <button @click="toggleSubmenu(item.label)"
                    class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-all duration-150"
                    :class="isSubmenuActive(item) ? 'text-vibe-purple font-medium' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'">
              <span v-html="item.icon" class="w-5 h-5 flex-shrink-0"></span>
              <span class="flex-1">{{ item.label }}</span>
              <svg class="w-4 h-4 transition-transform" :class="expandedMenus[item.label] ? 'rotate-90' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <div v-show="expandedMenus[item.label]" class="ml-4 space-y-1 border-l border-gray-200 dark:border-gray-700 pl-3">
              <button v-for="child in item.children" :key="child.path" @click="navigateTo(child.path)"
                      class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left transition-all duration-150"
                      :class="isActive(child.path) ? 'bg-vibe-purple/10 text-vibe-purple font-medium' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'">
                <span>{{ child.label }}</span>
              </button>
            </div>
          </div>

          <!-- Regular nav item -->
          <button v-else @click="navigateTo(item.path)"
                  class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-all duration-150"
                  :class="isActive(item.path) ? 'bg-vibe-purple/10 text-vibe-purple font-medium' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'">
            <span v-html="item.icon" class="w-5 h-5 flex-shrink-0"></span>
            <span>{{ item.label }}</span>
          </button>
        </template>
      </nav>

      <!-- User -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-vibe-purple to-vibe-cyan flex items-center justify-center text-white text-xs font-bold">
            {{ authStore.userName?.charAt(0) || 'U' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ authStore.userName }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 capitalize">{{ authStore.user?.role }}</p>
          </div>
          <button @click="authStore.logout()" class="text-gray-400 hover:text-red-500 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Overlay for mobile sidebar -->
    <div v-if="sidebarOpen" @click="sidebarOpen = false" class="fixed inset-0 z-20 bg-black/50 lg:hidden"></div>

    <!-- Main -->
    <div class="lg:pl-64">
      <!-- Top bar -->
      <header class="sticky top-0 z-10 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between px-4 py-3 lg:px-6">
          <div class="flex items-center gap-3">
            <button @click="sidebarOpen = !sidebarOpen" class="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
              <svg class="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 class="text-lg font-semibold text-gray-900 dark:text-white">{{ pageTitle }}</h1>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentDate }}</p>
            </div>
          </div>
          <slot name="header-actions"></slot>
        </div>
      </header>

      <!-- Page content -->
      <main class="p-4 lg:p-6 space-y-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import logoIcon from '@/assets/logo-icon.png'
import { useAuthStore } from '@/stores/auth'
import { useBranchStore } from '@/stores/branchStore'

const props = defineProps<{ title?: string }>()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const branchStore = useBranchStore()
const sidebarOpen = ref(false)
const branchDropdownOpen = ref(false)
const expandedMenus = reactive<Record<string, boolean>>({ 
  'Food Stock': true, 
  'Finance': true, 
  'Staff': false, 
  'Consoles': false 
})

const pageTitle = computed(() => props.title || (route.meta.title as string) || 'Dashboard')

const currentDate = computed(() => {
  return new Date().toLocaleDateString('my-MM', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
})

function selectBranch(id: number) {
  branchStore.setBranch(id)
  branchDropdownOpen.value = false
  window.location.reload()
}

function closeDropdown(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.relative')) {
    branchDropdownOpen.value = false
  }
}

onMounted(() => {
  branchStore.fetchBranches()
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

const navItems = [
  { path: '/', label: 'Dashboard', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>' },
  { path: '/bookings', label: 'Bookings', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>' },
  { path: '/members', label: 'Members', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>' },
  { path: '/sales-daily', label: 'Sales Daily', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>' },
  { path: '/games', label: 'Games', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
  {
    label: 'Consoles',
    icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>',
    children: [
      { path: '/consoles/manage', label: 'Console Management' },
    ],
  },
  { path: '/topups', label: 'TopUp Logs', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>' },
  { path: '/opex', label: 'OPEX', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>' },
  {
    label: 'Staff',
    icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>',
    children: [
      { path: '/staff', label: 'Staff Management' },
      { path: '/staff-attendance', label: 'Attendance' },
      { path: '/staff-salary', label: 'Salary' },
    ],
  },
  {
    label: 'Loyalty',
    icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    children: [
      { path: '/loyalty', label: 'Overview' },
      { path: '/loyalty/members', label: 'Members' },
      { path: '/loyalty/rewards', label: 'Rewards' },
      { path: '/loyalty/redemptions', label: 'Redemptions' },
      { path: '/loyalty/settings', label: 'Settings' },
    ],
  },
  {
    label: 'Food & Inventory',
    icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>',
    children: [
      { path: '/food-menu', label: 'Menu Register' },
      { path: '/stock-in', label: 'Stock In' },
      { path: '/stock-out', label: 'Stock Out' },
      { path: '/inventory', label: 'Inventory' },
    ],
  },
  { path: '/promotions', label: 'Promotions', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>' },
  { path: '/coupons', label: 'Coupons', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>' },
  {
    label: 'Finance',
    icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    children: [
      { path: '/finance-dashboard', label: 'Financial Dashboard' },
      { path: '/finance', label: 'Web Finance' },
      { path: '/pnl', label: 'P&L' },
      { path: '/balance-sheet', label: 'Balance Sheet' },
      { path: '/cashflow', label: 'Cash Flow' },
      { path: '/profit-distribution', label: 'Profit Distribution' },
      { path: '/dividends', label: 'Dividends' },
      { path: '/capital-movements', label: 'Capital Movements' },
      { path: '/shareholders', label: 'Shareholders' },
    ],
  },
  { path: '/financial-report', label: 'Old Reports', icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function isSubmenuActive(item: any) {
  return item.children?.some((c: any) => isActive(c.path))
}

function toggleSubmenu(label: string) {
  expandedMenus[label] = !expandedMenus[label]
}

function navigateTo(path: string) {
  router.push(path)
  sidebarOpen.value = false
}
</script>
