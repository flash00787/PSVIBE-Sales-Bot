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
  // Step 3: Add route - use base64 encoded Python
  console.log('=== Step 3: Fix router ===');
  const routeScript = `p='/root/psvibe-dashboard/src/router/index.ts'
c=open(p).read()
idx=c.find("path: '/coupons'")
end=c.find('},', c.find('title: "Coupons"', idx))
nc=c[:end+2]+"\\n    {\\n      path: '/topups',\\n      name: 'topups',\\n      component: () => import('../views/TopUpLogs.vue'),\\n      meta: { requiresAuth: true, title: 'TopUp Logs' },\\n    },\\n"+c[end+2:]
open(p,'w').write(nc)
print('OK')`;
  let r = await sshExec(`echo ${Buffer.from(routeScript).toString('base64')} | base64 -d | python3`);
  console.log('Router:', r.stdout || r.stderr, r.code);

  r = await sshExec('grep -c topups /root/psvibe-dashboard/src/router/index.ts');
  console.log('Router matches:', r.stdout);

  // Step 4: Add nav link
  console.log('\n=== Step 4: Fix nav link ===');
  const navScript = `p='/root/psvibe-dashboard/src/components/AppLayout.vue'
c=open(p).read()
idx=c.find("path: '/coupons', label: 'Coupons'")
end=c.find('},', idx)
newItem='  { path: \\'/topups\\', label: \\'TopUp Logs\\', icon: \\'<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>\\' },'
nc=c[:end+2]+'\\n'+newItem+'\\n'+c[end+2:]
open(p,'w').write(nc)
print('OK')`;
  r = await sshExec(`echo ${Buffer.from(navScript).toString('base64')} | base64 -d | python3`);
  console.log('Nav link:', r.stdout || r.stderr, r.code);

  r = await sshExec('grep -c topups /root/psvibe-dashboard/src/components/AppLayout.vue');
  console.log('Nav matches:', r.stdout);

  // Verify both files
  r = await sshExec('grep -A3 topups /root/psvibe-dashboard/src/router/index.ts');
  console.log('\nRouter verify:', r.stdout);
  
  r = await sshExec('grep -B1 -A1 topups /root/psvibe-dashboard/src/components/AppLayout.vue');
  console.log('Nav verify:', r.stdout);

  // Step 5: Rebuild & deploy
  console.log('\n=== Step 5: Rebuild ===');
  r = await sshExec('cd /root/psvibe-dashboard && npm run build 2>&1', 120);
  console.log('Build:', r.code === 0 ? 'SUCCESS' : 'FAILED');
  const buildLines = r.stdout.split('\n').filter(l => l.includes('TopUp') || l.includes('topup') || l.includes('dist') || l.includes('error') || l.includes('✓') || l.includes('KB'));
  console.log(buildLines.join('\n').slice(-500));
  if (r.code !== 0) {
    console.log('Full output:', r.stdout.slice(-2000));
    return;
  }

  r = await sshExec('cp -r /root/psvibe-dashboard/dist/* /root/psvibe_api_server/dashboard-dist/');
  console.log('Deploy:', r.code === 0 ? 'OK' : 'FAILED');

  r = await sshExec('systemctl restart psvibe-api && systemctl is-active psvibe-api');
  console.log('API:', r.stdout);

  // Final verification - check TopUpLogs is in dist
  r = await sshExec('ls -la /root/psvibe_api_server/dashboard-dist/assets/ | grep -i topup');
  console.log('TopUp in dist:', r.stdout || '(not found - checking all...)');
  if (!r.stdout) {
    r = await sshExec('ls /root/psvibe_api_server/dashboard-dist/assets/');
    console.log('All assets:', r.stdout.slice(-500));
    r = await sshExec('find /root/psvibe_api_server/dashboard-dist/ -name "*opUp*" -o -name "*topup*"');
    console.log('Find TopUp:', r.stdout);
  }

  console.log('\n✅ DONE — URL path: /#/topups');
}

run().catch(e => console.error('FATAL:', e.message));
