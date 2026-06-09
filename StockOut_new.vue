<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

const items = ref<any[]>([])
const loading = ref(false)
const submitting = ref(false)

const selectedItemId = ref<number | null>(null)
const quantity = ref(0)
const salePrice = ref(0)
const notes = ref('')

// Stock-out history
const stockOutItems = ref<any[]>([])
const stockOutLoading = ref(false)
const stockOutSearch = ref('')
const stockOutTotal = ref(0)

const selectedItem = computed(() => items.value.find(i => i.id === selectedItemId.value))
const maxQuantity = computed(() => selectedItem.value?.quantity || 0)

async function fetchItems() {
  loading.value = true
  try {
    const res = await apiClient.get('/api/dashboard/inventory', { params: { limit: 500 } })
    items.value = res.data.data || []
  } catch { items.value = [] }
  finally { loading.value = false }
}

async function submitStockOut() {
  if (!selectedItemId.value) { alert('Please select a food item'); return }
  if (quantity.value <= 0) { alert('Quantity must be greater than 0'); return }
  if (quantity.value > maxQuantity.value) { alert('Not enough stock! Available: ' + maxQuantity.value); return }
  submitting.value = true
  try {
    await apiClient.post('/api/dashboard/stock-out', {
      item_id: selectedItemId.value,
      quantity: quantity.value,
      unit_price: salePrice.value,
      notes: notes.value,
    })
    alert('Deducted ' + quantity.value + ' units from ' + selectedItem.value?.item_name + '!')
    quantity.value = 0; salePrice.value = 0; notes.value = ''
    selectedItemId.value = null
    fetchItems()
    fetchStockOutHistory()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Stock Out failed')
  }
  finally { submitting.value = false }
}

async function fetchStockOutHistory() {
  stockOutLoading.value = true
  try {
    const params: any = { limit: 100 }
    if (stockOutSearch.value) params.search = stockOutSearch.value
    const res = await apiClient.get('/api/dashboard/stock-out', { params })
    stockOutItems.value = res.data.data || []
    stockOutTotal.value = res.data.total || 0
  } catch { stockOutItems.value = [] }
  finally { stockOutLoading.value = false }
}

async function deleteStockOut(id: number) {
  if (!confirm('Delete this stock-out record? This will restore the inventory quantity.')) return
  try {
    await apiClient.delete(`/api/dashboard/stock-out/${id}`)
    fetchStockOutHistory()
    fetchItems()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Delete failed')
  }
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchItems()
  fetchStockOutHistory()
})
</script>

<template>
  <AppLayout title="Stock Out">
    <h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-6">📤 Stock Out — Deduct Stock</h1>

    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 max-w-2xl mb-8">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Select Food Item *</label>
        <select v-model="selectedItemId"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option :value="null">-- Choose an item --</option>
          <option v-for="item in items" :key="item.id" :value="item.id">
            {{ item.item_name }} — Stock: {{ item.quantity }}
          </option>
        </select>
      </div>

      <div v-if="selectedItem" class="mb-6 p-4 rounded-lg" :class="selectedItem.quantity <= 0 ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50 dark:bg-gray-700'">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          Current Stock: <span class="font-bold text-lg" :class="selectedItem.quantity <= (selectedItem.reorder_level || 0) ? 'text-red-600' : 'text-gray-900 dark:text-white'">{{ selectedItem.quantity }}</span>
          <span v-if="selectedItem.quantity <= 0" class="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">Out of Stock!</span>
        </p>
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">Max Deductible: {{ selectedItem.quantity }}</p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quantity to Deduct *</label>
        <input v-model.number="quantity" type="number" min="1" :max="maxQuantity" placeholder="Enter quantity"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sale Price (Ks)</label>
        <input v-model.number="salePrice" type="number" min="0" step="50" placeholder="Price at which sold"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Notes</label>
        <input v-model="notes" placeholder="Reason / reference"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <button @click="submitStockOut" :disabled="submitting || !selectedItemId || quantity <= 0 || quantity > maxQuantity"
        class="w-full bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50">
        {{ submitting ? 'Processing...' : '✘ Stock Out' }}
      </button>
    </div>

    <!-- Stock Out History -->
    <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4 mt-8">📋 Stock Out History</h2>
    <div class="mb-4">
      <input v-model="stockOutSearch" @input="fetchStockOutHistory" placeholder="Search by item, staff, notes..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
    </div>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Item</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Qty</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Price</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Total</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Staff</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Notes</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="so in stockOutItems" :key="so.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">{{ so.item_name }}</td>
              <td class="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">{{ so.quantity }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ Number(so.unit_price).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">{{ Number(so.total).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ so.staff_name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ formatDate(so.sale_date || so.created_at) }}</td>
              <td class="px-4 py-3 text-sm text-gray-500 max-w-[200px] truncate">{{ so.notes || '-' }}</td>
              <td class="px-4 py-3 text-right text-sm">
                <button @click="deleteStockOut(so.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="stockOutItems.length === 0">
              <td colspan="8" class="px-4 py-8 text-center text-gray-500">No stock-out records found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>
