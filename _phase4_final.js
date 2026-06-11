#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const { execSync } = require('child_process');

const scriptB64 = execSync('base64 -w0 /home/node/.openclaw/workspace/_auto_release_consoles.py').toString().trim();

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const cmd = 
  'echo "' + scriptB64 + '" | base64 -d > /root/scripts/auto_release_consoles.py && ' +
  'chmod +x /root/scripts/auto_release_consoles.py && ' +
  'echo "=== Testing auto_release_consoles.py ===" && ' +
  'python3 /root/scripts/auto_release_consoles.py && ' +
  'echo "" && ' +
  'echo "=== Verifying members.py changes ===" && ' +
  'grep -n "STAFF_NOTIFY_CHAT\|auto_generate_receipt\|receipt_data" /root/psvibe-sales-bot/bot/handlers/members.py && ' +
  'echo "" && ' +
  'echo "=== Final syntax check ===" && ' +
  'python3 -c "import ast; ast.parse(open(\'/root/psvibe-sales-bot/bot/handlers/members.py\').read()); print(\'members.py: Syntax OK\')" && ' +
  'echo "=== Restarting bot ===" && ' +
  'systemctl restart psvibe-sale-bot && ' +
  'sleep 3 && ' +
  'systemctl status psvibe-sale-bot --no-pager | head -10';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log(out);
      if (code) console.error('Exit code:', code);
      conn.end();
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 60000 });
