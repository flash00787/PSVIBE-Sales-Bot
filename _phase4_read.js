#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  // Read step_tu_confirm area in members.py
  'grep -n "step_tu_confirm\|save_receipt_json\|get_receipt_kb\|auto_generate" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read booking handlers
  'ls /root/psvibe-sales-bot/bot/handlers/',
  // Check DB schema for console_booking
  'docker exec mysql mysql -uroot -prootpassword psvibe -e "SHOW TABLES;" 2>/dev/null || docker exec mysql mysql -uroot -p$(cat /root/.my.cnf 2>/dev/null || echo "") psvibe -e "SHOW TABLES;" 2>/dev/null',
  // Check existing cron
  'ls /etc/cron.d/ 2>/dev/null; crontab -l 2>/dev/null',
  // Check existing scripts dir
  'ls /root/scripts/ 2>/dev/null || echo "NO SCRIPTS DIR"',
];

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
let idx = 0;

function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx}: ${cmd.substring(0,80)}... ===`);
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); runNext(); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', () => { console.log(out || '(empty)'); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
