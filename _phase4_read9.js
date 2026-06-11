#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const MPASS="PsVibe@2026_Rotated!";

const commands = [
  // Read booking_flow.py around console booking/ending
  'sed -n "1,250p" /root/psvibe-sales-bot/bot/handlers/booking_flow.py',
  // Read console_mgmt.py
  'cat /root/psvibe-sales-bot/bot/handlers/console_mgmt.py | head -200',
  // Check if there are any console bookings currently "active" - maybe the status field differs  
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT DISTINCT console_id, status FROM console_booking ORDER BY id DESC LIMIT 20;" 2>&1`,
  // Check admin_bookings.py
  'head -100 /root/psvibe-sales-bot/bot/handlers/admin_bookings.py',
  // Check for any "status" updates in booking code
  'grep -rn "console_status\|console_booking" /root/psvibe-sales-bot/bot/ --include="*.py" | grep -v ".bak" | head -20',
];

let idx = 0;
function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx} ===`);
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); runNext(); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', () => { console.log(out.substring(0, 4000)); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
