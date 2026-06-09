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
  console.log('=== Fix main_menu.py broken indentation ===');

  // Check the FULL main_menu.py to understand the broken area
  await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,30p" bot/handlers/main_menu.py');

  // Fix: remove lines 15-22 (the broken indented lines after from bot import *)
  await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -i "15,22d" bot/handlers/main_menu.py');
  
  // Verify
  await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "12,20p" bot/handlers/main_menu.py');

  // Check for other files with similar breakage
  await sshExec(conn, `cd /root/psvibe-sales-bot && for f in bot/handlers/*.py; do awk '/^from bot import \\*$/{getline; if(/^[[:space:]]/) print FILENAME\":\"NR\":\"\\$0}' "$f"; done`);

  // Restart  
  await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service');
  await new Promise(r => setTimeout(r, 6000));

  console.log('\n=== Status ===');
  await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
  
  console.log('\n=== Journal ===');
  await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 25 --since "30 sec ago" 2>&1');

  // Commit
  console.log('\n=== Commit ===');
  await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: remove broken multi-line continuation after from bot import * in main_menu.py" && git push 2>&1`);

  console.log('\n=== DONE ===');
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
