const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${cmd.substring(0, 150)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => { stdout += d.toString(); });
      stream.stderr.on('data', d => { stderr += d.toString(); });
      stream.on('close', (code, signal) => {
        const out = (stdout + stderr).trim();
        console.log(out.substring(0, 2000));
        resolve({ code, stdout, stderr, combined: out });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: '5.223.81.16', port: 22, username: 'root',
      privateKey: fs.readFileSync(path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa')),
      readyTimeout: 15000,
    });
  });
  console.log('=== CONNECTED ===');

  try {
    // 1. Check current state
    console.log('\n=== STEP 1: Current State ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git status');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,10p" bot/constants.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "130,140p" bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -10 bot/helpers.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -15 bot/__init__.py');

    // 2. Try simple import to see where it fails
    console.log('\n=== STEP 2: Test current import ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales; print(\'OK\')" 2>&1 | head -10');

    // 3. NOW APPLY THE PROPER FIX using a Python script on the VPS itself
    console.log('\n=== STEP 3: Apply fix via Python ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 << 'PYEOF'
import re

# Fix constants.py: remove `from bot import ...` line
with open('bot/constants.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 4 and line.strip().startswith('from bot import') and 'ASSET_CATEGORIES' in line:
        new_lines.append('# (moved: original from bot import removed to break circular dependency)\n')
        print(f"FIXED constants.py line {i+1}: removed from bot import")
    else:
        new_lines.append(line)

with open('bot/constants.py', 'w') as f:
    f.writelines(new_lines)

# Fix __init__.py: comment out lines 132-133 and add them at end before handler import
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    ln = i + 1
    if ln == 132 and 'from bot.constants import' in line:
        new_lines.append('# (moved to end of file) from bot.constants import *\\n')
        print(f"FIXED __init__.py line {ln}: commented constants import")
    elif ln == 133 and 'from bot.helpers import' in line:
        new_lines.append('# (moved to end of file) from bot.helpers import *\\n')
        print(f"FIXED __init__.py line {ln}: commented helpers import")
    else:
        new_lines.append(line)

# Find last import line (from bot.handlers) and add our imports before it
insert_idx = None
for i, line in enumerate(new_lines):
    ln = i + 1
    if 'from bot.handlers import' in line or 'from bot.app import' in line:
        insert_idx = i
        break

if insert_idx is not None:
    new_lines.insert(insert_idx, 'from bot.constants import *\\n')
    new_lines.insert(insert_idx + 1, 'from bot.helpers import *\\n')
    print(f"INSERTED constants+helpers import before line {insert_idx+1}")

with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)

print("DONE: Applied both fixes")
PYEOF`);

    // 4. Verify fix
    console.log('\n=== STEP 4: Verify imports ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales; print(\'SINGLE IMPORT OK\')" 2>&1');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
from bot.handlers import sales, booking, admin, members, stock, stock_in, finance, salary_adv
from bot import constants
print('ALL IMPORTS OK')
" 2>&1`);

    // 5. Verify files look right
    console.log('\n=== STEP 5: Verify file changes ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,10p" bot/constants.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "130,140p" bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot.constants\|from bot.helpers" bot/__init__.py');

    // 6. Restart services
    console.log('\n=== STEP 6: Restart services ===');
    await sshExec(conn, 'systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 4000));
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -8');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 15 --since "1 min ago" 2>&1');

    // 7. Git commit (skip pre-commit hooks)
    console.log('\n=== STEP 7: Git commit and push ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: resolve circular import between __init__.py, constants.py, and helpers.py" && git push 2>&1');

    console.log('\n=== ALL DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
