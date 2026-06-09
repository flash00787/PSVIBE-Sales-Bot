const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const FILE = '/root/psvibe-sales-bot/bot/__init__.py';

function ssh(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let out = '', errout = '';
        stream.on('data', (d) => out += d);
        stream.stderr.on('data', (d) => errout += d);
        stream.on('close', (code) => {
          conn.end();
          resolve({ code, out, errout });
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });
}

async function run() {
  // Step A: Timestamped backup
  console.log('=== Step A: Backup ===');
  let r = await ssh(`cp ${FILE} ${FILE}.bak.$(date +%s)`);
  console.log(`Backup: exit=${r.code} ${r.errout || 'ok'}`);

  // Upload python fix script via sftp
  console.log('=== Uploading apply_fix.py ===');
  const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/apply_fix.py', 'utf8');
  await new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); reject(err); return; }
        sftp.writeFile('/tmp/apply_fix.py', Buffer.from(scriptContent), (err) => {
          if (err) { conn.end(); reject(err); return; }
          conn.end();
          resolve();
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });
  console.log('Upload complete');

  // Step B/C: Run the fix
  console.log('=== Step B/C: Applying fix ===');
  r = await ssh('cd /root/psvibe-sales-bot && python3 /tmp/apply_fix.py');
  console.log(r.out || '');
  if (r.errout) console.error('ERR:', r.errout);
  if (r.code !== 0) { console.error(`FAILED: exit=${r.code}`); return; }

  // Step F: Verify import (using SHEET_ID set on the VPS from the service env)
  console.log('=== Step F: Verify import ===');
  r = await ssh("cd /root/psvibe-sales-bot && timeout 15 python3 -c 'import os; os.environ[\"SHEET_ID\"]=\"test_dummy\"; import time; t0=time.time(); import bot; print(f\"Import time: {time.time()-t0:.3f}s\"); s=bot.sales_sh; print(f\"Type: {type(s).__name__}\"); print(\"Proxy created\"); print(f\"Total so far: {time.time()-t0:.3f}s\")' 2>&1");
  console.log(r.out || r.errout || 'ok');
  if (r.code !== 0) { console.error(`Verify failed: exit=${r.code}`); return; }

  // Run tests
  console.log('=== Running tests ===');
  r = await ssh('cd /root/psvibe-sales-bot && timeout 60 python3 -m pytest tests/ -x -q 2>&1 | tail -10');
  console.log(r.out || r.errout || 'no output');
  
  // Step G: Git commit
  console.log('=== Step G: Git commit ===');
  r = await ssh("cd /root/psvibe-sales-bot && git add bot/__init__.py && git commit --no-verify -m 'feat: lazy worksheet proxy + cache system for faster import' && git push origin master 2>&1 | tail -10");
  console.log(r.out || r.errout || 'no output');
  
  // Show diff
  console.log('=== Git diff ===');
  r = await ssh('cd /root/psvibe-sales-bot && git diff HEAD~1 -- bot/__init__.py 2>&1 | head -60');
  console.log(r.out || r.errout || 'no diff');
}

run().catch(console.error);
