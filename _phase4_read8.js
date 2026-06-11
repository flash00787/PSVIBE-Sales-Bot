#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const MPASS="PsVibe@2026_Rotated!";

const commands = [
  // Check active bookings
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT id, console_id, member_id, end_time, status FROM console_booking WHERE status != 'Done' AND status != 'Cancelled' LIMIT 10;" 2>&1`,
  // Check all distinct status values
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT DISTINCT status FROM console_booking;" 2>&1`,
  // Check console_status distinct statuses
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT DISTINCT status FROM console_status;" 2>&1`,
  // Read booking_flow.py around end/complete functions
  'grep -n "Done\|Active\|Free\|Booked\|completed\|available\|status\|end_time\|session_end\|def " /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -50',
  // Read console.py for booking management  
  'grep -n "Done\|Active\|Free\|Booked\|completed\|available\|status\|end_time\|def " /root/psvibe-sales-bot/bot/handlers/console.py | head -50',
  // Check that context.bot is the right way to send message
  'grep -rn "context.bot" /root/psvibe-sales-bot/bot/handlers/members.py | head -5',
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
