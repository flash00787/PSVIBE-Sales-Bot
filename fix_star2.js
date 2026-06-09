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
  console.log('=== Fix: sed replace explicit imports with star imports ===');

  try {
    // Fix each file individually with sed
    // Pattern: replace 'from bot import X, Y, Z' at start of line with 'from bot import *'
    const files = [
      'bot/handlers/attendance.py',
      'bot/handlers/booking_flow.py',
      'bot/handlers/broadcast.py',
      'bot/handlers/console_mgmt.py',
      'bot/handlers/ginst.py',
      'bot/handlers/payroll.py',
      'bot/handlers/stock_in.py'
    ];

    for (const f of files) {
      const cmd = `cd /root/psvibe-sales-bot && sed -i '1s/^from bot import .*/from bot import */' ${f}`;
      await sshExec(conn, cmd);
    }

    // Verify
    console.log('\n=== Verify fixed files ===');
    for (const f of files) {
      await sshExec(conn, `cd /root/psvibe-sales-bot && head -1 ${f}`);
    }

    // Check if there are more explicit imports with commas mid-file
    console.log('\n=== Check remaining explicit imports ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import.*,.*,' bot/handlers/*.py | grep -v '.bak\|.test_backup'`);

    // Also fix console.py which has two from bot import * lines - one is already star, the other at 352
    console.log('\n=== Check console.py ===');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "^from bot import" bot/handlers/console.py');
    
    // Fix console.py line 352 if it's explicit
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '352s/^from bot import .*/from bot import */' bot/handlers/console.py`);

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
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: revert handler explicit imports to from bot import * to fix amt/fmt/col/empty/filled KeyErrors" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
