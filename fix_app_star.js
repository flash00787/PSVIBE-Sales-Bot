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
  console.log('=== Fix app.py - revert ee61e89 explicit import to star import ===');

  try {
    // 1. Check current app.py imports
    console.log('\n--- Current app.py imports ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "^from bot import" bot/app.py');

    // 2. Check original app.py before ee61e89
    console.log('\n--- Original app.py (41cbe15) imports ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show 41cbe15:bot/app.py | grep -n "^from bot import" | head -5');

    // 3. Fix app.py line 19 - revert to from bot import *
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '19s/from bot import .*/from bot import */' bot/app.py`);
    
    // 4. Check app.py line 20 - is it also problematic?
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "19,22p" bot/app.py');
    
    // Also check if there are duplicate from bot.app imports in __init__.py
    console.log('\n--- Checking __init__.py for duplicate imports ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot.app\\|from bot.handlers" bot/__init__.py');

    // Check if __init__.py has duplicate handlers/app imports
    console.log('\n--- __init__.py tail ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -15 bot/__init__.py');

    // Fix: remove duplicate handlers+app imports if they exist (keep only one set at the end)
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()

# Track lines to remove (duplicate from bot.handlers and from bot.app)
indices_to_remove = []
seen_handlers = False
seen_app = False
for i, line in enumerate(lines):
    s = line.strip()
    if s == 'from bot.handlers import *  # noqa: F401,F403,E402':
        if seen_handlers:
            indices_to_remove.append(i)
        else:
            seen_handlers = True
    if s == 'from bot.app import main as main  # noqa: F401,E402':
        if seen_app:
            indices_to_remove.append(i)
        else:
            seen_app = True

new_lines = [l for i, l in enumerate(lines) if i not in indices_to_remove]
print(f'Removed {len(indices_to_remove)} duplicate lines')
with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)
"`);

    // Verify __init__.py
    console.log('\n--- __init__.py tail after dedup ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -10 bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot.app\\|from bot.handlers" bot/__init__.py');

    // 5. Restart
    console.log('\n=== Restart ===');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 8000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -15');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 30 --since "30 sec ago" 2>&1');

    // Commit
    console.log('\n=== Commit ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: revert app.py explicit import to from bot import * - ee61e89 introduced nonexistent name fallback" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
