<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'

interface Expense {
  id: number
  category: string
  description: string
  amount: number
  payment_method: string
  recorded_by: string
  expense_date: string
  created_at: string
}

interface CategoryTotal {
  category: string
  total: number
  count: number
}

const expenses = ref<Expense[]>([])
const loading = ref(false)
const adding = ref(false)
const deleting = ref<number | null>(null)
const summary = ref<{ categories: CategoryTotal[]; grand_total: number }>({ categories: [], grand_total: 0 })
const error = ref('')
const successMsg = ref('')

// Filters
const dateFrom = ref('')
const dateTo = ref('')
const searchQuery = ref('')

// Form
const form = ref({
  category: 'Electricity',
  description: '',
  amount: 0,
  payment_method: 'Cash',
  expense_date: new Date().toISOString().slice(0, 10),
})

const categories = [
  'Electricity', 'Water', 'Rent', 'Staff Salary', 'Internet',
  'Snacks/Drinks', 'Maintenance', 'Marketing', 'Others',
]

const paymentMethods = ['Cash', 'WavePay', 'AYA Pay', 'KPay']

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatAmount(val: number) {
  if (val == null) return '-'
  return val.toLocaleString('my-MM') + ' Ks'
}

function categoryClass(cat: string) {
  const map: Record<string, string> = {
    'Electricity': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    'Water': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    'Rent': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    'Staff Salary': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    'Internet': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
    'Snacks/Drinks': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    'Maintenance': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    'Marketing': 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400',
    'Others': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
  }
  return map[cat] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
}

async function fetchSummary() {
  try {
    const params: any = {}
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const res = await apiClient.get('/api/dashboard/opex/summary', { params })
    if (res.data.success) {
      summary.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to fetch summary:', e)
  }
}

async function fetchExpenses() {
  loading.value = true
  error.value = ''
  try {
    const params: any = {}
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (searchQuery.value) params.search = searchQuery.value
    const res = await apiClient.get('/api/dashboard/opex', { params })
    if (res.data.success) {
      expenses.value = res.data.data || []
    } else {
      error.value = res.data.error || 'Failed to load expenses'
    }
  } catch (e: any) {
    console.error('Failed to fetch expenses:', e)
    error.value = e?.response?.data?.error || e.message || 'Failed to load expenses'
  }
  finally { loading.value = false }
}

async function addExpense() {
  if (!form.value.category || form.value.amount <= 0) {
    error.value = 'Category and amount are required'
    return
  }
  adding.value = true
  error.value = ''
  successMsg.value = ''
  try {
    const res = await apiClient.post('/api/dashboard/opex', form.value)
    if (res.data.success) {
      successMsg.value = res.data.data?.msg || 'Expense added successfully'
      form.value = {
        category: 'Electricity',
        description: '',
        amount: 0,
        payment_method: 'Cash',
        expense_date: new Date().toISOString().slice(0, 10),
      }
      await fetchExpenses()
      await fetchSummary()
      setTimeout(() => { successMsg.value = '' }, 3000)
    } else {
      error.value = res.data.error || 'Failed to add expense'
    }
  } catch (e: any) {
    console.error('Failed to add expense:', e)
    error.value = e?.response?.data?.error || e.message || 'Failed to add expense'
  }
  finally { adding.value = false }
}

async function deleteExpense(item: Expense) {
  if (!confirm(`Delete this expense?\n\nCategory: ${item.category}\nAmount: ${item.amount.toLocaleString('my-MM')} Ks\nDate: ${item.expense_date}`)) {
    return
  }
  deleting.value = item.id
  error.value = ''
  successMsg.value = ''
  try {
    const res = await apiClient.delete(`/api/dashboard/opex/${item.id}`)
    if (res.data.success) {
      successMsg.value = `Expense "${item.category}" deleted`
      expenses.value = expenses.value.filter(e => e.id !== item.id)
      await fetchSummary()
      setTimeout(() => { successMsg.value = '' }, 3000)
    } else {
      error.value = res.data.error || 'Failed to delete expense'
    }
  } catch (e: any) {
    console.error('Failed to delete expense:', e)
    error.value = e?.response?.data?.error || e.message || 'Failed to delete expense'
  }
  finally { deleting.value = null }
}

onMounted(() => {
  fetchExpenses()
  fetchSummary()
})
</script>

<template>
  <AppLayout title="OPEX">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">💰 OPEX Management</h1>
    </div>

    <!-- Summary Cards -->
    <div v-if="summary.grand_total > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5 border-l-4 border-indigo-500">
        <p class="text-sm text-gray-500 dark:text-gray-400">Total Expenses</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ summary.grand_total.toLocaleString('my-MM') }} Ks</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5 border-l-4 border-emerald-500">
        <p class="text-sm text-gray-500 dark:text-gray-400">Categories</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ summary.categories.length }}</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5 border-l-4 border-amber-500">
        <p class="text-sm text-gray-500 dark:text-gray-400">Top Category</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ summary.categories[0]?.category || '-' }}</p>
        <p v-if="summary.categories[0]" class="text-sm text-gray-500">{{ summary.categories[0].total.toLocaleString('my-MM') }} Ks</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5 border-l-4 border-rose-500">
        <p class="text-sm text-gray-500 dark:text-gray-400">Transactions</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ summary.categories.reduce((s, c) => s + c.count, 0) }}
        </p>
      </div>
    </div>

    <!-- Add Expense Form -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">➕ Add New Expense</h2>
      
      <div v-if="successMsg" class="mb-4 px-4 py-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
        ✅ {{ successMsg }}
      </div>
      <div v-if="error && !successMsg" class="mb-4 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
        ❌ {{ error }}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <!-- Category -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category *</label>
          <select v-model="form.category"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>

        <!-- Description -->
        <div class="md:col-span-1">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
          <input v-model="form.description" type="text" placeholder="Optional note..."
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
        </div>

        <!-- Amount -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Amount (Ks) *</label>
          <input v-model.number="form.amount" type="number" min="0" placeholder="0"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
        </div>

        <!-- Payment Method -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Payment</label>
          <select v-model="form.payment_method"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
            <option v-for="pm in paymentMethods" :key="pm" :value="pm">{{ pm }}</option>
          </select>
        </div>

        <!-- Date -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
          <input v-model="form.expense_date" type="date"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
        </div>

        <!-- Submit -->
        <div class="flex items-end">
          <button @click="addExpense" :disabled="adding"
            class="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg text-sm font-medium transition-colors">
            <span v-if="adding" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2 align-middle"></span>
            {{ adding ? 'Adding...' : 'Add Expense' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Category Breakdown -->
    <div v-if="summary.categories.length > 0" class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">📊 Category Breakdown</h2>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Category</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Count</th>
              <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Total</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Bar</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="cat in summary.categories" :key="cat.category">
              <td class="px-4 py-2 text-sm">
                <span :class="categoryClass(cat.category)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ cat.category }}</span>
              </td>
              <td class="px-4 py-2 text-sm text-right text-gray-700 dark:text-gray-300">{{ cat.count }}</td>
              <td class="px-4 py-2 text-sm text-right font-medium text-gray-900 dark:text-white">{{ cat.total.toLocaleString('my-MM') }} Ks</td>
              <td class="px-4 py-2 text-sm">
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                  <div class="h-2.5 rounded-full bg-indigo-500"
                    :style="{ width: summary.grand_total > 0 ? (cat.total / summary.grand_total * 100) + '%' : '0%' }"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4 items-end">
      <div>
        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">From</label>
        <input v-model="dateFrom" type="date" @change="fetchExpenses(); fetchSummary()"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm" />
      </div>
      <div>
        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">To</label>
        <input v-model="dateTo" type="date" @change="fetchExpenses(); fetchSummary()"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm" />
      </div>
      <div class="flex-1 min-w-[200px]">
        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Search</label>
        <input v-model="searchQuery" @input="fetchExpenses" placeholder="Search category, description..."
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm" />
      </div>
      <div>
        <button @click="dateFrom = ''; dateTo = ''; searchQuery = ''; fetchExpenses(); fetchSummary()"
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm">
          Clear Filters
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>

    <!-- Expense List Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Description</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Amount</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Payment</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Recorded By</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Delete</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in expenses" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ formatDate(item.expense_date) }}</td>
              <td class="px-4 py-3 text-sm">
                <span :class="categoryClass(item.category)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ item.category }}</span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 max-w-xs truncate">{{ item.description || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white whitespace-nowrap">{{ formatAmount(item.amount) }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.payment_method || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.recorded_by || '-' }}</td>
              <td class="px-4 py-3 text-center">
                <button
                  @click="deleteExpense(item)"
                  :disabled="deleting === item.id"
                  class="px-3 py-1.5 text-xs font-medium text-red-600 hover:text-white bg-red-50 hover:bg-red-600 dark:bg-red-900/20 dark:hover:bg-red-700 dark:text-red-400 dark:hover:text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Delete this expense"
                >
                  <span v-if="deleting === item.id" class="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-1 align-middle"></span>
                  🗑️ Delete
                </button>
              </td>
            </tr>
            <tr v-if="expenses.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                No expenses found
                <p class="text-sm mt-1">Try adjusting your filters or add a new expense above.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>
