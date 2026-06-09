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
        console.log(out.substring(0, 8000));
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
  console.log('=== DEEP DIAGNOSIS ===');

  try {
    // 1. Check if keep_alive and ensure_sheet_headers exist in bot
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^def keep_alive\\|^keep_alive\\b' bot/__init__.py`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^def ensure_sheet_headers\\|^ensure_sheet_headers\\b' bot/__init__.py`);
    
    // 2. Check systemd env vars
    await sshExec(conn, 'cat /etc/systemd/system/psvibe-sale-bot.service 2>&1 | head -30');
    
    // 3. Check the ORIGINAL __init__.py before commit ee61e89
    console.log('\n--- ORIGINAL __init__.py (before ee61e89) tail ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show c729a08:bot/__init__.py | tail -10');

    // 4. Check the pre-ee61e89 state of constants.py  
    console.log('\n--- ORIGINAL constants.py (before ee61e89) ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show c729a08:bot/constants.py | head -15');
    
    // 5. Check the diff introduced by ee61e89 in constants.py
    console.log('\n--- ee61e89 diff for constants.py ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show ee61e89 -- bot/constants.py 2>&1 | head -40');
    
    // 6. Check current constants.py full
    console.log('\n--- CURRENT constants.py ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && cat -n bot/constants.py | head -20');

    // 7. Check what app.py line 19 looks like
    console.log('\n--- app.py import line ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "19,25p" bot/app.py');

    // 8. Check if `from bot import keep_alive` works in the service env
    console.log('\n--- Test import with service env ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && source /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null; python3 -c "
import os
# Check SHEET_ID
print('SHEET_ID:', os.environ.get('SHEET_ID', 'NOT SET')[:10])
" 2>&1`);

  } finally {
    conn.end();
    console.log('\n=== DONE ===');
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
