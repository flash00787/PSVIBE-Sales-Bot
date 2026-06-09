<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const dividends = ref<any[]>([])
const shareholders = ref<any[]>([])
const summary = ref<any>(null)
const loading = ref(false)
const error = ref('')
const showModal = ref(false)
const form = ref({
  shareholder_id: 0,
  amount: 0,
  dividend_date: new Date().toISOString().slice(0, 10),
  payment_method: 'cash',
  status: 'paid',
  notes: '',
})
const formSubmitting = ref(false)

function fmt(n: any): string { return Number(n || 0).toLocaleString('en-US') }
function formatDate(d: string): string {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return d }
}
function statusClass(s: string): string {
  const m: Record<string, string> = { paid: 'bg-emerald-100 text-emerald-700', pending: 'bg-amber-100 text-amber-700', cancelled: 'bg-red-100 text-red-700' }
  return m[s?.toLowerCase()] || 'bg-gray-100 text-gray-600'
}

const paymentMethods = ['cash', 'KPay', 'WavePay', 'AYA Pay', 'KBZ Bank', "ACM's Acc"]
const statuses = ['paid', 'pending', 'cancelled']

async function fetchDividends() {
  loading.value = true; error.value = ''
  try {
    const r = await apiClient.get('/api/dashboard/dividends/list')
    if (r.data.success) dividends.value = r.data.data || []
    else error.value = r.data.error || 'Failed to load'
  } catch (e: any) { error.value = e.response?.data?.error || e.message }
  finally { loading.value = false }
}
async function fetchSummary() {
  try {
    const r = await apiClient.get('/api/dashboard/dividends/summary')
    if (r.data.success) summary.value = r.data.data
  } catch {}
}
async function fetchShareholders() {
  try {
    const r = await apiClient.get('/api/dashboard/shareholders')
    if (r.data.success) shareholders.value = r.data.data || []
  } catch {}
}
function openModal() {
  form.value = {
    shareholder_id: shareholders.value.length > 0 ? shareholders.value[0].id : 0,
    amount: 0,
    dividend_date: new Date().toISOString().slice(0, 10),
    payment_method: 'cash',
    status: 'paid',
    notes: '',
  }
  showModal.value = true
}
async function submitDividend() {
  if (!form.value.shareholder_id || form.value.amount <= 0) { error.value = 'Select shareholder and enter amount'; return }
  formSubmitting.value = true; error.value = ''
  try {
    const r = await apiClient.post('/api/dashboard/dividends/record', form.value)
    if (r.data.success) { showModal.value = false; await Promise.all([fetchDividends(), fetchSummary()]) }
    else error.value = r.data.error || 'Failed'
  } catch (e: any) { error.value = e.response?.data?.error || e.message }
  finally { formSubmitting.value = false }
}
onMounted(async () => { await Promise.all([fetchDividends(), fetchSummary(), fetchShareholders()]) })
</script>

<template>
  <AppLayout>
    <div class="p-4 lg:p-6">
      <div class="mb-6 flex flex-wrap items-center gap-4">
        <h1 class="text-2xl font-bold flex-1">💸 Dividends</h1>
        <button @click="openModal" class="px-4 py-2 bg-vibe-purple text-white rounded-lg text-sm hover:bg-purple-700 transition">
          + Record Dividend
        </button>
      </div>

      <div v-if="error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">{{ error }}</div>

      <!-- Summary Cards -->
      <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl p-4 shadow-sm border">
          <p class="text-xs text-gray-500">Total Paid</p>
          <p class="text-xl font-extrabold text-emerald-600">{{ fmt(summary.total_paid) }} Ks</p>
        </div>
        <div v-for="sh in summary.shareholders" :key="sh.shareholder_id" class="bg-white rounded-xl p-4 shadow-sm border">
          <p class="text-xs text-gray-500 truncate">{{ sh.shareholder_name }}</p>
          <p class="text-lg font-bold text-vibe-purple">{{ fmt(sh.total_dividends) }} Ks</p>
          <p class="text-xs text-gray-400">{{ sh.dividend_count }} payment{{ sh.dividend_count !== 1 ? 's' : '' }}</p>
        </div>
      </div>

      <!-- Dividends Table -->
      <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100">
          <h3 class="text-lg font-bold">Dividend History</h3>
        </div>
        <div v-if="loading" class="p-8 text-center text-gray-400">Loading...</div>
        <div v-else-if="dividends.length === 0" class="p-8 text-center text-gray-400">
          No dividends recorded yet. Click "+ Record Dividend" to add one.
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="text-left px-4 py-3">Date</th>
              <th class="text-left px-4 py-3">Shareholder</th>
              <th class="text-right px-4 py-3">Amount</th>
              <th class="text-left px-4 py-3">Payment</th>
              <th class="text-center px-4 py-3">Status</th>
              <th class="text-left px-4 py-3 hidden lg:table-cell">Notes</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="d in dividends" :key="d.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-gray-600">{{ formatDate(d.dividend_date) }}</td>
              <td class="px-4 py-3 font-medium">{{ d.shareholder_name }}</td>
              <td class="px-4 py-3 text-right font-semibold text-emerald-600">{{ fmt(d.amount) }} Ks</td>
              <td class="px-4 py-3 text-gray-600">{{ d.payment_method }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="statusClass(d.status)" class="inline-block px-2 py-0.5 rounded-full text-xs font-medium">{{ d.status }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500 text-xs hidden lg:table-cell max-w-xs truncate">{{ d.notes || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Record Dividend Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-xl font-bold mb-4">Record Dividend</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Shareholder</label>
              <select v-model="form.shareholder_id" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple">
                <option v-for="sh in shareholders" :key="sh.id" :value="sh.id">{{ sh.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Amount (Ks)</label>
              <input v-model.number="form.amount" type="number" min="0" placeholder="e.g. 500000" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Dividend Date</label>
              <input v-model="form.dividend_date" type="date" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Payment Method</label>
              <select v-model="form.payment_method" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple">
                <option v-for="pm in paymentMethods" :key="pm" :value="pm">{{ pm }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Status</label>
              <select v-model="form.status" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Notes</label>
              <input v-model="form.notes" type="text" placeholder="Optional note..." class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-vibe-purple" />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button @click="showModal = false" class="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50">Cancel</button>
            <button @click="submitDividend" :disabled="formSubmitting" class="px-4 py-2 text-sm bg-vibe-purple text-white rounded-lg hover:bg-purple-700 disabled:opacity-50">{{ formSubmitting ? 'Saving...' : 'Save Dividend' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </AppLayout>
</template>
