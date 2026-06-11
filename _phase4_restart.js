#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const cmd = 
  'echo "=== Restarting bot ===" && ' +
  'systemctl restart psvibe-sale-bot && ' +
  'sleep 3 && ' +
  'systemctl status psvibe-sale-bot --no-pager 2>&1 | head -8 && ' +
  'echo "" && ' +
  'echo "=== Cron verification ===" && ' +
  'cat /etc/cron.d/kora-auto-release && ' +
  'echo "" && ' +
  'echo "=== Script verification ===" && ' +
  'ls -la /root/scripts/auto_release_consoles.py && ' +
  'echo "" && ' +
  'echo "✓ ALL PHASE 4 UPGRADES COMPLETE"';

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
