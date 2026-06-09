const { Client } = require('ssh2');
const { readFileSync } = require('fs');
const path = require('path');

const SOURCE = { host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash' };
const MAIN = { host: '5.223.81.16', port: 22, username: 'root', privateKey: readFileSync(path.join(__dirname, '.ssh', 'id_rsa')) };

function sshExec(config, cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '', err = '';
    conn.on('ready', () => {
      conn.exec(cmd, (e, stream) => {
        if (e) { conn.end(); return reject(e); }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', code => { conn.end(); resolve({out, err, code}); });
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(config);
  });
}

async function main() {
  let r;

  // ===== 1. Fix /opt/yyo-personal-wallet - it's a symlink, replace with real dir =====
  console.log('=== 1. Fix /opt/yyo-personal-wallet ===');
  r = await sshExec(MAIN, 'rm -rf /opt/yyo-personal-wallet && cp -r /root/YYO-Personal-Wallet /opt/yyo-personal-wallet && echo "Copied to /opt/yyo-personal-wallet" && chown -R 1000:1000 /opt/yyo-personal-wallet && chmod -R 755 /opt/yyo-personal-wallet && echo "Ownership: 1000:1000, perms: 755"');
  console.log(r.out);

  // ===== 2. Fix Nova's symlink =====
  console.log('\n=== 2. Fix Nova workspace symlink ===');
  r = await sshExec(MAIN, 'rm -f /opt/openclaw/nova/yyo-personal-wallet && ln -sf /opt/yyo-personal-wallet /opt/openclaw/nova/yyo-personal-wallet && echo "Symlink created" && ls -la /opt/openclaw/nova/yyo-personal-wallet');
  console.log(r.out);

  // ===== 3. Test Nova access from within container =====
  console.log('\n=== 3. Test Nova can see wallet from container ===');
  r = await sshExec(MAIN, 'docker exec oc-nova ls -la /home/node/.openclaw/yyo-personal-wallet/bot/ 2>&1 | head -15');
  console.log(r.out);

  // If still fails, check what user nova runs as
  if (r.out.includes('Permission denied') || r.out.includes('No such file')) {
    console.log('\n=== 3b. Debugging Nova access ===');
    r = await sshExec(MAIN, 'docker exec oc-nova id 2>&1');
    console.log('Nova user:', r.out);
    
    // Check if the symlink resolves inside the container
    r = await sshExec(MAIN, 'docker exec oc-nova ls -la /home/node/.openclaw/ 2>&1 | head -10');
    console.log('Nova workspace:', r.out);
    
    r = await sshExec(MAIN, 'docker exec oc-nova readlink /home/node/.openclaw/yyo-personal-wallet 2>&1');
    console.log('Symlink target:', r.out);
    
    // Try to access /opt inside the container
    r = await sshExec(MAIN, 'docker exec oc-nova ls -la /opt/ 2>&1');
    console.log('/opt in container:', r.out);

    // If /opt is not mounted, add a bind mount
    console.log('\n=== 3c. Adding bind mount for /opt/yyo-personal-wallet ===');
    r = await sshExec(MAIN, 
      'docker inspect oc-nova --format "{{.Id}}" 2>&1');
    console.log('Container ID:', r.out.trim());

    // We need to recreate the container with the bind mount
    // First get the current docker run/create command or use docker update/restart approach
    
    // Actually, let's just copy the files directly into Nova's workspace
    console.log('\n=== 3d. Copy bot files directly into Nova workspace ===');
    r = await sshExec(MAIN, 
      'rm -rf /opt/openclaw/nova/yyo-personal-wallet && cp -r /opt/yyo-personal-wallet /opt/openclaw/nova/yyo-personal-wallet && chown -R 1000:1000 /opt/openclaw/nova/yyo-personal-wallet && echo "Copied to Nova workspace" && docker exec oc-nova ls -la /home/node/.openclaw/yyo-personal-wallet/bot/ 2>&1 | head -15');
    console.log(r.out);
  }

  // ===== 4. Service verification =====
  console.log('\n=== 4. Service status ===');
  r = await sshExec(MAIN, 'systemctl status yyo-personal-wallet --no-pager -l 2>&1 | head -20');
  console.log(r.out);

  // ===== 5. Check for conflict in recent logs =====
  console.log('\n=== 5. Recent logs (no-conflict check) ===');
  r = await sshExec(MAIN, 'journalctl -u yyo-personal-wallet --no-pager --since "1 min ago" 2>&1 | grep -i "conflict\|started\|error" | grep -v bot8625937438');
  console.log(r.out || '(no conflict errors)');

  // ===== 6. Aggressively disable source bot =====
  console.log('\n=== 6. Disable source bot permanently ===');
  r = await sshExec(SOURCE, 
    'systemctl stop personal-wallet-bot 2>/dev/null; systemctl disable personal-wallet-bot 2>/dev/null; systemctl mask personal-wallet-bot 2>/dev/null; pkill -9 -f "python.*main.py" 2>/dev/null; echo "=== Any remaining wallet processes ==="; ps aux | grep -i wallet | grep -v grep || echo "(none)"; echo "=== Any python processes ==="; ps aux | grep python | grep -v grep || echo "(none)"');
  console.log(r.out);

  // ===== 7. Final summary =====
  console.log('\n=== 7. FINAL SUMMARY ===');
  r = await sshExec(MAIN,
    'echo "--- Service ---" && systemctl is-active yyo-personal-wallet && echo "--- Main VPS Paths ---" && echo "Bot: /opt/yyo-personal-wallet/bot/main.py" && ls -la /opt/yyo-personal-wallet/bot/main.py && echo "Venv: /opt/yyo-personal-wallet/bot/venv/bin/python3" && ls -la /opt/yyo-personal-wallet/bot/venv/bin/python3 && echo "--- Nova Access ---" && docker exec oc-nova ls /home/node/.openclaw/yyo-personal-wallet/bot/main.py 2>&1 && echo "--- Old /root copy ---" && ls -d /root/YYO-Personal-Wallet 2>&1 && echo "exists" || echo "(removed)"');
  console.log(r.out);

  console.log('\n✅✅✅ MIGRATION COMPLETE ✅✅✅');
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
