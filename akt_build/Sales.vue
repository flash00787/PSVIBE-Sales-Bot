<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">🛒 Sales</h2>
      <button @click="newSale" class="btn-primary">+ New Sale</button>
    </div>
    <!-- Sales List -->
    <div class="card overflow-x-auto">
      <div class="flex gap-3 mb-3 flex-wrap">
        <input v-model="dateFilter" type="date" @change="load" class="input-field w-40" />
        <input v-model="dateTo" type="date" @change="load" class="input-field w-40" />
        <select v-model="statusFilter" @change="load" class="input-field w-40">
          <option value="">All Status</option><option value="Paid">Paid</option><option value="Partial">Partial</option><option value="Unpaid">Unpaid</option>
        </select>
      </div>
      <table class="w-full text-sm">
        <thead><tr class="border-b text-left text-gray-500">
          <th class="p-3">Invoice</th><th class="p-3">Date</th><th class="p-3">Customer</th>
          <th class="p-3 text-right">Total</th><th class="p-3">Payment</th><th class="p-3">Status</th><th class="p-3"></th>
        </tr></thead>
        <tbody>
          <tr v-for="s in sales" :key="s.id" class="border-b hover:bg-gray-50">
            <td class="p-3 font-mono text-xs">{{ s.invoice_number }}</td>
            <td class="p-3 text-xs">{{ fmtDate(s.sale_date) }}</td>
            <td class="p-3">{{ s.customer_name || 'Walk-in' }}</td>
            <td class="p-3 text-right font-medium">{{ fmt(s.total_amount) }} Ks</td>
            <td class="p-3 text-xs">{{ s.payment_method }}</td>
            <td class="p-3"><span :class="s.payment_status==='Paid'?'badge-green':s.payment_status==='Partial'?'badge-yellow':'badge-red'">{{ s.payment_status }}</span></td>
            <td class="p-3">
              <button @click="viewSale(s.id)" class="text-primary-600 hover:underline text-xs mr-2">View</button>
              <button v-if="!s.is_void" @click="voidSale(s.id)" class="text-red-500 hover:underline text-xs">Void</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="p-3 text-sm text-gray-500">{{ total }} sales</div>
    </div>

    <!-- New Sale Modal -->
    <div v-if="showSaleForm" class="fixed inset-0 bg-black/40 flex z-50" @click.self="showSaleForm=false">
      <div class="bg-white w-full max-w-4xl mx-auto my-8 rounded-xl shadow-xl flex flex-col max-h-[90vh]">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="text-lg font-bold">New Sale</h3>
          <button @click="showSaleForm=false" class="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <div class="flex-1 overflow-auto p-4">
          <!-- Product Search with Autocomplete -->
          <div class="relative mb-4">
            <div class="flex gap-2">
              <input ref="searchInput" v-model="productSearch" @input="onSearchInput" @keydown="onSearchKeydown" @focus="openSuggestions" @blur="onSearchBlur"
                placeholder="Search product (name/code/barcode)..." class="input-field flex-1" />
              <button @click="searchProducts" class="btn-primary btn-sm">Search</button>
            </div>
            <!-- Suggestion Dropdown -->
            <div v-if="showSuggestions && suggestionResults.length" class="absolute z-20 left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg max-h-64 overflow-auto">
              <div v-for="(p, idx) in suggestionResults" :key="'s'+p.id"
                @mousedown.prevent="addToCart(p)"
                class="flex items-center gap-3 p-3 hover:bg-primary-50 cursor-pointer border-b last:border-b-0"
                :class="{ 'bg-primary-50': idx === suggestionIdx }">
                <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0" :style="{ backgroundColor: avatarColor(p.name) }">
                  {{ p.name.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium truncate">{{ p.name }}</div>
                  <div class="text-xs text-gray-400">{{ p.code }} - {{ p.size }}/{{ p.color }}</div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-sm font-semibold">{{ fmt(p.selling_price) }} Ks</div>
                  <div class="text-xs" :class="p.stock_qty > 5 ? 'text-green-600' : p.stock_qty > 0 ? 'text-orange-500' : 'text-red-500'">
                    Stock: {{ p.stock_qty }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Cart -->
          <div v-if="cart.length" class="mb-4">
            <div class="flex justify-between items-center mb-2">
              <h4 class="text-sm font-semibold text-gray-600">Cart ({{ cart.length }} items)</h4>
              <button @click="clearCart" class="text-xs text-red-500 hover:text-red-700 hover:underline">🗑 Clear Cart</button>
            </div>
            <div class="space-y-2">
              <div v-for="(item,i) in cart" :key="i" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border">
                <div class="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-xs flex-shrink-0" :style="{ backgroundColor: avatarColor(item.name) }">
                  {{ item.name.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium truncate">{{ item.name }}</div>
                  <div class="text-xs text-gray-400">{{ item.size }}/{{ item.color }}</div>
                </div>
                <div class="flex items-center gap-1">
                  <button @click="decQty(i)" class="w-7 h-7 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 text-sm">−</button>
                  <input v-model.number="item.qty" min="1" type="number" class="w-14 text-center border rounded px-1 py-1 text-sm" @change="calcTotal" />
                  <button @click="incQty(i)" class="w-7 h-7 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 text-sm">+</button>
                </div>
                <div class="text-right flex-shrink-0 w-20">
                  <div class="text-xs text-gray-400">{{ fmt(item.unit_price) }}</div>
                  <div class="text-sm font-semibold">{{ fmt(item.qty*item.unit_price) }} Ks</div>
                </div>
                <button @click="cart.splice(i,1);calcTotal()" class="text-red-400 hover:text-red-600 ml-1">✕</button>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <div class="text-4xl mb-2">🛒</div>
            <p class="text-sm">No items yet. Search & add products above.</p>
          </div>

          <!-- Totals -->
          <div v-if="cart.length" class="border-t pt-3 mt-3 space-y-3">
            <div class="flex justify-between text-sm"><span>Subtotal</span><span class="font-medium">{{ fmt(subtotal) }} Ks</span></div>
            <div class="flex justify-between text-sm items-center gap-2">
              <span>Discount</span>
              <div class="flex items-center gap-1">
                <input v-model.number="discVal" type="number" min="0" class="input-field w-20 text-right" @change="calcTotal" />
                <select v-model="discType" class="input-field w-16 text-xs" @change="calcTotal"><option value="flat">Ks</option><option value="percent">%</option></select>
              </div>
            </div>
            <div class="flex justify-between font-bold text-lg border-t pt-2"><span>Total</span><span class="text-primary-600">{{ fmt(grandTotal) }} Ks</span></div>

            <!-- Payment Method / Split Payment -->
            <div>
              <label class="flex items-center gap-2 text-sm font-medium mb-2">
                <input type="checkbox" v-model="splitPayment" class="rounded" />
                <span>Split Payment</span>
              </label>

              <!-- Single Payment -->
              <div v-if="!splitPayment">
                <select v-model="payMethod" class="input-field w-full"><option>Cash</option><option>KPay</option><option>WavePay</option><option>Bank Transfer</option><option>Credit</option></select>
                <input v-model.number="paidAmt" type="number" min="0" class="input-field mt-2" placeholder="Paid amount (default: full)" />
              </div>

              <!-- Split Payment Rows -->
              <div v-else class="space-y-2">
                <div v-for="(row, i) in splitRows" :key="i" class="flex gap-2 items-center">
                  <select v-model="row.method" class="input-field flex-1"><option>Cash</option><option>KPay</option><option>WavePay</option><option>Bank Transfer</option></select>
                  <input v-model.number="row.amount" type="number" min="0" class="input-field w-28 text-right" @input="calcSplitTotal" />
                  <button @click="removeSplitRow(i)" class="text-red-400 hover:text-red-600" v-if="splitRows.length>1">✕</button>
                </div>
                <div class="flex justify-between items-center text-xs">
                  <button @click="addSplitRow" class="text-primary-600 hover:underline">+ Add method</button>
                  <span>Remaining: <b :class="splitRemaining!==0?'text-red-600':'text-green-600'">{{ fmt(splitRemaining) }} Ks</b></span>
                </div>
              </div>
            </div>

            <div v-if="payMethod==='Credit' || (splitPayment && splitRows.some(r=>r.method==='Credit'))">
              <label class="text-sm font-medium">Customer</label>
              <select v-model="selCustomer" class="input-field"><option value="">Walk-in</option><option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }} (Credit: {{ fmt(c.current_credit) }})</option></select>
            </div>
            <button @click="submitSale" :disabled="submitting" class="btn-primary w-full mt-2">{{ submitting?'Processing...':'Complete Sale' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- View Sale Modal -->
    <div v-if="viewing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="viewing=null">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[80vh] overflow-auto">
        <h3 class="text-lg font-bold mb-3">Invoice: {{ viewing.invoice_number }}</h3>
        <div class="text-sm space-y-1 mb-4">
          <p>Date: {{ fmtDate(viewing.sale_date) }}</p>
          <p>Customer: {{ viewing.customer_name || 'Walk-in' }}</p>
          <p>Payment: {{ viewing.payment_method }} | Status: {{ viewing.payment_status }}</p>
          <div v-if="viewing.payment_breakdown && viewing.payment_breakdown.length" class="mt-2 bg-gray-50 rounded p-2">
            <p class="text-xs text-gray-500 mb-1 font-medium">Payment Breakdown:</p>
            <div v-for="(pb, i) in viewing.payment_breakdown" :key="i" class="flex justify-between text-xs">
              <span>{{ pb.method }}</span><span class="font-medium">{{ fmt(pb.amount) }} Ks</span>
            </div>
          </div>
        </div>
        <table class="w-full text-sm"><thead><tr class="border-b text-left"><th class="p-2">Item</th><th class="p-2">Qty</th><th class="p-2 text-right">Price</th><th class="p-2 text-right">Total</th></tr></thead>
          <tbody><tr v-for="it in viewing.items" :key="it.id" class="border-b">
            <td class="p-2">{{ it.product_name }} ({{ it.size }}/{{ it.color }})</td>
            <td class="p-2">{{ it.qty }}</td><td class="p-2 text-right">{{ fmt(it.unit_price) }}</td><td class="p-2 text-right">{{ fmt(it.total_price) }}</td>
          </tr></tbody></table>
        <div class="text-right mt-3 font-bold">Total: {{ fmt(viewing.total_amount) }} Ks</div>
        <button @click="viewing=null" class="btn-secondary mt-4 w-full">Close</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'; import api from '../api'
const sales=ref([]); const total=ref(0); const dateFilter=ref(''); const dateTo=ref(''); const statusFilter=ref('')
const showSaleForm=ref(false); const productSearch=ref(''); const suggestionResults=ref([]); const showSuggestions=ref(false); const suggestionIdx=ref(-1)
const cart=ref([]); const searchInput=ref(null)
const discVal=ref(0); const discType=ref('flat'); const payMethod=ref('Cash'); const paidAmt=ref(0); const selCustomer=ref('')
const customers=ref([]); const submitting=ref(false); const viewing=ref(null)
const splitPayment=ref(false); const splitRows=ref([{method:'Cash',amount:0}])

let searchTimer = null

function fmt(v){return v?Number(v).toLocaleString():'0'}
function fmtDate(d){if(!d)return'';return new Date(d).toLocaleDateString()}
function avatarColor(name){const colors=['#6366f1','#8b5cf6','#ec4899','#f43f5e','#f97316','#eab308','#22c55e','#14b8a6','#06b6d4','#3b82f6'];let hash=0;for(let i=0;i<(name||'A').length;i++)hash=(hash*31+(name||'A').charCodeAt(i))&0xfffffff;return colors[hash%colors.length]}
const subtotal=computed(()=>cart.value.reduce((s,i)=>s+i.qty*i.unit_price,0))
const grandTotal=computed(()=>{let d=discVal.value;if(discType.value==='percent')d=subtotal.value*d/100;return Math.max(0,subtotal.value-d)})
const splitTotal=computed(()=>splitRows.value.reduce((s,r)=>s+(r.amount||0),0))
const splitRemaining=computed(()=>grandTotal.value-splitTotal.value)

function incQty(i){cart.value[i].qty++;calcTotal()}
function decQty(i){if(cart.value[i].qty>1){cart.value[i].qty--;calcTotal()}}
function clearCart(){cart.value=[];discVal.value=0;paidAmt.value=0;splitRows.value=[{method:'Cash',amount:0}]}

async function load(){
  const p={};if(dateFilter.value)p.date_from=dateFilter.value;if(dateTo.value)p.date_to=dateTo.value;if(statusFilter.value)p.payment_status=statusFilter.value
  const {data}=await api.get('/sales',{params:p});sales.value=data.items;total.value=data.total
}

async function searchProducts(){
  if(!productSearch.value)return
  const {data}=await api.get('/products',{params:{search:productSearch.value,limit:15}})
  const prods=data.items;suggestionResults.value=[]
  for(const p of prods){
    const {data:v}=await api.get(`/products/${p.id}/variants`)
    for(const vr of v){if(vr.stock_qty>0)suggestionResults.value.push({...vr,name:p.name,code:p.code,selling_price:p.selling_price,product_id:p.id})}
  }
}

function onSearchInput(){
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!productSearch.value) { suggestionResults.value = []; showSuggestions.value = false; return }
    await searchProducts()
    showSuggestions.value = true
    suggestionIdx.value = -1
  }, 300)
}

function onSearchKeydown(e){
  if (!showSuggestions.value) return
  if (e.key === 'ArrowDown') { e.preventDefault(); suggestionIdx.value = Math.min(suggestionIdx.value + 1, suggestionResults.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); suggestionIdx.value = Math.max(suggestionIdx.value - 1, -1) }
  else if (e.key === 'Enter') {
    e.preventDefault()
    if (suggestionIdx.value >= 0 && suggestionIdx.value < suggestionResults.value.length) {
      addToCart(suggestionResults.value[suggestionIdx.value])
    } else { searchProducts() }
  }
  else if (e.key === 'Escape') { showSuggestions.value = false }
}

function onSearchBlur(){ setTimeout(() => { showSuggestions.value = false }, 200) }
function openSuggestions(){ if (suggestionResults.value.length) showSuggestions.value = true }

function addToCart(p){
  const ex=cart.value.find(i=>i.variant_id===p.id)
  if(ex){ex.qty++}else{cart.value.push({variant_id:p.id,name:p.name,size:p.size,color:p.color,qty:1,unit_price:p.selling_price})}
  suggestionResults.value=[];productSearch.value='';showSuggestions.value=false;calcTotal()
}

function calcTotal(){} // reactive

function calcSplitTotal(){
  if(splitPayment.value && splitRows.value.length===1){splitRows.value[0].amount=grandTotal.value}
}

function addSplitRow(){ splitRows.value.push({method:'Cash',amount:0}) }
function removeSplitRow(i){ if(splitRows.value.length>1) splitRows.value.splice(i,1) }

async function newSale(){
  showSaleForm.value=true;cart.value=[];discVal.value=0;paidAmt.value=0;selCustomer.value=''
  splitPayment.value=false;splitRows.value=[{method:'Cash',amount:0}]
  productSearch.value='';suggestionResults.value=[];showSuggestions.value=false
  const {data}=await api.get('/customers',{params:{limit:200}});customers.value=data.items
}

async function submitSale(){
  if(!cart.value.length)return
  if(splitPayment.value && Math.abs(splitRemaining.value) > 0.01){ alert('Split payment amounts must equal total!'); return }
  submitting.value=true
  try{
    const payload={
      items:cart.value.map(i=>({variant_id:i.variant_id,qty:i.qty,unit_price:i.unit_price})),
      discount_amount:discVal.value,discount_type:discType.value,
      payment_method:splitPayment.value ? 'Split' : payMethod.value,
      paid_amount:splitPayment.value ? splitTotal.value : (paidAmt.value||grandTotal.value)
    }
    if(splitPayment.value){ payload.payment_breakdown = splitRows.value.filter(r=>r.amount>0) }
    if(selCustomer.value)payload.customer_id=selCustomer.value
    await api.post('/sales',payload)
    showSaleForm.value=false;await load()
  }catch(e){alert(e.response?.data?.detail||'Sale failed')}
  finally{submitting.value=false}
}

// Auto-fill single split row
watch(grandTotal, (v) => { if(splitPayment.value && splitRows.value.length===1 && splitRows.value[0].amount===0) splitRows.value[0].amount=v })

async function viewSale(id){const {data}=await api.get(`/sales/${id}`);viewing.value=data}
async function voidSale(id){if(confirm('Void this sale? Stock will be returned.')){await api.put(`/sales/${id}/void`);await load()}}
onMounted(load)
</script>