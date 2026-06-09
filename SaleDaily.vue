<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterDate = ref('')
const total = ref(0)
const summary = ref<any>(null)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { limit: 100 }
    if (search.value) params.search = search.value
    if (filterDate.value) params.date = filterDate.value
    const res = await apiClient.get('/api/dashboard/sales-daily', { params })
    items.value = res.data.data || []
    total.value = res.data.total || 0
    summary.value = res.data.summary || null
  } catch { items.value = []; summary.value = null }
  finally { loading.value = false }
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDateTime(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    paid: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

onMounted(fetchData)
</script>

<template>
  <AppLayout title="Sales Daily">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">💰 Sales Daily Records</h1>
    </div>

    <!-- Summary Cards -->
    <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Gross</p>
        <p class="text-2xl font-bold text-indigo-600 mt-1">{{ summary.total_gross.toLocaleString() }} Ks</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Discount</p>
        <p class="text-2xl font-bold text-orange-600 mt-1">{{ summary.total_discount.toLocaleString() }} Ks</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Net</p>
        <p class="text-2xl font-bold text-green-600 mt-1">{{ summary.total_net.toLocaleString() }} Ks</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Amount</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ summary.total_amount.toLocaleString() }} Ks</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search by voucher, member, staff..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <input v-model="filterDate" @change="fetchData" type="date"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <button @click="filterDate = ''; search = ''; fetchData()" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Clear</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Voucher</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Console</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Member</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Gross</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Discount</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Net</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Staff</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Payment</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">{{ item.voucher_no || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(item.sale_date) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.console_id || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.member_id || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ Number(item.gross).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-right text-orange-600">{{ Number(item.discount).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-right font-medium text-green-600">{{ Number(item.net).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.staff_name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.payment_method || '-' }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="9" class="px-4 py-8 text-center text-gray-500">No sales records found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>
