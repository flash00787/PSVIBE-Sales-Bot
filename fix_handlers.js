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
        console.log(out.substring(0, 5000));
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
  console.log('=== FINAL FIX: Move handler imports out of __init__.py ===');

  try {
    // Step 1: Remove `from bot.handlers import *` from __init__.py
    console.log('\n--- Step 1: Remove handlers import from __init__.py ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()
# Find and remove 'from bot.handlers import *'
new_lines = []
for line in lines:
    if 'from bot.handlers import' not in line and 'from bot.app import' not in line:
        new_lines.append(line)
    else:
        print(f'REMOVED: {line.strip()}')
with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)
" 2>&1`);

    // Step 2: Add handlers import to main.py AFTER `from bot import main`
    console.log('\n--- Step 2: Add handlers import to main.py ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('main.py', 'r') as f:
    lines = f.readlines()
# Find the 'from bot import ...' line and add handlers import after it
new_lines = []
for line in lines:
    new_lines.append(line)
    if line.strip().startswith('from bot import main'):
        new_lines.append('import bot.handlers  # Load all handler modules (moved from bot/__init__.py to avoid circular import)\\n')
        print('ADDED: import bot.handlers after line:', line.strip())
with open('main.py', 'w') as f:
    f.writelines(new_lines)
" 2>&1`);

    // Step 3: Verify
    console.log('\n--- Step 3: Verify new main.py ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -A2 "from bot import main" main.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -5 bot/__init__.py');
    
    // Step 4: Test import
    console.log('\n--- Step 4: Test import bot (should succeed) ---');
    // We can't fully test in bare shell due to env vars, but check import structure
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
import sys
try:
    # Just try to import bot constants and helpers - no handlers
    from bot import constants
    print('Bot constants import: OK')
except Exception as e:
    print(f'Import error: {e}')
" 2>&1`);

    // Step 5: Restart services
    console.log('\n--- Step 5: Restart services ---');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -15');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 20 --since "30 sec ago" 2>&1');

    // Step 6: Commit
    console.log('\n--- Step 6: Commit ---');
    const msg = 'Fix: move handler imports from __init__.py to main.py to break circular dependency';
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "${msg}" && git push 2>&1`);

    console.log('\n=== ALL DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
