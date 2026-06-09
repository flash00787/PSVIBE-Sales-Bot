# Patch Inventory.vue - add Edit & Delete buttons, and edit modal
path = 'src/views/Inventory.vue'
with open(path, 'r') as f:
    content = f.read()

# Add Edit and Delete buttons in the Actions column header + rows
# 1. Add "Actions" header cell
old_header = '<th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Reorder At</th>'
new_header = '<th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Reorder At</th>\n              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>'
content = content.replace(old_header, new_header)

# 2. Add Actions cell with Edit+Delete buttons alongside the Reorder At cell
# The row ends with Reorder At td, then empty colspan=8. Let me find the exact pattern.
# Current pattern for item rows:
old_row_end = '<td class="px-4 py-3 text-sm text-right text-gray-500">≤ {{ item.reorder_level || 0 }}</td>'
new_row_end = '<td class="px-4 py-3 text-sm text-right text-gray-500">≤ {{ item.reorder_level || 0 }}</td>\n              <td class="px-4 py-3 text-right text-sm">\n                <button @click="openEdit(item)" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-2 transition-colors">Edit</button>\n                <button @click="deleteItem(item.id)" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors">Delete</button>\n              </td>'
content = content.replace(old_row_end, new_row_end)

# 3. Update colspan for empty state from 8 to 9
content = content.replace('colspan="8"', 'colspan="9"')

# 4. Add edit modal (before closing </template>)
# First add script functions: showEdit, saveItem, deleteItem
old_script = '''const search = ref('')
const categoryFilter = ref('')
const total = ref(0)'''
new_script = '''const search = ref('')
const categoryFilter = ref('')
const total = ref(0)
const showModal = ref(false)
const editing = ref<any>(null)
const form = ref({ item_name: '', category: '', quantity: 0, unit_price: 0, reorder_level: 0 })

function openCreate() {
  editing.value = null
  form.value = { item_name: '', category: '', quantity: 0, unit_price: 0, reorder_level: 0 }
  showModal.value = true
}

function openEdit(item: any) {
  editing.value = item
  form.value = {
    item_name: item.item_name || '',
    category: item.category || '',
    quantity: item.quantity || 0,
    unit_price: item.unit_price || 0,
    reorder_level: item.reorder_level || 0,
  }
  showModal.value = true
}

async function saveItem() {
  loading.value = true
  try {
    if (editing.value) {
      await apiClient.put(`/api/dashboard/inventory/${editing.value.id}`, form.value)
    } else {
      await apiClient.post('/api/dashboard/inventory', form.value)
    }
    showModal.value = false
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Save failed')
  }
  finally { loading.value = false }
}

async function deleteItem(id: number) {
  if (!confirm('Delete this inventory item?')) return
  try {
    await apiClient.delete(`/api/dashboard/inventory/${id}`)
    fetchData()
  } catch (e: any) {
    alert(e?.response?.data?.error || 'Delete failed')
  }
}'''
content = content.replace(old_script, new_script)

# Add apiClient import if missing
if "import apiClient from '@/api/client'" not in content:
    content = content.replace(
        "import { ref, onMounted, computed } from 'vue'",
        "import { ref, onMounted, computed } from 'vue'\nimport apiClient from '@/api/client'"
    )

# Add "+ Add Item" button and edit modal before closing </template>
old_template_end = '  </AppLayout>\n</template>'
new_template_end = '''    <!-- Edit/Create Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showModal=false">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ editing ? 'Edit Item' : 'Add Item' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Item Name</label>
            <input v-model="form.item_name"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
            <select v-model="form.category"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="">Select category</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantity</label>
              <input v-model.number="form.quantity" type="number" min="0"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unit Price</label>
              <input v-model.number="form.unit_price" type="number" min="0" step="50"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Reorder Level</label>
            <input v-model.number="form.reorder_level" type="number" min="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal=false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">Cancel</button>
          <button @click="saveItem" :disabled="loading" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50">Save</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>'''
content = content.replace(old_template_end, new_template_end)

# Add "+ Add New" button after title
old_title = '<h1 class="text-2xl font-bold text-gray-800 dark:text-white mb-6">📊 Food Inventory Overview</h1>'
new_title = '''<div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">📊 Food Inventory Overview</h1>
      <button @click="openCreate" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors">
        + Add Item
      </button>
    </div>'''
content = content.replace(old_title, new_title)

with open(path, 'w') as f:
    f.write(content)
print('Inventory.vue: Edit/Delete buttons, modal, and Add button added')
