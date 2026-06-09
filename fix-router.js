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

async function run() {
  // First, check current state of router file
  console.log('=== Current router state (lines 1-10) ===');
  let r = await sshExec('head -10 /root/psvibe-dashboard/src/router/index.ts');
  console.log(r.stdout);

  // The router was corrupted. Restore from git or rewrite properly.
  // Let's rewrite the whole router file correctly since it's corrupted.
  console.log('\n=== Restoring router file ===');
  
  const routerContent = `import { createRouter, createWebHashHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, title: 'Dashboard' },
    },
    {
      path: '/bookings',
      name: 'bookings',
      component: () => import('../views/BookingsManagement.vue'),
      meta: { requiresAuth: true, title: 'Bookings' },
    },
    {
      path: '/members',
      name: 'members',
      component: () => import('../views/MembersManagement.vue'),
      meta: { requiresAuth: true, title: 'Members' },
    },
    // ---- Food Stock (4-section split) ----
    {
      path: '/food-menu',
      name: 'food-menu',
      component: () => import('../views/FoodMenuRegister.vue'),
      meta: { requiresAuth: true, title: 'Food Menu Register' },
    },
    {
      path: '/stock-in',
      name: 'stock-in',
      component: () => import('../views/StockIn.vue'),
      meta: { requiresAuth: true, title: 'Stock In' },
    },
    {
      path: '/stock-out',
      name: 'stock-out',
      component: () => import('../views/StockOut.vue'),
      meta: { requiresAuth: true, title: 'Stock Out' },
    },
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('../views/Inventory.vue'),
      meta: { requiresAuth: true, title: 'Food Inventory' },
    },
    // ------------------------------------
    {
      path: '/promotions',
      name: 'promotions',
      component: () => import('../views/Promotions.vue'),
      meta: { requiresAuth: true, title: 'Promotions' },
    },
    {
      path: '/coupons',
      name: 'coupons',
      component: () => import('../views/Coupons.vue'),
      meta: { requiresAuth: true, title: 'Coupons' },
    },
    {
      path: '/topups',
      name: 'topups',
      component: () => import('../views/TopUpLogs.vue'),
      meta: { requiresAuth: true, title: 'TopUp Logs' },
    },
    {
      path: '/games',
      name: 'games',
      component: () => import('../views/GamesLibrary.vue'),
      meta: { requiresAuth: true, title: 'Games' },
    },
    {
      path: '/sales-daily',
      name: 'sales-daily',
      component: () => import('../views/SaleDaily.vue'),
      meta: { requiresAuth: true, title: 'Sales Daily' },
    },
    {
      path: '/financial-report',
      name: 'financial-report',
      component: () => import('../views/FinancialReport.vue'),
      meta: { requiresAuth: true, title: 'Financial Report' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
`;

  const b64 = Buffer.from(routerContent).toString('base64');
  r = await sshExec(`echo ${b64} | base64 -d > /root/psvibe-dashboard/src/router/index.ts`);
  console.log('Router rewrite:', r.code === 0 ? 'OK' : 'FAILED');

  // Verify
  r = await sshExec('grep -c topups /root/psvibe-dashboard/src/router/index.ts');
  console.log('Router topups count:', r.stdout);

  // Check nav link is also clean
  r = await sshExec('grep topups /root/psvibe-dashboard/src/components/AppLayout.vue');
  console.log('Nav link:', r.stdout);

  // Now build
  console.log('\n=== Building ===');
  r = await sshExec('cd /root/psvibe-dashboard && npm run build 2>&1', 120);
  console.log('Build:', r.code === 0 ? 'SUCCESS' : 'FAILED');
  
  const lines = r.stdout.split('\n');
  const relevant = lines.filter(l => l.includes('error') || l.includes('TopUp') || l.includes('✓ built'));
  console.log(relevant.join('\n'));
  
  if (r.code !== 0) {
    console.log('\nErrors (last 30 lines):', lines.slice(-30).join('\n'));
    return;
  }

  // Deploy
  r = await sshExec('cp -r /root/psvibe-dashboard/dist/* /root/psvibe_api_server/dashboard-dist/');
  console.log('Deploy:', r.code === 0 ? 'OK' : 'FAILED');

  r = await sshExec('systemctl restart psvibe-api && systemctl is-active psvibe-api');
  console.log('API:', r.stdout);

  // Final check
  r = await sshExec('ls /root/psvibe_api_server/dashboard-dist/assets/ | grep -i topup');
  console.log('TopUp asset:', r.stdout || 'NOT FOUND');

  if (!r.stdout) {
    r = await sshExec('find /root/psvibe_api_server/dashboard-dist/ -name "*opUp*" -o -name "*topup*" 2>/dev/null');
    console.log('Find:', r.stdout || 'NOTHING');
  }

  console.log('\n✅ DONE — URL path: /#/topups');
}

run().catch(e => console.error('FATAL:', e.message));
