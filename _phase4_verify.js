#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Verify members.py has the changes
  'grep -n "STAFF_NOTIFY_CHAT" /root/psvibe-sales-bot/bot/handlers/members.py; echo "EXIT:$?"',
  // Verify auto_generate_receipt exists
  'grep -n "auto_generate_receipt" /root/psvibe-sales-bot/bot/handlers/members.py; echo "EXIT:$?"',
  // Verify receipt_data insertion
  'grep -n "receipt_data" /root/psvibe-sales-bot/bot/handlers/members.py; echo "EXIT:$?"',
  // Check bot service status
  'systemctl status psvibe-sale-bot --no-pager 2>&1 | head -15',
  // Check recent bot logs
  'journalctl -u psvibe-sale-bot --no-pager -n 15 2>&1',
];

let idx = 0;
function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log('\n=== CMD ' + idx + ' ===');
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); runNext(); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', () => { console.log(out); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
