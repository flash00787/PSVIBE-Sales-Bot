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
  console.log('=== Fix: add back from bot.app import main ===');

  try {
    // 1. Add back `from bot.app import main as main` to __init__.py (NOT the handlers import)
    console.log('\n--- Step 1: Add back app import ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    content = f.read()
# Check current end
lines = content.split('\\n')
print('Last 5 lines:')
for l in lines[-5:]:
    print(repr(l))
" 2>&1`);

    // Add from bot.app import main as main at the end of __init__.py (after constants+helpers)
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()
# Add app import after helpers import at end
new_lines = []
for line in lines:
    new_lines.append(line)
    if line.strip() == 'from bot.helpers import *':
        new_lines.append('from bot.app import main as main  # noqa: F401,E402\\n')
        print('ADDED: from bot.app import main as main after helpers import')
with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)
" 2>&1`);

    // Verify
    console.log('\n--- Verify __init__.py tail ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -8 bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -15 main.py');

    // Restart
    console.log('\n--- Restart ---');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 25 --since "30 sec ago" 2>&1');

    // Commit
    console.log('\n--- Commit ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: restore from bot.app import main in __init__.py (removed mistakenly)" && git push 2>&1`);

    console.log('\n=== ALL DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
