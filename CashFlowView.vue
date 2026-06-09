<template>
  <AppLayout>
    <div class="p-4 lg:p-6">
      <!-- Header -->
      <div class="mb-6 flex flex-wrap items-center gap-4">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex-1">&#x1f4b5; Cash Flow Statement</h1>
        <div class="flex gap-2">
          <select v-model="year" class="px-3 py-2 rounded-lg border dark:bg-gray-800 dark:border-gray-700 dark:text-white text-sm">
            <option v-for="y in [2025,2026,2027]" :key="y" :value="y">{{ y }}</option>
          </select>
          <select v-model="month" class="px-3 py-2 rounded-lg border dark:bg-gray-800 dark:border-gray-700 dark:text-white text-sm">
            <option v-for="m in 12" :key="m" :value="m">{{ m.toString().padStart(2,'0') }}</option>
          </select>
          <button @click="fetchData" :disabled="loading" class="px-4 py-2 bg-vibe-purple hover:bg-vibe-purple/90 text-white rounded-lg text-sm disabled:opacity-50">{{ loading ? 'Loading...' : 'Load' }}</button>
        </div>
      </div>
      <!-- Error -->
      <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-xl text-red-600 text-sm">&#x26a0;&#xfe0f; {{ error }}</div>
      <div v-if="data" class="space-y-4">
        <!-- Opening Balance Banner -->
        <div class="bg-gradient-to-r from-vibe-purple/10 to-vibe-cyan/10 dark:from-vibe-purple/5 dark:to-vibe-cyan/5 rounded-xl p-5 border border-vibe-purple/20 text-center">
          <p class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Opening Balance</p>
          <p class="text-3xl font-extrabold text-vibe-purple">{{ fmt(data.opening_balance) }} Ks</p>
          <p class="text-xs text-gray-400 mt-1">As of {{ data.period }}-01</p>
        </div>
        <!-- Sections -->
        <template v-for="(section, key) in data.sections" :key="key">
          <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">{{ section.title }}</h2>
            <div class="w-full text-sm">
              <div v-for="item in section.items" :key="item.label" class="flex justify-between py-2.5 border-b border-gray-100 dark:border-gray-700/30">
                <span class="text-gray-800 dark:text-gray-200">
                  <span v-if="item.emoji">{{ item.emoji }}</span> {{ item.label }}
                  <span v-if="item.type === 'adjustment'" class="text-[10px] text-yellow-600 dark:text-yellow-400 italic"> (non-cash)</span>
                </span>
                <span class="font-semibold" :class="itemColor(item.type)">{{ itemSign(item.type) }}{{ fmt(item.amount) }}</span>
              </div>
              <div class="flex justify-between pt-3 mt-1 border-t-2 border-gray-300 dark:border-gray-600">
                <span class="font-bold text-gray-900 dark:text-white">Subtotal</span>
                <span class="font-bold" :class="section.subtotal >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ fmt(section.subtotal) }}</span>
              </div>
            </div>
          </div>
        </template>
        <!-- Net Change -->
        <div class="rounded-xl p-5 shadow-sm border-2 transition-colors" :class="data.summary.net_change >= 0 ? 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-400' : 'bg-red-50 dark:bg-red-900/10 border-red-400'">
          <div class="flex justify-between items-center">
            <div>
              <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ data.period }} — Net Cash Flow</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                &#x2795; Inflows: {{ fmt(data.summary.total_inflows) }} Ks &nbsp;|&nbsp; &#x2796; Outflows: {{ fmt(data.summary.total_outflows) }} Ks
              </p>
            </div>
            <p class="text-2xl font-extrabold" :class="data.summary.net_change >= 0 ? 'text-emerald-500' : 'text-red-500'">
              {{ data.summary.net_change >= 0 ? '+' : '' }}{{ fmt(data.summary.net_change) }} Ks
            </p>
          </div>
        </div>
        <!-- Closing Balance -->
        <div class="bg-gradient-to-r from-vibe-cyan/10 to-emerald-500/10 dark:from-vibe-cyan/5 dark:to-emerald-500/5 rounded-xl p-5 border border-emerald-400/30 text-center">
          <p class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Closing Balance</p>
          <p class="text-3xl font-extrabold" :class="data.summary.closing_balance >= 0 ? 'text-emerald-500' : 'text-red-500'">
            {{ fmt(data.summary.closing_balance) }} Ks
          </p>
          <p class="text-xs text-gray-400 mt-1">As of {{ data.period }} end</p>
        </div>
        <!-- Reconciliation -->
        <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">Reconciliation</p>
          <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
            <div class="flex justify-between"><span>Opening Balance</span><span class="font-medium">{{ fmt(data.summary.opening_balance) }} Ks</span></div>
            <div class="flex justify-between"><span>&#x2795; Total Inflows</span><span class="font-medium text-emerald-500">+{{ fmt(data.summary.total_inflows) }} Ks</span></div>
            <div class="flex justify-between"><span>&#x2796; Total Outflows</span><span class="font-medium text-red-500">-{{ fmt(data.summary.total_outflows) }} Ks</span></div>
            <div class="flex justify-between pt-1 border-t border-gray-300 dark:border-gray-600"><span class="font-semibold text-gray-700 dark:text-gray-300">Net Change</span><span class="font-semibold" :class="data.summary.net_change >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ data.summary.net_change >= 0 ? '+' : '' }}{{ fmt(data.summary.net_change) }} Ks</span></div>
            <div class="flex justify-between pt-1 border-t-2 border-vibe-purple/40"><span class="font-bold text-gray-800 dark:text-gray-200">Closing Balance</span><span class="font-bold" :class="data.summary.closing_balance >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ fmt(data.summary.closing_balance) }} Ks</span></div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const year = ref(2026)
const month = ref(6)
const loading = ref(false)
const error = ref('')
const data = ref<any>(null)

function fmt(n: number): string {
  return Number(n || 0).toLocaleString('en-US')
}

function itemSign(type: string): string {
  if (type === 'inflow') return '+'
  if (type === 'outflow') return '-'
  return ''
}

function itemColor(type: string): string {
  if (type === 'inflow') return 'text-emerald-500'
  if (type === 'outflow') return 'text-red-500'
  return 'text-yellow-600 dark:text-yellow-400'
}

async function fetchData() {
  loading.value = true; error.value = ''
  try {
    const res = await apiClient.get('/api/dashboard/financial/cashflow', { params: { year: year.value, month: month.value } })
    if (res.data.success) data.value = res.data.data
    else error.value = res.data.error || 'Failed'
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message
  } finally { loading.value = false }
}

onMounted(fetchData)
</script>
