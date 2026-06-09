<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const loading = ref(false)
const report = ref<any>(null)
const activeTab = ref<'assets' | 'payables' | 'receivables' | 'advances' | 'prepaid'>('assets')

async function fetchReport() {
  loading.value = true
  try {
    const res = await apiClient.get('/api/dashboard/financial-report')
    report.value = res.data.data
  } catch (e: any) {
    report.value = null
  }
  finally { loading.value = false }
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    paid: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    settled: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    overdue: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  }
  return map[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

const tabs = [
  { key: 'assets', label: '🏢 Assets', totalKey: 'assets_total' },
  { key: 'payables', label: '📤 Payables', totalKey: 'payables_total' },
  { key: 'receivables', label: '📥 Receivables', totalKey: 'receivables_total' },
  { key: 'advances', label: '💸 Advances', totalKey: 'advances_total' },
  { key: 'prepaid', label: '📋 Prepaid', totalKey: 'prepaid_total' },
] as const

onMounted(fetchReport)
</script>

<template>
  <AppLayout title="Financial Report">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">📊 Financial Report</h1>
      <button @click="fetchReport" :disabled="loading"
        class="btn-outline text-sm flex items-center gap-1.5 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
        ↻ Refresh
      </button>
    </div>

    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>

    <template v-else-if="report">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 cursor-pointer" :class="{ 'ring-2 ring-indigo-500': activeTab === 'assets' }" @click="activeTab = 'assets'">
          <p class="text-xs text-gray-500 dark:text-gray-400 uppercase">Total Assets</p>
          <p class="text-2xl font-bold text-indigo-600 mt-1">{{ report.assets_total.toLocaleString() }} Ks</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 cursor-pointer" :class="{ 'ring-2 ring-indigo-500': activeTab === 'payables' }" @click="activeTab = 'payables'">
          <p class="text-xs text-gray-500 dark:text-gray-400 uppercase">Payables (Pending)</p>
          <p class="text-2xl font-bold text-orange-600 mt-1">{{ report.payables_pending.toLocaleString() }} Ks</p>
          <p class="text-xs text-gray-400 mt-1">Total: {{ report.payables_total.toLocaleString() }} Ks</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 cursor-pointer" :class="{ 'ring-2 ring-indigo-500': activeTab === 'receivables' }" @click="activeTab = 'receivables'">
          <p class="text-xs text-gray-500 dark:text-gray-400 uppercase">Receivables (Pending)</p>
          <p class="text-2xl font-bold text-green-600 mt-1">{{ report.receivables_pending.toLocaleString() }} Ks</p>
          <p class="text-xs text-gray-400 mt-1">Total: {{ report.receivables_total.toLocaleString() }} Ks</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 uppercase">OPEX (30 days)</p>
          <p class="text-2xl font-bold text-red-600 mt-1">{{ report.opex_30d.toLocaleString() }} Ks</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="activeTab === tab.key ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'">
          {{ tab.label }}
          <span class="ml-1 opacity-75">({{ report[tab.totalKey]?.toLocaleString() }} Ks)</span>
        </button>
      </div>

      <!-- Assets Table -->
      <div v-if="activeTab === 'assets'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Purchase Date</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Notes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="asset in report.assets" :key="asset.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ asset.name || '-' }}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(asset.purchase_date) }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-indigo-600">{{ asset.amount.toLocaleString() }} Ks</td>
                <td class="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">{{ asset.notes || '-' }}</td>
              </tr>
              <tr v-if="report.assets.length === 0">
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">No assets recorded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Payables Table -->
      <div v-if="activeTab === 'payables'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Payee</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Due Date</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="p in report.payables" :key="p.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ p.payee || '-' }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-orange-600">{{ p.amount.toLocaleString() }} Ks</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(p.due_date) }}</td>
                <td class="px-4 py-3 text-center">
                  <span :class="statusBadge(p.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ p.status || '-' }}</span>
                </td>
              </tr>
              <tr v-if="report.payables.length === 0">
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">No payables recorded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Receivables Table -->
      <div v-if="activeTab === 'receivables'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Payer</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Due Date</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="r in report.receivables" :key="r.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ r.payer || '-' }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-green-600">{{ r.amount.toLocaleString() }} Ks</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(r.due_date) }}</td>
                <td class="px-4 py-3 text-center">
                  <span :class="statusBadge(r.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ r.status || '-' }}</span>
                </td>
              </tr>
              <tr v-if="report.receivables.length === 0">
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">No receivables recorded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Advances Table -->
      <div v-if="activeTab === 'advances'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Member</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Advance Date</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Settle Date</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="a in report.advances" :key="a.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ a.member_id || '-' }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-red-600">{{ a.amount.toLocaleString() }} Ks</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(a.advance_date) }}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(a.settle_date) }}</td>
                <td class="px-4 py-3 text-center">
                  <span :class="statusBadge(a.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ a.status || '-' }}</span>
                </td>
              </tr>
              <tr v-if="report.advances.length === 0">
                <td colspan="5" class="px-4 py-8 text-center text-gray-500">No advances recorded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Prepaid Table -->
      <div v-if="activeTab === 'prepaid'" class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Description</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Settle Date</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="p in report.prepaid" :key="p.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ p.description || '-' }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-purple-600">{{ p.amount.toLocaleString() }} Ks</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(p.settle_date) }}</td>
                <td class="px-4 py-3 text-center">
                  <span :class="statusBadge(p.status)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ p.status || '-' }}</span>
                </td>
              </tr>
              <tr v-if="report.prepaid.length === 0">
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">No prepaid items recorded</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="text-center py-12 text-gray-500">Failed to load financial report</div>
  </AppLayout>
</template>
