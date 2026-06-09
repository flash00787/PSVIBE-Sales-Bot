const { Client } = require('ssh2');
const fs = require('fs');

const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

function sshExec(cmd, timeout = 30) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let stdout = '', stderr = '';
    const timer = setTimeout(() => { conn.end(); reject(new Error('timeout')); }, timeout * 1000);
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { clearTimeout(timer); conn.end(); return reject(err); }
        stream.on('data', (d) => stdout += d.toString());
        stream.stderr.on('data', (d) => stderr += d.toString());
        stream.on('close', (code) => {
          clearTimeout(timer); conn.end();
          resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code });
        });
      });
    });
    conn.on('error', (e) => { clearTimeout(timer); reject(e); });
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY, readyTimeout: 10000 });
  });
}

const endpointCode = `
@router.get("/topups")
async def dashboard_get_topups(search: str = "", limit: int = 100, offset: int = 0, user: dict = Depends(get_current_user)):
    """Get all topup logs with optional search by member_id."""
    try:
        if search:
            where = "WHERE member_id LIKE %s"
            params = (f"%{search}%",)
        else:
            where = ""
            params = ()
        count = _mysql_query_one(f"SELECT COUNT(*) as total FROM topup_log {where}", params) or {"total": 0}
        rows = _mysql_query(
            f"SELECT id, member_id, amount, mins_added, topup_date, staff_name, payment_method, "
            f"balance_mins_before, balance_mins_after, notes, created_at "
            f"FROM topup_log {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            params + (limit, offset))
        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "member_id": r["member_id"],
                "amount": float(r["amount"]) if r.get("amount") else 0,
                "mins_added": r["mins_added"],
                "topup_date": str(r["topup_date"]) if r.get("topup_date") else "",
                "staff_name": r.get("staff_name", ""),
                "payment_method": r.get("payment_method", ""),
                "balance_before": r.get("balance_mins_before"),
                "balance_after": r.get("balance_mins_after"),
                "notes": r.get("notes", ""),
                "created_at": str(r["created_at"]) if r.get("created_at") else "",
            })
        return {"success": True, "data": items, "total": count["total"]}
    except Exception as e:
        logger.error(f"GET /topups error: {e}")
        return {"success": False, "error": str(e)}
`;

async function run() {
  try {
    // Step 1: Append endpoint (base64 encode to avoid shell escaping issues)
    console.log('=== Step 1: Append API endpoint ===');
    const b64 = Buffer.from(endpointCode).toString('base64');
    let r = await sshExec(`echo ${b64} | base64 -d >> /root/psvibe_api_server/dashboard_routes.py`);
    console.log('Append:', r.code, r.stderr || 'ok');
    
    r = await sshExec('python3 -m py_compile /root/psvibe_api_server/dashboard_routes.py 2>&1');
    console.log('Syntax:', r.stdout || r.stderr || 'OK', r.code);
    
    r = await sshExec('tail -3 /root/psvibe_api_server/dashboard_routes.py');
    console.log('Last lines:', r.stdout);
    
    // Step 2: Create Vue file
    console.log('\n=== Step 2: Create TopUpLogs.vue ===');
    const vueStr = `<script setup lang="ts">
import AppLayout from "@/components/AppLayout.vue"
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const total = ref(0)
const copiedMemberId = ref('')

function formatDate(val: string) {
  if (!val) return '-'
  return new Date(val).toLocaleDateString('my-MM', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatKs(val: number | null) {
  if (val == null) return '-'
  return new Intl.NumberFormat('my-MM').format(val) + ' Ks'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await apiClient.get('/api/dashboard/topups', { params: { search: search.value, limit: 100 } })
    items.value = res.data.data || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('Failed to fetch topup logs:', e)
    items.value = []
    total.value = 0
  } finally { loading.value = false }
}

async function copyMemberId(mid: string) {
  if (!mid) return
  try {
    await navigator.clipboard.writeText(mid)
  } catch {
    const el = document.createElement('textarea')
    el.value = mid
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copiedMemberId.value = mid
  setTimeout(() => { copiedMemberId.value = '' }, 2000)
}

onMounted(fetchData)
</script>

<template>
  <AppLayout title="TopUp Logs">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">Credit Card TopUp Logs</h1>
    </div>

    <div class="flex flex-wrap gap-3 mb-4">
      <input v-model="search" @input="fetchData" placeholder="Search by Member ID..."
        class="w-full md:w-96 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
      <button @click="search = ''; fetchData()"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
        Show All
      </button>
      <span v-if="total > 0" class="self-center text-sm text-gray-500 dark:text-gray-400 ml-2">
        {{ total }} record{{ total !== 1 ? 's' : '' }}
      </span>
    </div>

    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>

    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Member ID</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Amount (Ks)</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Mins Added</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Staff</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Payment</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Bal Before</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Bal After</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Notes</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750">
              <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">{{ item.id }}</td>
              <td class="px-4 py-3 text-sm">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-indigo-600 dark:text-indigo-400">{{ item.member_id || '-' }}</span>
                  <button @click="copyMemberId(item.member_id)"
                          class="text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex-shrink-0"
                          :title="copiedMemberId === item.member_id ? 'Copied!' : 'Copy Member ID'">
                    <svg v-if="copiedMemberId !== item.member_id" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <svg v-else class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                </div>
              </td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ formatKs(item.amount) }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ item.mins_added != null ? item.mins_added : '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.staff_name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ item.payment_method || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ item.balance_before != null ? item.balance_before : '-' }}</td>
              <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">{{ item.balance_after != null ? item.balance_after : '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 max-w-[150px] truncate" :title="item.notes">{{ item.notes || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ formatDate(item.topup_date) }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="10" class="px-4 py-8 text-center text-gray-500">No topup logs found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>`;
    const vueB64 = Buffer.from(vueStr).toString('base64');
    r = await sshExec(`echo ${vueB64} | base64 -d > /root/psvibe-dashboard/src/views/TopUpLogs.vue`);
    console.log('Vue file:', r.code === 0 ? 'OK' : 'FAILED', r.stderr);
    
    r = await sshExec('wc -l /root/psvibe-dashboard/src/views/TopUpLogs.vue');
    console.log('Vue lines:', r.stdout);

    // Step 3: Add route
    console.log('\n=== Step 3: Add route ===');
    r = await sshExec(`python3 -c "
p='/root/psvibe-dashboard/src/router/index.ts'
c=open(p).read()
idx=c.find(\"path: '/coupons'\")
end=c.find('},', c.find('title: \\\"Coupons\\\"', idx))
nc=c[:end+2]+\"\\n    {\\n      path: '/topups',\\n      name: 'topups',\\n      component: () => import('../views/TopUpLogs.vue'),\\n      meta: { requiresAuth: true, title: 'TopUp Logs' },\\n    },\\n\"+c[end+2:]
open(p,'w').write(nc)
print('OK')
"`);
    console.log('Router:', r.stdout || r.stderr, r.code);

    // Step 4: Add nav link
    console.log('\n=== Step 4: Add nav link ===');
    r = await sshExec(`python3 -c "
p='/root/psvibe-dashboard/src/components/AppLayout.vue'
c=open(p).read()
idx=c.find(\"path: '/coupons', label: 'Coupons'\")
end=c.find('},', idx)
nc=c[:end+2]+'\\n  { path: \\'/topups\\', label: \\'TopUp Logs\\', icon: \\'<svg class=\"w-5 h-5\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z\" /></svg>\\' },'+c[end+2:]
open(p,'w').write(nc)
print('OK')
"`);
    console.log('Nav link:', r.stdout || r.stderr, r.code);

    // Verify
    r = await sshExec('grep topups /root/psvibe-dashboard/src/components/AppLayout.vue');
    console.log('Nav verify:', r.stdout);

    // Step 5: Build
    console.log('\n=== Step 5: Build ===');
    r = await sshExec('cd /root/psvibe-dashboard && npm run build 2>&1', 120);
    console.log('Build result:', r.code === 0 ? 'SUCCESS' : 'FAILED');
    if (r.code !== 0) {
      console.log('Build output (last 50 lines):', r.stdout.split('\n').slice(-50).join('\n'));
      if (r.stderr) console.log('Build stderr:', r.stderr);
      return;
    }
    // Show build summary
    const buildLines = r.stdout.split('\n').filter(l => l.includes('dist') || l.includes('error') || l.includes('✓') || l.includes('KB'));
    console.log('Build summary:', buildLines.join('\n').slice(-500));

    // Deploy
    console.log('\n=== Deploying ===');
    r = await sshExec('cp -r /root/psvibe-dashboard/dist/* /root/psvibe_api_server/dashboard-dist/');
    console.log('Copy:', r.code === 0 ? 'OK' : 'FAILED: ' + r.stderr);

    r = await sshExec('systemctl restart psvibe-api');
    console.log('Restart:', r.code === 0 ? 'OK' : 'FAILED: ' + r.stderr);

    r = await sshExec('systemctl is-active psvibe-api');
    console.log('Service status:', r.stdout);

    console.log('\n✅ DONE — URL path: /#/topups');
  } catch(e) {
    console.error('FATAL:', e.message);
  }
}
run();
