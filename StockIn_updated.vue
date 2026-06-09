<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const total = ref(0)
const summary = ref<any>(null)
const submitting = ref(false)

// Stock-in history
const stockInItems = ref<any[]>([])
const stockInLoading = ref(false)
const stockInSearch = ref('')
const stockInTotal = ref(0)

// Edit state
const showEditModal = ref(false)
const editItem = ref<any>(null)
const editForm = ref({
  item_name: '',
  quantity: 0,
  unit_cost: 0,
  source: '',
  receipt_no: '',
  payment_method: '',
  paid_by: '',
  staff_name: '',
})

async function fetchItems() {
  loading.value = true
  try {
    const res = await apiClient.get('/api/dashboard/inventory', { params: { limit: 500 } })
    items.value = res.data.data || []
  } catch { items.value = [] }
  finally { loading.value = false }
}

const selectedItemId = ref<number | null>(null)
const quantity = ref(0)
const unitCost = ref(0)
const source = ref('')
const receiptNo = ref('')
const paymentMethod = ref('')
const paidBy = ref('')
const staffName = ref('')

const paymentMethods = ['Cash', 'KPay', 'WavePay', 'AYA Pay', 'KBZ Bank', 'CB Pay', 'Bank Transfer', 'Other']

const selectedItem = computed(() => items.value.find(i => i.id === selectedItemId.value))
const totalCost = computed(() => quantity.value * unitCost.value)

async function submitStockIn() {
  if (!selectedItemId.value) { alert('Please select a food item'); return }
  if (quantity.value <= 0) { alert('Quantity must be greater than 0'); return }
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
    quantity.value = 0; unitCost.value = 0; source.value = ''; receiptNo.value = ''
    paymentMethod.value = ''; paidBy.value = ''; staffName.value = ''
    selectedItemId.value = null
    fetchItems()
    fetchStockInHistory()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Stock In failed')
  }
  finally { submitting.value = false }
}

async function fetchStockInHistory() {
  stockInLoading.value = true
  try {
    const params: any = { limit: 100 }
    if (stockInSearch.value) params.search = stockInSearch.value
    const res = await apiClient.get('/api/dashboard/stock-in', { params })
    stockInItems.value = res.data.data || []
    stockInTotal.value = res.data.total || 0
  } catch { stockInItems.value = [] }
  finally { stockInLoading.value = false }
}

async function deleteStockIn(id: number) {
  if (!confirm('Delete this stock-in record? This will reverse the inventory change.')) return
  try {
    await apiClient.delete(`/api/dashboard/stock-in/${id}`)
    fetchStockInHistory()
    fetchItems()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Delete failed')
  }
}

function openEdit(si: any) {
  editItem.value = si
  editForm.value = {
    item_name: si.item_name || '',
    quantity: Number(si.quantity) || 0,
    unit_cost: Number(si.unit_cost) || 0,
    source: si.source || '',
    receipt_no: si.receipt_no || '',
    payment_method: si.payment_method || '',
    paid_by: si.paid_by || '',
    staff_name: si.staff_name || '',
  }
  showEditModal.value = true
}

async function saveEdit() {
  if (!editItem.value) return
  submitting.value = true
  try {
    await apiClient.put(`/api/dashboard/stock-in/${editItem.value.id}`, editForm.value)
    alert('Stock In record updated!')
    showEditModal.value = false
    editItem.value = null
    fetchStockInHistory()
    fetchItems()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Update failed')
  }
  finally { submitting.value = false }
}

function getPaymentBadge(pm: string): string {
  const map: Record<string, string> = {
    'Cash': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    'KPay': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'KBZ Bank': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'AYA Pay': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    'WavePay': 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
  }
  return map[pm] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchItems()
  fetchStockInHistory()
})
</script>

<template>
  <AppLayout title="Stock In">
    <h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-6">📥 Stock In — Add Stock</h1>

    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 max-w-2xl mb-8">
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

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Staff Name</label>
        <input v-model="staffName" placeholder="Staff handling this stock-in"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <!-- Payment Method -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Payment Method</label>
        <select v-model="paymentMethod"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
          <option value="">-- Select --</option>
          <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Paid By</label>
        <input v-model="paidBy" placeholder="Who paid? (e.g. Capital, Boss)"
          class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      <button @click="submitStockIn" :disabled="submitting || !selectedItemId || quantity <= 0"
        class="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50">
        {{ submitting ? 'Adding...' : '✔ Stock In' }}
      </button>
    </div>

    <!-- Stock In History -->
    <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4 mt-8">📋 Stock In History</h2>
    <div class="mb-4">
      <input v-model="stockInSearch" @input="fetchStockInHistory" placeholder="Search by item, batch, source..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
    </div>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Batch ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Item</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Qty</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Unit Cost</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Source</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Staff</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Payment</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="si in stockInItems" :key="si.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">{{ si.batch_id }}</td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">{{ si.item_name }}</td>
              <td class="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">{{ si.quantity }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ Number(si.unit_cost).toLocaleString() }} Ks</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ si.source || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ si.staff_name || '-' }}</td>
              <td class="px-4 py-3 text-sm"><span class="px-2 py-0.5 rounded text-xs font-medium" :class="getPaymentBadge(si.payment_method)">{{ si.payment_method || '-' }}</span></td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ formatDate(si.created_at) }}</td>
              <td class="px-4 py-3 text-right text-sm space-x-2">
                <button @click="openEdit(si)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors">Edit</button>
                <button @click="deleteStockIn(si.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>
              </td>
            </tr>
            <tr v-if="stockInItems.length === 0">
              <td colspan="9" class="px-4 py-8 text-center text-gray-500">No stock-in records found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="showEditModal = false"></div>
      <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4">✏️ Edit Stock In</h3>

        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Item Name</label>
          <input v-model="editForm.item_name"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantity</label>
          <input v-model.number="editForm.quantity" type="number" min="1"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unit Cost (Ks)</label>
          <input v-model.number="editForm.unit_cost" type="number" min="0" step="50"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Supplier / Source</label>
          <input v-model="editForm.source"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Receipt / Invoice No</label>
          <input v-model="editForm.receipt_no"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Payment Method</label>
          <select v-model="editForm.payment_method"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option value="">-- Select --</option>
            <option v-for="m in paymentMethods" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Paid By</label>
          <input v-model="editForm.paid_by"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Staff Name</label>
          <input v-model="editForm.staff_name"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <div class="flex justify-end gap-3">
          <button @click="showEditModal = false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveEdit" :disabled="submitting" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
            {{ submitting ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
