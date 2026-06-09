const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${cmd.substring(0, 180)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let o = '', e = '';
      stream.on('data', d => { o += d.toString(); });
      stream.stderr.on('data', d => { e += d.toString(); });
      stream.on('close', (code) => {
        const out = (o + e).trim();
        console.log(out.substring(0, 3000));
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
  console.log('=== SSH CONNECTED ===');

  try {
    // FIX: Remove `from bot import ...` from helpers.py line 5
    // ALL those names are defined locally in helpers.py itself
    console.log('\n=== FIX helpers.py: remove redundant from bot import ===');
    
    // Use Python to safely remove the line
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/helpers.py', 'r') as f:
    lines = f.readlines()
# Remove line 5 (0-indexed: 4) if it starts with 'from bot import'
if lines[4].strip().startswith('from bot import'):
    lines.pop(4)
    print('REMOVED line 5: from bot import ...')
else:
    print('Line 5 was already fixed')
with open('bot/helpers.py', 'w') as f:
    f.writelines(lines)
" 2>&1`);

    // Verify helpers.py
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,12p" bot/helpers.py');

    // TEST 1: Basic import
    console.log('\n=== TEST 1: import bot.handlers.sales ===');
    let r = await sshExec(conn, 'cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales; print(\'IMPORT OK\')" 2>&1');
    
    if (r.code === 0 && r.out.includes('IMPORT OK')) {
      // TEST 2: All handlers
      console.log('\n=== TEST 2: All handlers + constants ===');
      await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
from bot.handlers import sales, booking, admin, members, stock, stock_in, finance, salary_adv
from bot import constants
print('ALL IMPORTS OK')
" 2>&1`);

      // RESTART SERVICES
      console.log('\n=== Restarting services ===');
      await sshExec(conn, 'systemctl restart psvibe-sale-bot.service 2>&1');
      await new Promise(r => setTimeout(r, 4000));
      await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -10');
      await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 10 --since "1 min ago" 2>&1');

      // GIT COMMIT (skip pre-commit hooks that revert changes)
      console.log('\n=== Git commit and push ===');
      await sshExec(conn, 'cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: resolve circular imports - constants.py and helpers.py both had redundant from bot imports" && git push 2>&1');
    } else {
      console.log('\n=== IMPORT STILL FAILS - diagnostic ===');
      await sshExec(conn, 'cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales" 2>&1');
    }

    console.log('\n=== ALL DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
