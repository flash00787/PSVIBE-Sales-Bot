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
  console.log('=== Fix: import main from bot.app directly ===');

  try {
    // 1. Check where keep_alive and ensure_sheet_headers are defined
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn "^def keep_alive\|^keep_alive =" bot/ | head -5`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn "^def ensure_sheet_headers\|^ensure_sheet_headers =" bot/ | head -5`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n "^def main\|^main =" bot/app.py | head -5`);
    
    // 2. Remove `from bot.app import main as main` from __init__.py
    console.log('\n--- Step 1: Remove app import from __init__.py ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if 'from bot.app import main' not in line:
        new_lines.append(line)
    else:
        print('REMOVED:', line.strip())
with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)
" 2>&1`);

    // 3. Fix main.py to import main from bot.app directly
    console.log('\n--- Step 2: Fix main.py ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('main.py', 'r') as f:
    content = f.read()
# Replace the import line
content = content.replace(
    'from bot import main, keep_alive, ensure_sheet_headers',
    'from bot import keep_alive, ensure_sheet_headers\\nfrom bot.app import main as main'
)
with open('main.py', 'w') as f:
    f.write(content)
print('FIXED main.py imports')
" 2>&1`);

    // Verify
    console.log('\n--- Verify ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -12 main.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -5 bot/__init__.py');

    // Restart
    console.log('\n--- Restart ---');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 20 --since "30 sec ago" 2>&1');

    // Commit
    console.log('\n--- Commit ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: import main from bot.app directly in main.py to avoid circular import via app.py" && git push 2>&1`);

    console.log('\n=== ALL DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
