import { Client } from 'ssh2';
import { readFileSync } from 'fs';

const conn = new Client();
const PRIVATE_KEY = readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function exec(conn, cmd, opts = {}) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, opts, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => errOut += d.toString());
      stream.on('close', code => {
        if (code !== 0) reject(new Error(`Exit ${code}: ${errOut || out}`));
        else resolve(out);
      });
    });
  });
}

function sftpWrite(conn, remotePath, content) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      const stream = sftp.createWriteStream(remotePath);
      stream.on('error', reject);
      stream.on('close', resolve);
      stream.end(content);
    });
  });
}

// ============ FILES TO CREATE ============

const ROUTER_CONTENT = `import { createRouter, createWebHashHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, title: 'Dashboard' },
    },
    {
      path: '/bookings',
      name: 'bookings',
      component: () => import('../views/BookingsManagement.vue'),
      meta: { requiresAuth: true, title: 'Bookings' },
    },
    {
      path: '/members',
      name: 'members',
      component: () => import('../views/MembersManagement.vue'),
      meta: { requiresAuth: true, title: 'Members' },
    },
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('../views/FoodStock.vue'),
      meta: { requiresAuth: true, title: 'Food Stock' },
    },
    {
      path: '/promotions',
      name: 'promotions',
      component: () => import('../views/Promotions.vue'),
      meta: { requiresAuth: true, title: 'Promotions' },
    },
    {
      path: '/games',
      name: 'games',
      component: () => import('../views/GamesLibrary.vue'),
      meta: { requiresAuth: true, title: 'Games' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
`;

const DASHBOARD_VIEW_CONTENT = `<template>
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

      <!-- Nav -->
      <nav class="p-4 space-y-1 overflow-y-auto" style="max-height: calc(100vh - 200px);">
        <button @click="navigateTo('/')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-vibe-purple/10 text-vibe-purple font-medium text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>Dashboard</span>
        </button>
        <button @click="navigateTo('/bookings')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>Bookings</span>
        </button>
        <button @click="navigateTo('/members')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span>Members</span>
        </button>
        <button @click="navigateTo('/inventory')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <span>Food Stock</span>
        </button>
        <button @click="navigateTo('/promotions')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          <span>Promotions</span>
        </button>
        <button @click="navigateTo('/games')" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-left">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Games</span>
        </button>
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
              <h1 class="text-lg font-semibold text-gray-900 dark:text-white">{{ currentTitle }}</h1>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentDate }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button @click="refreshData" :disabled="dashboardStore.loading"
                    class="btn-outline text-sm flex items-center gap-1.5 px-3 py-2">
              <svg class="w-4 h-4" :class="{ 'animate-spin': dashboardStore.loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="p-4 lg:p-6 space-y-6">
        <!-- Error -->
        <ErrorAlert :message="dashboardStore.error" @dismiss="dashboardStore.error = null" />

        <!-- Loading -->
        <LoadingSpinner v-if="dashboardStore.loading && !dashboardStore.lastRefresh" />

        <template v-else>
          <!-- Stats Cards -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard label="Bookings Today" :value="dashboardStore.stats.today_bookings" icon="bookings" />
            <StatsCard label="Active Players" :value="dashboardStore.stats.active_players" icon="players" />
            <StatsCard label="Revenue Today" :value="dashboardStore.stats.today_revenue" icon="revenue" />
            <StatsCard label="Total Members" :value="dashboardStore.stats.total_members" icon="members" />
          </div>

          <!-- Console Grid + Schedule -->
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <ConsoleGrid :consoles="dashboardStore.consoles" />
            <TodaySchedule :schedule="dashboardStore.schedule" />
          </div>

          <!-- Revenue Chart -->
          <div class="card p-5">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">📈 Revenue Trend (7 days)</h2>
            <div v-if="dashboardStore.revenueTrend.length === 0" class="text-center py-8 text-gray-400 text-sm">
              No revenue data yet
            </div>
            <div v-else class="relative h-64">
              <canvas ref="chartCanvas"></canvas>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import logoIcon from '@/assets/logo-icon.png'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import ConsoleGrid from '@/components/dashboard/ConsoleGrid.vue'
import TodaySchedule from '@/components/dashboard/TodaySchedule.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const sidebarOpen = ref(false)
const chartCanvas = ref<HTMLCanvasElement | null>(null)

const currentDate = computed(() => {
  return new Date().toLocaleDateString('my-MM', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
})

const currentTitle = computed(() => {
  return (route.meta.title as string) || 'Dashboard'
})

function navigateTo(path: string) {
  router.push(path)
  sidebarOpen.value = false
}

let chartInstance: any = null

async function initChart() {
  if (!chartCanvas.value || dashboardStore.revenueTrend.length === 0) return

  const { Chart, registerables } = await import('chart.js')
  Chart.register(...registerables)

  if (chartInstance) chartInstance.destroy()

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  const labels = dashboardStore.revenueTrend.map(p => {
    const d = new Date(p.date + 'T00:00:00')
    return d.toLocaleDateString('en', { month: 'short', day: 'numeric' })
  })
  const data = dashboardStore.revenueTrend.map(p => p.revenue)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Revenue (Ks)',
        data,
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#8B5CF6',
        pointRadius: 4,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (val: any) => val.toLocaleString() + ' Ks'
          },
          grid: {
            color: 'rgba(156, 163, 175, 0.1)'
          }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  })
}

async function refreshData() {
  await dashboardStore.fetchAll()
  await initChart()
}

onMounted(async () => {
  await dashboardStore.fetchAll()
  setTimeout(() => initChart(), 100)
})
</script>

<style scoped>
.btn-outline {
  @apply border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}
</style>
`;

// BOOKINGS MANAGEMENT
const BOOKINGS_CONTENT = `<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const statusFilter = ref('')
const total = ref(0)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref({ status: '', notes: '' })

async function fetchData() {
  loading.value = true
  try {
    const params: any = { search: search.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await axios.get('/api/dashboard/bookings', { params })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch { items.value = [] }
  finally { loading.value = false }
}

function openEdit(item: any) {
  editing.value = item
  form.value = { status: item.status || '', notes: item.notes || '' }
  showModal.value = true
}

async function saveItem() {
  if (!editing.value) return
  loading.value = true
  try {
    await axios.put(\`/api/dashboard/bookings/\${editing.value.id}\`, form.value)
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Save failed')
  }
  finally { loading.value = false }
}

async function deleteItem(id: string) {
  if (!confirm('Delete this booking?')) return
  try {
    await axios.delete(\`/api/dashboard/bookings/\${id}\`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    confirmed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    done: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

function formatDateTime(val: string) {
  if (!val) return ''
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Bookings Management</h1>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search by member, console, or phone..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <select v-model="statusFilter" @change="fetchData"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
        <option value="">All Statuses</option>
        <option value="confirmed">Confirmed</option>
        <option value="pending">Pending</option>
        <option value="cancelled">Cancelled</option>
        <option value="done">Done</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Console</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Member</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Duration</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Staff</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">#{{ item.id }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.console_name || item.console || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.member_name || item.member || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDateTime(item.booking_date || item.date) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.start_time || item.time || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.duration ? item.duration + ' min' : '-' }}</td>
              <td class="px-4 py-3 text-sm">
                <span :class="statusBadge(item.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.staff_name || item.staff || '-' }}</td>
              <td class="px-4 py-3 text-right text-sm">
                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>
                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="9" class="px-4 py-8 text-center text-gray-500">No bookings found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Booking' : 'Add Booking' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select v-model="form.status"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select status</option>
              <option value="confirmed">Confirmed</option>
              <option value="pending">Pending</option>
              <option value="cancelled">Cancelled</option>
              <option value="done">Done</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
            <textarea v-model="form.notes" rows="3"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Add notes..."></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
`;

// MEMBERS MANAGEMENT
const MEMBERS_CONTENT = `<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const total = ref(0)
const showModal = ref(false)
const showDetail = ref(false)
const editing = ref<any>(null)
const selectedMember = ref<any>(null)
const form = ref({ name: '', phone: '', tier: '' })

async function fetchData() {
  loading.value = true
  try {
    const res = await axios.get('/api/dashboard/members', { params: { search: search.value } })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch { items.value = [] }
  finally { loading.value = false }
}

function openDetail(member: any) {
  selectedMember.value = member
  showDetail.value = true
}

function openEdit(member: any) {
  editing.value = member
  form.value = { name: member.name || '', phone: member.phone || '', tier: member.tier || '' }
  showModal.value = true
}

async function saveItem() {
  if (!editing.value) return
  loading.value = true
  try {
    await axios.put(\`/api/dashboard/members/\${editing.value.id}\`, form.value)
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Save failed')
  }
  finally { loading.value = false }
}

async function deleteItem(id: string) {
  if (!confirm('Delete this member?')) return
  try {
    await axios.delete(\`/api/dashboard/members/\${id}\`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function tierBadge(tier: string) {
  const map: Record<string, string> = {
    platinum: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    gold: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    silver: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    bronze: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  }
  return map[tier?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Members Management</h1>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search by name or phone..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Member ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Phone</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Balance Mins</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tier</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Spend</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Join Date</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" @click="openDetail(item)" class="hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer">
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white font-mono">{{ item.member_id || item.id }}</td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white font-medium">{{ item.name }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.phone || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.balance_minutes || item.balance_mins || 0 }}</td>
              <td class="px-4 py-3 text-sm">
                <span :class="tierBadge(item.tier)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">
                  {{ item.tier || 'Regular' }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.total_spend ? Number(item.total_spend).toLocaleString() + ' Ks' : '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(item.join_date || item.created_at) }}</td>
              <td class="px-4 py-3 text-right text-sm" @click.stop>
                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>
                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="8" class="px-4 py-8 text-center text-gray-500">No members found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetail" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showDetail=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedMember?.name }}</h2>
          <button @click="showDetail=false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="space-y-3">
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Member ID</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ selectedMember?.member_id || selectedMember?.id }}</span>
          </div>
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Phone</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ selectedMember?.phone || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Tier</span>
            <span :class="tierBadge(selectedMember?.tier)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ selectedMember?.tier || 'Regular' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Balance Minutes</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ selectedMember?.balance_minutes || selectedMember?.balance_mins || 0 }}</span>
          </div>
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Total Spend</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ selectedMember?.total_spend ? Number(selectedMember.total_spend).toLocaleString() + ' Ks' : '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b dark:border-gray-700">
            <span class="text-gray-500 dark:text-gray-400">Join Date</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ formatDate(selectedMember?.join_date || selectedMember?.created_at) }}</span>
          </div>
        </div>
        <div v-if="selectedMember?.recent_activity" class="mt-6">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Recent Activity</h3>
          <div v-for="(act, i) in selectedMember.recent_activity" :key="i" class="py-2 border-b dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
            {{ act }}
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Member' : 'Add Member' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <input v-model="form.name"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
            <input v-model="form.phone"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tier</label>
            <select v-model="form.tier"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select tier</option>
              <option value="platinum">Platinum</option>
              <option value="gold">Gold</option>
              <option value="silver">Silver</option>
              <option value="bronze">Bronze</option>
              <option value="regular">Regular</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
`;

// FOOD STOCK
const FOOD_STOCK_CONTENT = `<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const categoryFilter = ref('')
const total = ref(0)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref({ item_name: '', category: '', quantity: 0, unit_price: 0, reorder_level: 0 })

const categories = ['Beverages', 'Snacks', 'Instant Noodles', 'Candy', 'Other']

async function fetchData() {
  loading.value = true
  try {
    const params: any = { search: search.value }
    if (categoryFilter.value) params.category = categoryFilter.value
    const res = await axios.get('/api/dashboard/inventory', { params })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch { items.value = [] }
  finally { loading.value = false }
}

function isLowStock(item: any) {
  return item.quantity <= item.reorder_level
}

function openCreate() {
  editing.value = null
  form.value = { item_name: '', category: '', quantity: 0, unit_price: 0, reorder_level: 0 }
  showModal.value = true
}

function openEdit(item: any) {
  editing.value = item
  form.value = {
    item_name: item.item_name || '',
    category: item.category || '',
    quantity: item.quantity || 0,
    unit_price: item.unit_price || 0,
    reorder_level: item.reorder_level || 0,
  }
  showModal.value = true
}

async function saveItem() {
  loading.value = true
  try {
    if (editing.value) {
      await axios.put(\`/api/dashboard/inventory/\${editing.value.id}\`, form.value)
    } else {
      await axios.post('/api/dashboard/inventory', form.value)
    }
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Save failed')
  }
  finally { loading.value = false }
}

async function deleteItem(id: string) {
  if (!confirm('Are you sure you want to delete this item?')) return
  try {
    await axios.delete(\`/api/dashboard/inventory/\${id}\`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Food Stock</h1>
      <button @click="openCreate" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors">
        + Add New
      </button>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search items..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <select v-model="categoryFilter" @change="fetchData"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
        <option value="">All Categories</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Item Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quantity</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Unit Price</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Reorder Level</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                {{ item.item_name }}
                <span v-if="isLowStock(item)" class="ml-2 px-1.5 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded-full">Low Stock</span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.category || '-' }}</td>
              <td class="px-4 py-3 text-sm" :class="isLowStock(item) ? 'text-red-600 dark:text-red-400 font-bold' : 'text-gray-700 dark:text-gray-300'">
                {{ item.quantity }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.unit_price ? Number(item.unit_price).toLocaleString() + ' Ks' : '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.reorder_level || 0 }}</td>
              <td class="px-4 py-3 text-right text-sm">
                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>
                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="6" class="px-4 py-8 text-center text-gray-500">No items found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Item' : 'Add New Item' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Item Name *</label>
            <input v-model="form.item_name" required
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
            <select v-model="form.category"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select category</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantity</label>
            <input v-model.number="form.quantity" type="number" min="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unit Price (Ks)</label>
            <input v-model.number="form.unit_price" type="number" min="0" step="0.01"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Reorder Level</label>
            <input v-model.number="form.reorder_level" type="number" min="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
`;

// PROMOTIONS
const PROMOTIONS_CONTENT = `<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const total = ref(0)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref({
  name: '',
  promo_type: 'discount',
  discount_type: 'percentage',
  discount_value: 0,
  start_date: '',
  end_date: '',
  status: 'active',
  notes: '',
})

const promoTypes = ['cashback_coupon', 'discount', 'bonus']

function statusBadge(status: string) {
  const map: Record<string, string> = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
    expired: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function fetchData() {
  loading.value = true
  try {
    const res = await axios.get('/api/dashboard/promotions', { params: { search: search.value } })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch { items.value = [] }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = {
    name: '',
    promo_type: 'discount',
    discount_type: 'percentage',
    discount_value: 0,
    start_date: '',
    end_date: '',
    status: 'active',
    notes: '',
  }
  showModal.value = true
}

function openEdit(item: any) {
  editing.value = item
  form.value = {
    name: item.name || '',
    promo_type: item.promo_type || 'discount',
    discount_type: item.discount_type || 'percentage',
    discount_value: item.discount_value || 0,
    start_date: item.start_date ? item.start_date.split('T')[0] : '',
    end_date: item.end_date ? item.end_date.split('T')[0] : '',
    status: item.status || 'active',
    notes: item.notes || '',
  }
  showModal.value = true
}

async function saveItem() {
  loading.value = true
  try {
    if (editing.value) {
      await axios.put(\`/api/dashboard/promotions/\${editing.value.id}\`, form.value)
    } else {
      await axios.post('/api/dashboard/promotions', form.value)
    }
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Save failed')
  }
  finally { loading.value = false }
}

async function toggleStatus(item: any) {
  const newStatus = item.status === 'active' ? 'inactive' : 'active'
  try {
    await axios.put(\`/api/dashboard/promotions/\${item.id}\`, { status: newStatus })
    item.status = newStatus
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Toggle failed')
  }
}

async function deleteItem(id: string) {
  if (!confirm('Delete this promotion?')) return
  try {
    await axios.delete(\`/api/dashboard/promotions/\${id}\`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Promotions</h1>
      <button @click="openCreate" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors">
        + Add New
      </button>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search promotions..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Discount</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Start Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">End Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ item.name }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 capitalize">{{ (item.promo_type || '').replace(/_/g, ' ') }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                {{ item.discount_type === 'percentage' ? item.discount_value + '%' : Number(item.discount_value).toLocaleString() + ' Ks' }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(item.start_date) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(item.end_date) }}</td>
              <td class="px-4 py-3 text-sm">
                <span :class="statusBadge(item.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">
                  {{ item.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-right text-sm">
                <button @click="toggleStatus(item)" class="text-yellow-600 hover:text-yellow-800 dark:text-yellow-400 dark:hover:text-yellow-300 mr-3 transition-colors">
                  {{ item.status === 'active' ? 'Deactivate' : 'Activate' }}
                </button>
                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>
                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-gray-500">No promotions found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Promotion' : 'Add New Promotion' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Promotion Name *</label>
            <input v-model="form.name"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
            <select v-model="form.promo_type"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="pt in promoTypes" :key="pt" :value="pt">{{ pt.replace(/_/g, ' ') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Discount Type</label>
            <select v-model="form.discount_type"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed Amount (Ks)</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Discount Value</label>
            <input v-model.number="form.discount_value" type="number" min="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input v-model="form.start_date" type="date"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
              <input v-model="form.end_date" type="date"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select v-model="form.status"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
            <textarea v-model="form.notes" rows="2"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Optional notes..."></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
`;

// GAMES LIBRARY
const GAMES_CONTENT = `<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const genreFilter = ref('')
const total = ref(0)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref({ game_title: '', genre: '', solo_multi: '', disc_count: 0, final_status: '' })

const genres = ['Action', 'Adventure', 'RPG', 'Sports', 'Racing', 'Fighting', 'Horror', 'Puzzle', 'Strategy', 'Shooter', 'Other']
const statuses = ['Available', 'Damaged', 'Lost', 'In Use']
const soloMultiOpts = ['Solo', 'Multi', 'Both']

async function fetchData() {
  loading.value = true
  try {
    const params: any = { search: search.value }
    if (genreFilter.value) params.genre = genreFilter.value
    const res = await axios.get('/api/dashboard/games', { params })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch { items.value = [] }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { game_title: '', genre: '', solo_multi: 'Solo', disc_count: 1, final_status: 'Available' }
  showModal.value = true
}

function openEdit(item: any) {
  editing.value = item
  form.value = {
    game_title: item.game_title || '',
    genre: item.genre || '',
    solo_multi: item.solo_multi || '',
    disc_count: item.disc_count || 0,
    final_status: item.final_status || '',
  }
  showModal.value = true
}

async function saveItem() {
  loading.value = true
  try {
    if (editing.value) {
      await axios.put(\`/api/dashboard/games/\${editing.value.id}\`, form.value)
    } else {
      await axios.post('/api/dashboard/games', form.value)
    }
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Save failed')
  }
  finally { loading.value = false }
}

async function deleteItem(id: string) {
  if (!confirm('Delete this game?')) return
  try {
    await axios.delete(\`/api/dashboard/games/\${id}\`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.message || 'Delete failed')
  }
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    available: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    damaged: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    lost: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
    'in use': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Games Library</h1>
      <button @click="openCreate" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors">
        + Add New
      </button>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search by title or genre..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <select v-model="genreFilter" @change="fetchData"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
        <option value="">All Genres</option>
        <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Game Title</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Genre</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Solo/Multi</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Disc Count</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ item.game_title }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.genre || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.solo_multi || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.disc_count || 0 }}</td>
              <td class="px-4 py-3 text-sm">
                <span :class="statusBadge(item.final_status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">
                  {{ item.final_status || 'Unknown' }}
                </span>
              </td>
              <td class="px-4 py-3 text-right text-sm">
                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3 transition-colors">Edit</button>
                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="6" class="px-4 py-8 text-center text-gray-500">No games found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Game' : 'Add New Game' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Game Title *</label>
            <input v-model="form.game_title"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Genre</label>
            <select v-model="form.genre"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select genre</option>
              <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Solo / Multi</label>
            <select v-model="form.solo_multi"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select</option>
              <option v-for="sm in soloMultiOpts" :key="sm" :value="sm">{{ sm }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Disc Count</label>
            <input v-model.number="form.disc_count" type="number" min="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select v-model="form.final_status"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select status</option>
              <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
`;

conn.on('ready', async () => {
  try {
    console.log('[1/4] Writing 5 new page components...');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/BookingsManagement.vue', BOOKINGS_CONTENT);
    console.log('  ✓ BookingsManagement.vue');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/MembersManagement.vue', MEMBERS_CONTENT);
    console.log('  ✓ MembersManagement.vue');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/FoodStock.vue', FOOD_STOCK_CONTENT);
    console.log('  ✓ FoodStock.vue');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/Promotions.vue', PROMOTIONS_CONTENT);
    console.log('  ✓ Promotions.vue');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/GamesLibrary.vue', GAMES_CONTENT);
    console.log('  ✓ GamesLibrary.vue');

    console.log('[2/4] Writing router...');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/router/index.ts', ROUTER_CONTENT);
    console.log('  ✓ router/index.ts');

    console.log('[3/4] Writing DashboardView.vue...');
    await sftpWrite(conn, '/root/psvibe-dashboard/src/views/DashboardView.vue', DASHBOARD_VIEW_CONTENT);
    console.log('  ✓ DashboardView.vue');

    console.log('[4/4] Building...');
    const buildOut = await exec(conn, 'cd /root/psvibe-dashboard && npm run build 2>&1');
    console.log('Build output:', buildOut.slice(-500));

    console.log('Deploying...');
    await exec(conn, 'rm -rf /root/psvibe_api_server/dashboard-dist && cp -r /root/psvibe-dashboard/dist /root/psvibe_api_server/dashboard-dist');
    console.log('  ✓ Copied dist');

    await exec(conn, 'sudo systemctl restart psvibe-api');
    console.log('  ✓ Restarted psvibe-api');

    console.log('\n✅ ALL DONE — 5 pages created, router updated, sidebar updated, built & deployed');
    conn.end();
  } catch (e) {
    console.error('FAILED:', e.message);
    conn.end();
    process.exit(1);
  }
});

conn.on('error', (err) => { console.error('SSH error:', err.message); process.exit(1); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: PRIVATE_KEY,
  readyTimeout: 30000
});
