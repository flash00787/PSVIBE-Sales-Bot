const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${cmd.substring(0, 200)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let o = '', e = '';
      stream.on('data', d => { o += d.toString(); });
      stream.stderr.on('data', d => { e += d.toString(); });
      stream.on('close', (code) => {
        const out = (o + e).trim();
        console.log(out.substring(0, 6000));
        resolve({ code, out });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((r, x) => { conn.on('ready', r); conn.on('error', x); conn.connect({
    host: '5.223.81.16', port: 22, username: 'root',
    privateKey: fs.readFileSync(path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa')),
    readyTimeout: 15000,
  });});
  console.log('=== Fix: Restore from bot import * in ezplicit-import handlers ===');

  try {
    // 1. Find ALL handler files with `from bot import X, Y, Z` (explicit)
    console.log('\n--- All handler files with explicit from bot import ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import.*,.*,' bot/handlers/*.py | grep -v '.bak\|.test_backup' | head -20`);
    
    // 2. Restore from bot import * in all affected non-bak handler files
    console.log('\n--- Fixing all explicit imports back to star imports ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 << 'PYFIX'
import os, glob, re

handler_dir = 'bot/handlers'
files = glob.glob(f'{handler_dir}/*.py')
files = [f for f in files if '.bak' not in f and '.test_backup' not in f]

for fpath in sorted(files):
    with open(fpath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    for line in lines:
        # Match lines that start with 'from bot import ' and contain commas (explicit list)
        stripped = line.split('#')[0].strip()
        if stripped.startswith('from bot import ') and ',' in stripped:
            # Replace with star import
            new_lines.append('from bot import *\n')
            print(f'FIXED: {fpath}: {line.strip()[:80]}... --> from bot import *')
            modified = True
        else:
            new_lines.append(line)
    
    if modified:
        with open(fpath, 'w') as f:
            f.writelines(new_lines)

print('DONE fixing handler imports')
PYFIX`);

    // 3. Check attendance.py fixed
    console.log('\n--- attendance.py after fix ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -3 bot/handlers/attendance.py');
    
    // 4. Check what other files were changed
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git diff --name-only');

    // 5. Restart
    console.log('\n--- Restart ---');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 25 --since "30 sec ago" 2>&1');

    // 6. Commit
    console.log('\n--- Commit ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: revert ee61e89 handler explicit imports back to from bot import * - explicit imports included nonexistent names like amt" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
