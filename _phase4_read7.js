#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const MPASS="PsVibe@2026_Rotated!";

const commands = [
  // Check console_booking table structure
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "DESCRIBE console_booking;" 2>&1`,
  // Check console_status table structure
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "DESCRIBE console_status;" 2>&1`,
  // Check some sample data from console_booking
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT * FROM console_booking ORDER BY id DESC LIMIT 3;" 2>&1`,
  // Check console_status sample
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT * FROM console_status LIMIT 5;" 2>&1`,
  // Check rest of members.py step_tu_confirm
  'sed -n "1420,1450p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Check booking_flow for end/complete functions
  'grep -n "def \|session.*end\|end_time\|booking.*status\|console.*status" /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -30',
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
