<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

const items = ref<any[]>([])
const loading = ref(false)
const selectedItemId = ref<number | null>(null)
const quantity = ref(0)
const unitCost = ref(0)
const source = ref('')
const receiptNo = ref('')
const paymentMethod = ref('')
const paidBy = ref('')
const staffName = ref('')
const submitting = ref(false)

const paymentMethods = ['Cash', 'KPay', 'WavePay', 'AYA Pay', 'CB Pay', 'Bank Transfer', 'Other']

const selectedItem = computed(() => items.value.find(i => i.id === selectedItemId.value))
const totalCost = computed(() => quantity.value * unitCost.value)

async function fetchItems() {
  loading.value = true
  try {
    const res = await apiClient.get('/api/dashboard/inventory', { params: { limit: 500 } })
    items.value = res.data.data || []
  } catch { items.value = [] }
  finally { loading.value = false }
}

async function submitStockIn() {
  if (!selectedItemId.value) {
    alert('Please select a food item')
    return
  }
  if (quantity.value <= 0) {
    alert('Quantity must be greater than 0')
    return
  }
  submitting.value = true
  try {
    await apiClient.post('/api/dashboard/stock-in', {
      item_id: selectedItemId.value,
      quantity: quantity.value,
      unit_cost: unitCost.value,
      source: source.value,
      receipt_no: receiptNo.value,
      payment_method: paymentMethod.value,
      paid_by: paidBy.value,
      staff_name: staffName.value,
    })
    alert('Added ' + quantity.value + ' units to ' + selectedItem.value?.item_name + '!')
    quantity.value = 0
    unitCost.value = 0
    source.value = ''
    receiptNo.value = ''
    paymentMethod.value = ''
    paidBy.value = ''
    staffName.value = ''
    selectedItemId.value = null
    fetchItems()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Stock In failed')
  }
  finally { submitting.value = false }
}

onMounted(fetchItems)
</script>

<template>
  <AppLayout title="Stock In">
    <h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-6">📥 Stock In — Add Stock</h1>

    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 max-w-2xl">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Select Food Item *</label>
        <select v-model="selectedItemId"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option :value="null">-- Choose an item --</option>
          <option v-for="item in items" :key="item.id" :value="item.id">
            {{ item.item_name }} — Stock: {{ item.quantity }} | Price: {{ Number(item.unit_price).toLocaleString() }} Ks
          </option>
        </select>
      </div>

      <div v-if="selectedItem" class="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          Current Stock: <span class="font-bold text-gray-900 dark:text-white">{{ selectedItem.quantity }}</span>
          <span v-if="selectedItem.quantity <= (selectedItem.reorder_level || 0)" class="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">Low Stock!</span>
        </p>
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">Sell Price: {{ Number(selectedItem.unit_price).toLocaleString() }} Ks</p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quantity to Add *</label>
        <input v-model.number="quantity" type="number" min="1" placeholder="Enter quantity"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Unit Cost (Ks)</label>
        <input v-model.number="unitCost" type="number" min="0" step="50" placeholder="Cost per item"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        <p v-if="quantity > 0 && unitCost > 0" class="text-xs text-indigo-600 dark:text-indigo-400 mt-1">
          Total Cost: {{ totalCost.toLocaleString() }} Ks
        </p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Supplier / Source</label>
        <input v-model="source" placeholder="e.g. Metro Wholesale"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Receipt / Invoice No</label>
        <input v-model="receiptNo" placeholder="e.g. INV-2024-001"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <!-- Payment Section -->
      <div class="border-t border-gray-200 dark:border-gray-600 pt-4 mt-4 mb-4">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">💳 Payment Details</h3>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Payment Method</label>
          <select v-model="paymentMethod"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option value="">-- Select payment method --</option>
            <option v-for="pm in paymentMethods" :key="pm" :value="pm">{{ pm }}</option>
          </select>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Paid By</label>
          <input v-model="paidBy" placeholder="Who paid for this stock?"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Staff Name</label>
          <input v-model="staffName" placeholder="Staff handling this stock-in"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
      </div>

      <button @click="submitStockIn" :disabled="submitting || !selectedItemId || quantity <= 0"
        class="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50">
        {{ submitting ? 'Adding...' : '✔ Stock In' }}
      </button>
    </div>
  </AppLayout>
</template>
