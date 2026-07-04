<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">📥 Purchases</h2>
      <button @click="showForm=true;resetForm()" class="btn-primary">+ New Purchase</button>
    </div>
    <!-- Filters -->
    <div class="card mb-4 flex gap-3 flex-wrap">
      <input v-model="dateFrom" type="date" @change="load" class="input-field w-40" />
      <input v-model="dateTo" type="date" @change="load" class="input-field w-40" />
    </div>
    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead><tr class="border-b text-left text-gray-500">
          <th class="p-3">GRN #</th><th class="p-3">Date</th><th class="p-3">Supplier</th><th class="p-3 text-right">Total</th><th class="p-3 text-right">Paid</th><th class="p-3 text-right">Balance</th><th class="p-3"></th>
        </tr></thead>
        <tbody>
          <tr v-for="p in purchases" :key="p.id" class="border-b hover:bg-gray-50">
            <td class="p-3 font-mono text-xs">{{ p.grn_number }}</td>
            <td class="p-3">{{ p.purchase_date }}</td>
            <td class="p-3">{{ p.supplier_name || '-' }}</td>
            <td class="p-3 text-right font-medium">{{ fmt(p.total_amount) }} Ks</td>
            <td class="p-3 text-right">{{ fmt(p.paid_amount) }} Ks</td>
            <td class="p-3 text-right" :class="(p.total_amount-p.paid_amount)>0?'text-red-600':''">{{ fmt(p.total_amount - p.paid_amount) }} Ks</td>
            <td class="p-3"><button @click="viewPurchase(p.id)" class="text-primary-600 hover:underline text-xs">View</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- View Purchase Modal -->
    <div v-if="viewing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="viewing=null">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="text-lg font-bold">{{ viewing.grn_number }}</h3>
          <button @click="viewing=null" class="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <div class="flex-1 overflow-auto p-4 space-y-4">
          <!-- Header Info -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-500">Date:</span> <b>{{ viewing.purchase_date }}</b></div>
            <div><span class="text-gray-500">Supplier:</span> <b>{{ viewing.supplier_name || 'N/A' }}</b></div>
          </div>
          <!-- Items Table -->
          <div>
            <h4 class="font-semibold text-gray-700 mb-2">Items</h4>
            <table class="w-full text-sm border">
              <thead><tr class="bg-gray-50 border-b text-left">
                <th class="p-2">Product</th><th class="p-2">Variant</th><th class="p-2 text-right">Qty</th><th class="p-2 text-right">Unit Cost</th><th class="p-2 text-right">Total</th>
              </tr></thead>
              <tbody>
                <tr v-for="it in viewing.items" :key="it.id" class="border-b">
                  <td class="p-2">{{ it.product_name }} <span class="text-gray-400 text-xs">({{ it.product_code }})</span></td>
                  <td class="p-2 text-xs">{{ it.size }} / {{ it.color }}</td>
                  <td class="p-2 text-right">{{ it.qty }}</td>
                  <td class="p-2 text-right">{{ fmt(it.unit_cost) }} Ks</td>
                  <td class="p-2 text-right font-medium">{{ fmt(it.qty * it.unit_cost) }} Ks</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Totals -->
          <div class="border rounded-lg p-4 bg-gray-50">
            <div class="grid grid-cols-3 gap-4 text-center">
              <div><p class="text-xs text-gray-500">Total Amount</p><p class="text-xl font-bold text-primary-600">{{ fmt(viewing.total_amount) }} Ks</p></div>
              <div><p class="text-xs text-gray-500">Paid Amount</p><p class="text-xl font-bold text-green-600">{{ fmt(viewing.paid_amount) }} Ks</p></div>
              <div><p class="text-xs text-gray-500">Balance</p><p class="text-xl font-bold" :class="(viewing.total_amount-viewing.paid_amount)>0?'text-red-600':'text-gray-600'">{{ fmt(viewing.total_amount - viewing.paid_amount) }} Ks</p></div>
            </div>
          </div>
          <!-- Payment Breakdown -->
          <div v-if="viewing.payment_breakdown && viewing.payment_breakdown.length" class="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-2 font-medium">Payment Breakdown:</p>
            <div v-for="(pb, i) in viewing.payment_breakdown" :key="i" class="flex justify-between text-xs mb-1">
              <span>{{ pb.method }}</span>
              <span class="font-medium">{{ fmt(pb.amount) }} Ks</span>
            </div>
          </div>
          <!-- Notes -->
          <div v-if="viewing.notes" class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-1">Notes</p>
            <p class="text-sm">{{ viewing.notes }}</p>
          </div>
        </div>
        <div class="p-3 border-t">
          <button @click="viewing=null" class="btn-secondary w-full">Close</button>
        </div>
      </div>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex z-50" @click.self="showForm=false">
      <div class="bg-white w-full max-w-2xl mx-auto my-8 rounded-xl shadow-xl flex flex-col max-h-[90vh]">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="text-lg font-bold">New Purchase</h3><button @click="showForm=false" class="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <div class="flex-1 overflow-auto p-4 space-y-3">
          <div class="flex gap-3">
            <div class="flex-1"><label class="text-sm font-medium">Date</label><input v-model="form.purchase_date" type="date" class="input-field" /></div>
            <div class="flex-1"><label class="text-sm font-medium">Supplier</label><select v-model="form.supplier_id" class="input-field"><option value="">None</option><option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option></select></div>
          </div>

          <!-- Search/add items with autocomplete -->
          <div class="relative">
            <div class="flex gap-2">
              <input ref="itemSearchInput" v-model="itemSearch" @input="onItemSearchInput" @keydown="onItemSearchKeydown" @focus="openItemSuggestions" @blur="onItemSearchBlur"
                placeholder="Search product..." class="input-field flex-1" />
              <button @click="searchItems" class="btn-primary btn-sm">Search</button>
            </div>
            <!-- Suggestion Dropdown -->
            <div v-if="showItemSuggestions && itemResults.length" class="absolute z-20 left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg max-h-56 overflow-auto">
              <div v-for="(r, idx) in itemResults" :key="r.id"
                @mousedown.prevent="addItem(r)"
                class="flex items-center gap-3 p-3 hover:bg-primary-50 cursor-pointer border-b last:border-b-0"
                :class="{ 'bg-primary-50': idx === itemSuggestionIdx }">
                <div class="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-xs flex-shrink-0" :style="{ backgroundColor: avatarColor(r.name) }">
                  {{ r.name.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium truncate">{{ r.name }}</div>
                  <div class="text-xs text-gray-400">{{ r.code }} - {{ r.size }}/{{ r.color }}</div>
                </div>
                <div class="text-xs text-gray-400">Stock: {{ r.stock_qty }}</div>
              </div>
            </div>
          </div>

          <!-- Cart Items -->
          <div v-if="form.items.length">
            <div class="flex justify-between items-center mb-2">
              <h4 class="font-medium text-sm">Items ({{ form.items.length }})</h4>
              <button @click="clearPurchaseCart" class="text-xs text-red-500 hover:text-red-700 hover:underline">🗑 Clear</button>
            </div>
            <div class="space-y-2">
              <div v-for="(it,i) in form.items" :key="i" class="flex items-center gap-2 p-2 bg-gray-50 rounded border text-sm">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs flex-shrink-0" :style="{ backgroundColor: avatarColor(it.name) }">
                  {{ it.name.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate text-xs">{{ it.name }}</div>
                  <div class="text-gray-400 text-xs">{{ it.code }} - {{ it.size }}/{{ it.color }}</div>
                </div>
                <div class="flex items-center gap-1">
                  <button @click="it.qty>1?it.qty--:null" class="w-6 h-6 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 text-xs">−</button>
                  <input v-model.number="it.qty" type="number" min="1" class="input-field w-14 text-center text-xs py-0.5" />
                  <button @click="it.qty++" class="w-6 h-6 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 text-xs">+</button>
                </div>
                <input v-model.number="it.unit_cost" type="number" min="0" class="input-field w-20 text-xs" placeholder="Cost" />
                <span class="w-20 text-right font-medium text-xs">{{ fmt(it.qty*it.unit_cost) }} Ks</span>
                <button @click="form.items.splice(i,1)" class="text-red-400 hover:text-red-600">✕</button>
              </div>
            </div>
            <div class="text-right font-bold mt-3 text-lg">Total: <span class="text-primary-600">{{ fmt(tot) }} Ks</span></div>
          </div>

          <!-- Paid Amount -->
          <div><label class="text-sm font-medium">Paid Amount</label><input v-model.number="form.paid_amount" type="number" min="0" class="input-field max-w-xs" /></div>

          <!-- Split Payment Toggle -->
          <div>
            <label class="flex items-center gap-2 text-sm font-medium mb-2">
              <input type="checkbox" v-model="splitPayment" class="rounded" />
              <span>Split Payment (track which account money came from)</span>
            </label>
            <div v-if="splitPayment" class="space-y-2">
              <div v-for="(row, i) in splitRows" :key="i" class="flex gap-2 items-center">
                <select v-model="row.method" class="input-field flex-1"><option>Cash</option><option>KPay</option><option>WavePay</option><option>Bank Transfer</option></select>
                <input v-model.number="row.amount" type="number" min="0" class="input-field w-28 text-right" />
                <button @click="removeSplitRow(i)" class="text-red-400 hover:text-red-600" v-if="splitRows.length>1">✕</button>
              </div>
              <div class="flex justify-between items-center text-xs">
                <button @click="addSplitRow" class="text-primary-600 hover:underline">+ Add account</button>
                <span>Remaining: <b :class="splitRemaining!==0?'text-red-600':'text-green-600'">{{ fmt(splitRemaining) }} Ks</b></span>
              </div>
            </div>
          </div>

          <div><label class="text-sm font-medium">Notes</label><textarea v-model="form.notes" class="input-field" rows="2"></textarea></div>
          <button @click="save" :disabled="saving" class="btn-primary w-full">{{ saving?'Saving...':'Save Purchase' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'; import api from '../api'
const purchases=ref([]); const showForm=ref(false); const viewing=ref(null)
const form=ref({purchase_date:'',supplier_id:'',items:[],paid_amount:0,notes:''})
const suppliers=ref([]); const itemSearch=ref(''); const itemResults=ref([]); const showItemSuggestions=ref(false); const itemSuggestionIdx=ref(-1)
const saving=ref(false); const itemSearchInput=ref(null)
const dateFrom=ref(''); const dateTo=ref('')
const splitPayment=ref(false); const splitRows=ref([{method:'Cash',amount:0}])

let searchTimer = null

function fmt(v){return v?Number(v).toLocaleString():'0'}
function avatarColor(name){const colors=['#6366f1','#8b5cf6','#ec4899','#f43f5e','#f97316','#eab308','#22c55e','#14b8a6','#06b6d4','#3b82f6'];let hash=0;for(let i=0;i<(name||'A').length;i++)hash=(hash*31+(name||'A').charCodeAt(i))&0xfffffff;return colors[hash%colors.length]}
const tot=computed(()=>form.value.items.reduce((s,i)=>s+i.qty*i.unit_cost,0))
const splitTotal=computed(()=>splitRows.value.reduce((s,r)=>s+(r.amount||0),0))
const splitRemaining=computed(()=>form.value.paid_amount - splitTotal.value)

function resetForm(){form.value={purchase_date:new Date().toISOString().slice(0,10),supplier_id:'',items:[],paid_amount:0,notes:''};splitPayment.value=false;splitRows.value=[{method:'Cash',amount:0}]}
function clearPurchaseCart(){form.value.items=[];splitRows.value=[{method:'Cash',amount:0}]}
async function load(){
  const p={}; if(dateFrom.value)p.date_from=dateFrom.value; if(dateTo.value)p.date_to=dateTo.value
  const {data}=await api.get('/purchases',{params:p});purchases.value=data.items
}
async function loadSuppliers(){const {data}=await api.get('/suppliers',{params:{limit:200}});suppliers.value=data.items}
async function searchItems(){
  if(!itemSearch.value)return
  const {data}=await api.get('/products',{params:{search:itemSearch.value,limit:15}})
  itemResults.value=[]
  for(const p of data.items){const {data:v}=await api.get(`/products/${p.id}/variants`);v.forEach(vr=>itemResults.value.push({...vr,name:p.name,code:p.code,product_id:p.id}))}
}

function onItemSearchInput(){
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!itemSearch.value) { itemResults.value = []; showItemSuggestions.value = false; return }
    await searchItems()
    showItemSuggestions.value = true
    itemSuggestionIdx.value = -1
  }, 300)
}

function onItemSearchKeydown(e){
  if (!showItemSuggestions.value) return
  if (e.key === 'ArrowDown') { e.preventDefault(); itemSuggestionIdx.value = Math.min(itemSuggestionIdx.value + 1, itemResults.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); itemSuggestionIdx.value = Math.max(itemSuggestionIdx.value - 1, -1) }
  else if (e.key === 'Enter') {
    e.preventDefault()
    if (itemSuggestionIdx.value >= 0 && itemSuggestionIdx.value < itemResults.value.length) {
      addItem(itemResults.value[itemSuggestionIdx.value])
    } else { searchItems() }
  }
  else if (e.key === 'Escape') { showItemSuggestions.value = false }
}

function onItemSearchBlur(){ setTimeout(() => { showItemSuggestions.value = false }, 200) }
function openItemSuggestions(){ if (itemResults.value.length) showItemSuggestions.value = true }

function addItem(r){
  if(!form.value.items.find(i=>i.variant_id===r.id)){
    form.value.items.push({variant_id:r.id,name:r.name,code:r.code,size:r.size,color:r.color,qty:1,unit_cost:0})
  }
  itemResults.value=[];itemSearch.value='';showItemSuggestions.value=false
}

function addSplitRow(){ splitRows.value.push({method:'Cash',amount:0}) }
function removeSplitRow(i){ if(splitRows.value.length>1) splitRows.value.splice(i,1) }

async function save(){
  if(!form.value.items.length)return
  if(splitPayment.value && Math.abs(splitRemaining.value) > 0.01){ alert('Split payment amounts must equal paid amount!'); return }
  saving.value=true
  try{
    const payload = { ...form.value, supplier_id: form.value.supplier_id || null }
    if(splitPayment.value){ payload.payment_breakdown = splitRows.value.filter(r=>r.amount>0) }
    await api.post('/purchases', payload)
    showForm.value=false;await load()
  }catch(e){alert(e.response?.data?.detail||'Failed')}finally{saving.value=false}
}
async function viewPurchase(id){const {data}=await api.get(`/purchases/${id}`);viewing.value=data}
onMounted(()=>{load();loadSuppliers()})
</script>