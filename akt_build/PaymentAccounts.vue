<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">💰 Payment Accounts</h2>
      <button @click="openNewAccount" class="btn-primary">+ New Account</button>
    </div>

    <!-- Accounts Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <div v-for="a in accounts" :key="a.id" @click="viewTransactions(a)"
        class="card cursor-pointer hover:shadow-md transition-shadow border-2"
        :class="a.is_active ? 'hover:border-primary-300' : 'opacity-50 border-gray-200'">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="font-bold text-gray-800">{{ a.name }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full"
              :class="a.type==='cash'?'bg-green-100 text-green-700':a.type==='bank'?'bg-blue-100 text-blue-700':'bg-purple-100 text-purple-700'">
              {{ a.type.replace('_',' ') }}
            </span>
          </div>
          <div class="flex gap-1">
            <button @click.stop="editAccount(a)" class="text-gray-400 hover:text-primary-600 text-sm" title="Edit">✏️</button>
          </div>
        </div>
        <p v-if="a.account_number" class="text-xs text-gray-400 mb-2">{{ a.account_number }}</p>
        <div class="text-2xl font-bold" :class="a.balance >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ fmt(a.balance) }} Ks
        </div>
        <div v-if="!a.is_active" class="text-xs text-red-500 mt-1">Inactive</div>
      </div>
    </div>

    <!-- Transactions Modal -->
    <div v-if="selectedAccount" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="selectedAccount=null">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div class="p-4 border-b flex justify-between items-center">
          <div>
            <h3 class="text-lg font-bold">{{ selectedAccount.name }}</h3>
            <p class="text-xs text-gray-400">{{ selectedAccount.type }} | Balance: <b :class="selectedAccount.balance>=0?'text-green-600':'text-red-600'">{{ fmt(selectedAccount.balance) }} Ks</b></p>
          </div>
          <div class="flex gap-2">
            <button @click="openManualTxn" class="text-xs btn-secondary py-1 px-3">+ Manual Txn</button>
            <button @click="selectedAccount=null" class="text-gray-400 hover:text-gray-600 text-xl">✕</button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-4">
          <table v-if="transactions.length" class="w-full text-sm">
            <thead><tr class="border-b text-left text-gray-500 text-xs">
              <th class="p-2">Date</th><th class="p-2">Type</th><th class="p-2">Ref</th><th class="p-2 text-right">Amount</th><th class="p-2 text-right">Balance</th><th class="p-2">Description</th>
            </tr></thead>
            <tbody>
              <tr v-for="t in transactions" :key="t.id" class="border-b hover:bg-gray-50">
                <td class="p-2 text-xs">{{ fmtDate(t.created_at) }}</td>
                <td class="p-2">
                  <span class="text-xs px-2 py-0.5 rounded-full"
                    :class="t.transaction_type==='sale'?'bg-green-100 text-green-700':t.transaction_type==='purchase'?'bg-red-100 text-red-700':t.transaction_type==='deposit'?'bg-blue-100 text-blue-700':'bg-orange-100 text-orange-700'">
                    {{ t.transaction_type }}
                  </span>
                </td>
                <td class="p-2 text-xs text-gray-400">{{ t.reference_type }} #{{ t.reference_id || '-' }}</td>
                <td class="p-2 text-right font-medium" :class="t.transaction_type==='purchase'||t.transaction_type==='withdrawal'?'text-red-600':'text-green-600'">
                  {{ t.transaction_type==='purchase'||t.transaction_type==='withdrawal'?'-':'' }}{{ fmt(t.amount) }} Ks
                </td>
                <td class="p-2 text-right text-xs">{{ fmt(t.balance_after) }} Ks</td>
                <td class="p-2 text-xs text-gray-500">{{ t.description || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center py-8 text-gray-400">No transactions yet.</div>
        </div>
        <div class="p-3 border-t">
          <button @click="selectedAccount=null" class="btn-secondary w-full">Close</button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Account Modal -->
    <div v-if="showAccountForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showAccountForm=false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-bold mb-4">{{ editingAccount ? 'Edit' : 'New' }} Account</h3>
        <div class="space-y-3">
          <div><label class="text-sm font-medium">Name</label><input v-model="accountForm.name" class="input-field" placeholder="e.g. Cash Register" /></div>
          <div>
            <label class="text-sm font-medium">Type</label>
            <select v-model="accountForm.type" class="input-field">
              <option value="cash">Cash</option>
              <option value="bank">Bank</option>
              <option value="mobile_wallet">Mobile Wallet</option>
            </select>
          </div>
          <div><label class="text-sm font-medium">Account Number</label><input v-model="accountForm.account_number" class="input-field" placeholder="Optional" /></div>
          <div><label class="text-sm font-medium">Opening Balance</label><input v-model.number="accountForm.balance" type="number" class="input-field" /></div>
          <div v-if="editingAccount" class="flex items-center gap-2">
            <input type="checkbox" v-model="accountForm.is_active" class="rounded" id="isActive" />
            <label for="isActive" class="text-sm">Active</label>
          </div>
          <button @click="saveAccount" class="btn-primary w-full">{{ editingAccount ? 'Update' : 'Create' }}</button>
        </div>
        <button @click="showAccountForm=false" class="btn-secondary w-full mt-2">Cancel</button>
      </div>
    </div>

    <!-- Manual Transaction Modal -->
    <div v-if="showManualTxn" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showManualTxn=false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-bold mb-4">Manual Transaction - {{ selectedAccount.name }}</h3>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium">Type</label>
            <select v-model="manualTxn.transaction_type" class="input-field">
              <option value="deposit">Deposit (+)</option>
              <option value="withdrawal">Withdrawal (-)</option>
            </select>
          </div>
          <div><label class="text-sm font-medium">Amount</label><input v-model.number="manualTxn.amount" type="number" min="0" step="0.01" class="input-field" /></div>
          <div><label class="text-sm font-medium">Description</label><input v-model="manualTxn.description" class="input-field" /></div>
          <button @click="saveManualTxn" :disabled="savingTxn" class="btn-primary w-full">{{ savingTxn?'Saving...':'Record' }}</button>
        </div>
        <button @click="showManualTxn=false" class="btn-secondary w-full mt-2">Cancel</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'; import api from '../api'
const accounts=ref([]); const selectedAccount=ref(null); const transactions=ref([])
const showAccountForm=ref(false); const editingAccount=ref(null)
const accountForm=ref({name:'',type:'cash',account_number:'',balance:0,is_active:true})
const showManualTxn=ref(false); const manualTxn=ref({transaction_type:'deposit',amount:0,description:''})
const savingTxn=ref(false)

function fmt(v){return v?Number(v).toLocaleString():'0'}
function fmtDate(d){if(!d)return'';const dt=new Date(d);return dt.toLocaleDateString()+' '+dt.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}

async function loadAccounts(){const {data}=await api.get('/payment-accounts');accounts.value=data.items}

function openNewAccount(){editingAccount.value=null;accountForm.value={name:'',type:'cash',account_number:'',balance:0,is_active:true};showAccountForm.value=true}

function editAccount(a){editingAccount.value=a;accountForm.value={name:a.name,type:a.type,account_number:a.account_number||'',balance:0,is_active:!!a.is_active};showAccountForm.value=true}

async function saveAccount(){
  try{
    if(editingAccount.value){
      await api.put(`/payment-accounts/${editingAccount.value.id}`,accountForm.value)
    }else{
      await api.post('/payment-accounts',accountForm.value)
    }
    showAccountForm.value=false;await loadAccounts()
  }catch(e){alert(e.response?.data?.detail||'Failed')}
}

async function viewTransactions(a){
  selectedAccount.value=a
  const {data}=await api.get(`/payment-accounts/${a.id}/transactions`)
  transactions.value=data.items
}

function openManualTxn(){manualTxn.value={transaction_type:'deposit',amount:0,description:''};showManualTxn.value=true}

async function saveManualTxn(){
  if(!manualTxn.value.amount)return;savingTxn.value=true
  try{
    await api.post('/payment-accounts/transactions',{...manualTxn.value,account_id:selectedAccount.value.id})
    showManualTxn.value=false;await loadAccounts()
    // Refresh transactions
    const {data}=await api.get(`/payment-accounts/${selectedAccount.value.id}/transactions`)
    transactions.value=data.items
    selectedAccount.value = accounts.value.find(a=>a.id===selectedAccount.value.id)
  }catch(e){alert(e.response?.data?.detail||'Failed')}finally{savingTxn.value=false}
}

onMounted(loadAccounts)
</script>