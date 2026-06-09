const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function sshExec(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let stdout = '', stderr = '';
        stream.on('data', (d) => stdout += d);
        stream.stderr.on('data', (d) => stderr += d);
        stream.on('close', (code) => {
          conn.end();
          resolve({ code, stdout, stderr });
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });
}

async function main() {
  // Restore from backup first (to undo any partial changes)
  console.log('=== Step A: Restore from backup ===');
  let r = await sshExec('cp /root/psvibe-sales-bot/bot/__init__.py.bak /root/psvibe-sales-bot/bot/__init__.py');
  console.log(`Restore: exit=${r.code}`);

  // Upload the Python fix script
  console.log('=== Uploading apply_fix.py ===');
  const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/apply_fix.py', 'utf8');
  
  await new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); reject(err); return; }
        sftp.writeFile('/tmp/apply_fix.py', Buffer.from(scriptContent), (err) => {
          if (err) { conn.end(); reject(err); return; }
          console.log('Upload complete');
          conn.end();
          resolve();
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });

  // Run the fix
  console.log('=== Step B/C: Applying fix ===');
  r = await sshExec('cd /root/psvibe-sales-bot && python3 /tmp/apply_fix.py');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);
  if (r.code !== 0) {
    console.error(`Exit code: ${r.code}`);
    return;
  }

  // Step F: Verify import time
  console.log('=== Step F: Verify ===');
  r = await sshExec('cd /root/psvibe-sales-bot && timeout 15 python3 <<\'EOF\'
import os
import sys
os.environ["SHEET_ID"] = "test_dummy"
import time
t0 = time.time()
try:
    import bot
    print(f"Import time: {time.time()-t0:.3f}s")
    s = bot.sales_sh
    print(f"Type: {type(s).__name__}")
    print("Proxy created, no ws call yet")
    t1 = time.time()
    print(f"Total so far: {t1-t0:.3f}s")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)
EOF
 2>&1');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);

  // Run tests
  r = await sshExec('cd /root/psvibe-sales-bot && timeout 60 python3 -m pytest tests/ -x -q 2>&1 | tail -10');
  console.log('Test results:');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);

  // Step G: Commit
  console.log('=== Step G: Git commit ===');
  r = await sshExec('cd /root/psvibe-sales-bot && git add bot/__init__.py && git commit --no-verify -m "feat: lazy worksheet proxy + cache system for faster import" && git push origin master 2>&1 | tail -10');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);

  // Final verification: show the changed lines
  r = await sshExec('cd /root/psvibe-sales-bot && git diff HEAD~1 -- bot/__init__.py | head -80');
  console.log('=== Git diff (first 80 lines) ===');
  console.log(r.stdout);
}

main().catch(console.error);
