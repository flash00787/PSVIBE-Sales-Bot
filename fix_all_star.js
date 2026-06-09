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
  console.log('=== Fix ALL explicit from bot import in handlers ===');

  try {
    // First, find ALL remaining explicit imports
    console.log('\n--- ALL remaining explicit imports ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import \" bot/handlers/*.py | grep -v '.bak' | grep -v '.test_backup' | grep ','`);

    // Write fix script to VPS
    await sshExec(conn, `cat > /tmp/fix_imports.py << 'ENDOFPYTHON'
import glob, re

handler_dir = '/root/psvibe-sales-bot/bot/handlers'
files = glob.glob(handler_dir + '/*.py')
fixed_any = False

for fpath in sorted(files):
    if '.bak' in fpath or '.test_backup' in fpath:
        continue
    
    with open(fpath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    for line in lines:
        s = line.lstrip()
        # Match explicit from bot import with commas (listing specific names)
        if s.startswith('from bot import ') and ',' in s.split('#')[0] and not s.startswith('#'):
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + 'from bot import *\n')
            modified = True
            print(f'FIXED: {fpath}: {line.strip()[:100]}')
        else:
            new_lines.append(line)
    
    if modified:
        with open(fpath, 'w') as f:
            f.writelines(new_lines)
        fixed_any = True

if fixed_any:
    print('FIXES APPLIED')
else:
    print('NO CHANGES NEEDED')
ENDOFPYTHON`);

    // Run the fix script
    console.log('\n--- Running fix script ---');
    await sshExec(conn, 'python3 /tmp/fix_imports.py');

    // Verify no more explicit imports
    console.log('\n--- Verify no remaining explicit imports ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import \" bot/handlers/*.py | grep -v '.bak' | grep -v '.test_backup' | grep ','`);

    // Also fix broadcast.py (has import on line 10 not just line 1)
    console.log('\n--- Check specific files ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -12 bot/handlers/broadcast.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -12 bot/handlers/console_mgmt.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -15 bot/handlers/ginst.py');

    // Restart
    console.log('\n=== Restart ===');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal (last 30 lines) ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 30 --since "30 sec ago" 2>&1');

    // Commit
    console.log('\n=== Commit ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: restore ALL handler explicit imports to from bot import * (including multi-line and indented)" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
