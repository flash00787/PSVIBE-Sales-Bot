#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const cmd = 
  'echo "===== FINAL VERIFICATION =====" && ' +
  'echo "" && ' +
  'echo "1. members.py syntax:" && ' +
  'python3 -c "import ast; ast.parse(open(\'/root/psvibe-sales-bot/bot/handlers/members.py\').read()); print(\'   OK\')" && ' +
  'echo "2. auto_release script syntax + test:" && ' +
  'python3 -c "import ast; ast.parse(open(\'/root/scripts/auto_release_consoles.py\').read()); print(\'   Syntax OK\')" && ' +
  'python3 /root/scripts/auto_release_consoles.py 2>&1 && ' +
  'echo "3. Bot running:" && ' +
  'systemctl is-active psvibe-sale-bot && ' +
  'echo "4. Cron active:" && ' +
  'systemctl is-active cron && ' +
  'echo "5. Backup exists:" && ' +
  'ls -la /root/psvibe-sales-bot/bot/handlers/members.py.bak_kora_phase4 && ' +
  'echo "" && ' +
  'echo "===== ALL CHECKS PASSED ====="';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', () => {
      console.log(out);
      conn.end();
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
