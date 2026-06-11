import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Branch {
  id: number
  name: string
  code: string
  address?: string
  phone?: string
  is_active?: boolean
}

export const useBranchStore = defineStore('branch', () => {
  const branches = ref<Branch[]>([])
  const currentBranchId = ref<number>(Number(localStorage.getItem('branch_id') || 1))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const currentBranch = computed(() =>
    branches.value.find(b => b.id === currentBranchId.value) || null
  )

  async function fetchBranches() {
    loading.value = true
    error.value = null
    try {
      const res = await axios.get('/api/dashboard/branches')
      if (res.data?.success) {
        branches.value = res.data.data || []
      }
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load branches'
      console.error('Failed to fetch branches:', e)
    } finally {
      loading.value = false
    }
  }

  function setBranch(id: number) {
    currentBranchId.value = id
    localStorage.setItem('branch_id', String(id))
  }

  return { branches, currentBranchId, currentBranch, loading, error, fetchBranches, setBranch }
})
