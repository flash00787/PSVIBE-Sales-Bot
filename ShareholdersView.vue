<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

const shareholders = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showModal = ref(false)
const editMode = ref(false)
const currentId = ref<number | null>(null)

const form = ref({
  name: '',
  role: 'Shareholder',
  capital_contribution: 0,
  ownership_pct: 0,
  notes: ''
})

const totalCapital = computed(() => shareholders.value.reduce((s, sh) => s + Number(sh.capital_contribution || 0), 0))
const totalPct = computed(() => shareholders.value.reduce((s, sh) => s + Number(sh.ownership_pct || 0), 0))

function fmt(n: any): string {
  return Number(n || 0).toLocaleString('en-US')
}

async function fetchShareholders() {
  loading.value = true; error.value = ''
  try {
    const res = await apiClient.get('/api/dashboard/shareholders')
    if (res.data.success) shareholders.value = res.data.data || []
    else error.value = res.data.error || 'Failed'
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message
  } finally { loading.value = false }
}

function openAdd() {
  editMode.value = false; currentId.value = null
  form.value = { name: '', role: 'Shareholder', capital_contribution: 0, ownership_pct: 0, notes: '' }
  showModal.value = true
}

function openEdit(sh: any) {
  editMode.value = true; currentId.value = sh.id
  form.value = { ...sh }
  form.value.capital_contribution = Number(sh.capital_contribution)
  form.value.ownership_pct = Number(sh.ownership_pct)
  showModal.value = true
}

async function save() {
  if (!form.value.name.trim()) return
  loading.value = true
  try {
    if (editMode.value && currentId.value) {
      await apiClient.put(`/api/dashboard/shareholders/${currentId.value}`, form.value)
    } else {
      await apiClient.post('/api/dashboard/shareholders', form.value)
    }
    showModal.value = false
    await fetchShareholders()
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message
  } finally { loading.value = false }
}

async function del(id: number, name: string) {
  if (!confirm(`Delete ${name}?`)) return
  try {
    await apiClient.delete(`/api/dashboard/shareholders/${id}`)
    await fetchShareholders()
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message
  }
}

onMounted(fetchShareholders)
</script>

<template>
  <AppLayout>
    <div class="p-4 lg:p-6">
      <div class="mb-6 flex items-center gap-4">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex-1">&#x1f3e6; Shareholders &amp; Capital</h1>
        <button @click="openAdd" class="px-4 py-2 bg-vibe-purple hover:bg-vibe-purple/90 text-white rounded-lg text-sm font-medium">+ Add Shareholder</button>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <p class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Total Shareholders</p>
          <p class="text-2xl font-extrabold text-vibe-purple">{{ shareholders.length }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <p class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Total Capital</p>
          <p class="text-2xl font-extrabold text-emerald-500">{{ fmt(totalCapital) }} Ks</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <p class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Ownership Allocation</p>
          <p class="text-2xl font-extrabold" :class="Math.abs(totalPct - 100) < 0.01 ? 'text-emerald-500' : 'text-red-500'">{{ fmt(totalPct) }}%</p>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-xl text-red-600 text-sm">&#x26a0;&#xfe0f; {{ error }}</div>

      <!-- Table -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Name</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Role</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Capital</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Ownership</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Notes</th>
              <th class="text-center px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sh in shareholders" :key="sh.id" class="border-t border-gray-100 dark:border-gray-700/30 hover:bg-gray-50 dark:hover:bg-gray-700/20">
              <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{{ sh.name }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="sh.role === 'Founder' ? 'bg-vibe-purple/10 text-vibe-purple' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">{{ sh.role }}</span>
              </td>
              <td class="px-4 py-3 text-right font-semibold text-emerald-600 dark:text-emerald-400">{{ fmt(sh.capital_contribution) }} Ks</td>
              <td class="px-4 py-3 text-right font-semibold">{{ Number(sh.ownership_pct).toFixed(1) }}%</td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs max-w-[200px] truncate">{{ sh.notes || '-' }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="openEdit(sh)" class="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 mr-1">Edit</button>
                <button @click="del(sh.id, sh.name)" class="text-xs px-2 py-1 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100">Del</button>
              </td>
            </tr>
            <tr v-if="!loading && shareholders.length === 0">
              <td colspan="6" class="px-4 py-8 text-center text-gray-400">No shareholders yet. Add one!</td>
            </tr>
          </tbody>
        </table>
        <div v-if="loading" class="p-4 text-center text-sm text-gray-400">Loading...</div>
      </div>

      <!-- Modal -->
      <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">{{ editMode ? 'Edit' : 'Add' }} Shareholder</h3>
          <div class="space-y-3">
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">Name *</label>
              <input v-model="form.name" class="w-full px-3 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm" /></div>
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">Role</label>
              <select v-model="form.role" class="w-full px-3 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm">
                <option>Founder</option><option>Co-Founder</option><option>Investor</option><option>Shareholder</option>
              </select></div>
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">Capital Contribution (Ks)</label>
              <input v-model.number="form.capital_contribution" type="number" class="w-full px-3 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm" /></div>
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">Ownership %</label>
              <input v-model.number="form.ownership_pct" type="number" step="0.01" class="w-full px-3 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm" /></div>
            <div><label class="text-xs font-medium text-gray-500 dark:text-gray-400">Notes</label>
              <textarea v-model="form.notes" rows="2" class="w-full px-3 py-2 rounded-lg border dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"></textarea></div>
          </div>
          <div class="flex gap-2 mt-5">
            <button @click="showModal = false" class="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm">Cancel</button>
            <button @click="save" class="flex-1 px-4 py-2 rounded-lg bg-vibe-purple text-white text-sm font-medium" :disabled="!form.name.trim()">{{ editMode ? 'Update' : 'Add' }}</button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
