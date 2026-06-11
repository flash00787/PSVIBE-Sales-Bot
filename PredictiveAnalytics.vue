<template>
  <AppLayout title="Predictive Analytics">
    <!-- Header Actions -->
    <template #header-actions>
      <div class="flex items-center gap-3">
        <button @click="refreshData" :disabled="loading"
                class="btn-outline text-sm flex items-center gap-1.5 px-3 py-2">
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>
    </template>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-vibe-purple"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <p class="text-red-700 dark:text-red-400 text-sm">{{ error }}</p>
      <button @click="refreshData" class="mt-2 text-sm text-vibe-purple hover:underline">Try again</button>
    </div>

    <template v-else>
      <!-- Forecast Card -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card p-5 bg-gradient-to-br from-vibe-purple to-purple-700 text-white">
          <p class="text-sm text-purple-200">📈 Daily Revenue Forecast</p>
          <p class="text-3xl font-bold mt-2">Ks {{ formatNumber(forecast.daily_forecast || 0) }}</p>
          <p class="text-xs text-purple-200 mt-1">Based on 7-day moving average</p>
        </div>
        <div class="card p-5 bg-gradient-to-br from-vibe-cyan to-teal-600 text-white">
          <p class="text-sm text-teal-200">💰 Projected 7-Day Revenue</p>
          <p class="text-3xl font-bold mt-2">Ks {{ formatNumber(forecast.projected_7day || 0) }}</p>
          <p class="text-xs text-teal-200 mt-1">Forecast for the next week</p>
        </div>
        <div class="card p-5 bg-gradient-to-br from-amber-500 to-orange-600 text-white">
          <p class="text-sm text-amber-200">📊 Month-over-Month</p>
          <p class="text-3xl font-bold mt-2" :class="forecast.trend_pct >= 0 ? '' : 'text-red-200'">
            {{ forecast.trend_pct >= 0 ? '+' : '' }}{{ forecast.trend_pct }}%
          </p>
          <p class="text-xs text-amber-200 mt-1">vs previous month</p>
        </div>
      </div>

      <!-- Sales Trend Chart -->
      <div class="card p-5">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">📊 Sales Trend (Last 30 Days)</h2>
        <div v-if="salesTrend.length === 0" class="text-center py-8 text-gray-400 text-sm">No sales data yet</div>
        <div v-else>
          <div class="relative" style="height: 280px;">
            <svg viewBox="0 0 900 280" class="w-full h-full" preserveAspectRatio="none">
              <!-- Grid lines -->
              <line v-for="i in 5" :key="'grid-'+i" :x1="0" :y1="i*56" :x2="900" :y2="i*56"
                    stroke="currentColor" class="text-gray-200 dark:text-gray-700" stroke-width="0.5" />
              <!-- Bars -->
              <rect v-for="(d, i) in salesTrend" :key="'bar-'+i"
                    :x="i * (900 / salesTrend.length) + 3" :y="280 - barHeight(d.total)"
                    :width="Math.max(900 / salesTrend.length - 6, 2)" :height="barHeight(d.total)"
                    rx="2" fill="url(#barGradient)" opacity="0.9">
                <title>{{ d.day }}: Ks {{ formatNumber(d.total) }}</title>
              </rect>
              <!-- Line overlay -->
              <polyline :points="linePoints" fill="none" stroke="#a855f7" stroke-width="2" />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#a855f7" />
                  <stop offset="100%" stop-color="#7c3aed" stop-opacity="0.5" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div class="flex justify-between mt-2 text-xs text-gray-400">
            <span>{{ salesTrend[0]?.day || '' }}</span>
            <span>{{ salesTrend[salesTrend.length-1]?.day || '' }}</span>
          </div>
        </div>
      </div>

      <!-- Two-Column: Peak Hours + Popular Games -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Peak Hours -->
        <div class="card p-5">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">⏰ Peak Hours</h2>
          <div v-if="peakHours.length === 0" class="text-center py-8 text-gray-400 text-sm">No booking data yet</div>
          <div v-else class="space-y-2">
            <div v-for="(h, i) in peakHours" :key="'peak-'+i"
                 class="flex items-center gap-3">
              <span class="text-sm font-mono text-gray-600 dark:text-gray-400 w-14">{{ h.hour_label }}</span>
              <div class="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                     :class="i < 3 ? 'bg-gradient-to-r from-vibe-purple to-purple-500' : 'bg-gradient-to-r from-vibe-cyan to-teal-400'"
                     :style="{ width: barPct(h.bookings) + '%' }"></div>
              </div>
              <span class="text-sm font-semibold text-gray-700 dark:text-gray-300 w-12 text-right">{{ h.bookings }}</span>
            </div>
          </div>
        </div>

        <!-- Popular Games -->
        <div class="card p-5">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">🎮 Popular Games</h2>
          <div v-if="popularGames.length === 0" class="text-center py-8 text-gray-400 text-sm">No game data yet</div>
          <div v-else class="space-y-2">
            <div v-for="(g, i) in popularGames" :key="'game-'+i"
                 class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                    :class="i < 3 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                {{ i + 1 }}
              </span>
              <span class="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">{{ g.game_title }}</span>
              <span class="text-sm font-semibold text-gray-500 dark:text-gray-400">
                {{ g.times_played }} plays
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Member Growth Chart -->
      <div class="card p-5">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">👥 Member Growth (Last 30 Days)</h2>
        <div v-if="memberGrowth.length === 0" class="text-center py-8 text-gray-400 text-sm">No member data yet</div>
        <div v-else>
          <div class="relative" style="height: 220px;">
            <svg viewBox="0 0 900 220" class="w-full h-full" preserveAspectRatio="none">
              <line v-for="i in 5" :key="'mg-'+i" :x1="0" :y1="i*44" :x2="900" :y2="i*44"
                    stroke="currentColor" class="text-gray-200 dark:text-gray-700" stroke-width="0.5" />
              <polyline :points="memberLinePoints" fill="none" stroke="#06b6d4" stroke-width="2.5"
                        vector-effect="non-scaling-stroke" />
              <!-- Dots -->
              <circle v-for="(d, i) in memberGrowth" :key="'mdot-'+i"
                      :cx="i * (900 / Math.max(memberGrowth.length - 1, 1))"
                      :cy="220 - memberDotY(d.new_members)"
                      r="3" fill="#06b6d4" stroke="white" stroke-width="1.5">
                <title>{{ d.day }}: {{ d.new_members }} members</title>
              </circle>
              <!-- Area fill -->
              <polygon :points="memberAreaPoints" fill="#06b6d4" opacity="0.1" />
            </svg>
          </div>
          <p class="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">
            Total Members: <span class="font-bold text-vibe-purple">{{ totalMembers }}</span>
          </p>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'

interface SalesDay { day: string; total: number; count: number }
interface PeakHour { hour: number; hour_label: string; bookings: number }
interface Game { game_title: string; times_played: number }
interface MemberDay { day: string; new_members: number }
interface Forecast { daily_forecast: number; projected_7day: number; trend_pct: number; current_month_total: number; last_month_total: number }

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const loading = ref(true)
const error = ref<string | null>(null)

const salesTrend = ref<SalesDay[]>([])
const peakHours = ref<PeakHour[]>([])
const popularGames = ref<Game[]>([])
const memberGrowth = ref<MemberDay[]>([])
const totalMembers = ref(0)
const forecast = ref<Forecast>({ daily_forecast: 0, projected_7day: 0, trend_pct: 0, current_month_total: 0, last_month_total: 0 })

function formatNumber(n: number): string {
  return n.toLocaleString('en-US')
}

function barHeight(val: number): number {
  const maxVal = Math.max(...salesTrend.value.map(d => d.total), 1)
  return Math.max((val / maxVal) * 260, 1)
}

function barPct(val: number): number {
  const maxVal = Math.max(...peakHours.value.map(h => h.bookings), 1)
  return (val / maxVal) * 100
}

const linePoints = computed(() => {
  if (!salesTrend.value.length) return ''
  const maxVal = Math.max(...salesTrend.value.map(d => d.total), 1)
  const w = 900
  const h = 280
  return salesTrend.value.map((d, i) => {
    const x = i * (w / (salesTrend.value.length - 1 || 1))
    const y = h - ((d.total / maxVal) * 260)
    return `${x},${y}`
  }).join(' ')
})

function memberDotY(val: number): number {
  const maxVal = Math.max(...memberGrowth.value.map(d => d.new_members), 1)
  return Math.max((val / maxVal) * 200, 1)
}

const memberLinePoints = computed(() => {
  if (!memberGrowth.value.length) return ''
  const w = 900; const h = 220
  return memberGrowth.value.map((d, i) => {
    const x = i * (w / Math.max(memberGrowth.value.length - 1, 1))
    const y = h - memberDotY(d.new_members)
    return `${x},${y}`
  }).join(' ')
})

const memberAreaPoints = computed(() => {
  if (!memberGrowth.value.length) return ''
  const w = 900; const h = 220
  const pts = memberGrowth.value.map((d, i) => {
    const x = i * (w / Math.max(memberGrowth.value.length - 1, 1))
    const y = h - memberDotY(d.new_members)
    return `${x},${y}`
  })
  return `${pts[0]?.split(',')[0] || 0},220 ${pts.join(' ')} ${pts[pts.length-1]?.split(',')[0] || w},220`
})

async function refreshData() {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('access_token')
    const headers: HeadersInit = token ? { 'Authorization': `Bearer ${token}` } : {}

    const res = await fetch(`${API_BASE}/dashboard/analytics/summary`, { headers })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Failed to load analytics')

    const data = json.data
    salesTrend.value = data.sales_trend || []
    peakHours.value = data.peak_hours || []
    popularGames.value = data.popular_games || []
    memberGrowth.value = data.member_growth || []
    totalMembers.value = data.total_members || 0
    forecast.value = {
      daily_forecast: data.forecast?.daily_forecast || 0,
      projected_7day: data.forecast?.projected_7day || 0,
      trend_pct: data.forecast?.trend_pct || 0,
      current_month_total: data.forecast?.current_month_total || 0,
      last_month_total: data.forecast?.last_month_total || 0
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to load analytics data'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.card {
  @apply bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm;
}
.btn-outline {
  @apply border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}
</style>
