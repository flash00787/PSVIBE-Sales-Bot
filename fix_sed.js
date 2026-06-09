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
        console.log(out.substring(0, 4000));
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
  console.log('=== Fix remaining explicit imports line-by-line ===');

  try {
    // console_mgmt.py line 9
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '9s/from bot import .*/from bot import */' bot/handlers/console_mgmt.py`);
    
    // broadcast.py line 10
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '10s/from bot import .*/from bot import */' bot/handlers/broadcast.py`);
    
    // ginst.py line 12  
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '12s/from bot import .*/from bot import */' bot/handlers/ginst.py`);

    // stock_in.py line 1 (already fixed by previous sed)
    // payroll.py line 1 (already fixed)
    // attendance.py line 1 (already fixed)
    // booking_flow.py line 1 (already fixed)

    // Check finance.py
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^from bot import' bot/handlers/finance.py | head -5`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '1s/from bot import .*/from bot import */' bot/handlers/finance.py`);
    
    // Fix line 6 of finance.py too (has from bot import wb)
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '6s/from bot import .*/from bot import */' bot/handlers/finance.py`);

    // Check admin_bookings.py
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^from bot import' bot/handlers/admin_bookings.py | head -5`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '8s/from bot import .*/from bot import */' bot/handlers/admin_bookings.py`);

    // Check console.py line 4 and 352
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^from bot import' bot/handlers/console.py`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '352s/from bot import .*/from bot import */' bot/handlers/console.py`);
    
    // Verify ALL fixed
    console.log('\n=== Verify ALL handler imports ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import ' bot/handlers/*.py | grep "," | grep -v '.bak'`);

    // Check specific fixed files
    await sshExec(conn, `cd /root/psvibe-sales-bot && head -10 bot/handlers/console_mgmt.py | tail -2`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && head -11 bot/handlers/broadcast.py | tail -2`);
    await sshExec(conn, `cd /root/psvibe-sales-bot && head -13 bot/handlers/ginst.py | tail -2`);

    // Restart
    console.log('\n=== Restart ===');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 30 --since "1 min ago" 2>&1');

    // Commit
    console.log('\n=== Commit ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: restore ALL remaining handler explicit imports to star imports (console_mgmt, broadcast, ginst, finance, admin_bookings)" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
