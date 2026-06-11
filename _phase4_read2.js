#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  // Search for topup-related functions in members.py
  'grep -n "def.*tu_\|def.*topup\|def.*receipt\|step_tu\|save_receipt\|get_receipt\|staff.*chat\|STAFF_CHAT" /root/psvibe-sales-bot/bot/handlers/members.py | head -40',
  // Check line count and look for receipt/topup patterns  
  'wc -l /root/psvibe-sales-bot/bot/handlers/members.py',
  // Find booking completion patterns
  'grep -rn "def.*complete\|end_time\|console_status\|def.*release\|console.*available" /root/psvibe-sales-bot/bot/handlers/ --include="*.py" | grep -v ".bak" | head -40',
  // Check MySQL access
  'docker ps --format "{{.Names}} {{.Image}}" 2>/dev/null | head -10',
  // Check for existing env vars / config
  'grep -r "STAFF_CHAT\|staff_chat\|STAFF_GROUP" /root/psvibe-sales-bot/bot/ --include="*.py" | head -10',
  // Check console_booking table
  'docker exec mysql mysql -uroot -e "SHOW DATABASES;" 2>/dev/null || docker exec mariadb mysql -uroot -e "SHOW DATABASES;" 2>/dev/null || echo "NO MYSQL/MARIADB"',
];

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
let idx = 0;

function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx}: ${cmd.substring(0,100)} ===`);
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
