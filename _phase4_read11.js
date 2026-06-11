#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const MPASS="PsVibe@2026_Rotated!";

const commands = [
  // Check API routes for booking/session end
  'grep -rn "console_status\|console_booking\|session.*end\|end_session\|booked\|Active\|Free" /root/psvibe_api_server/ --include="*.py" | grep -v ".pyc" | grep -v "__pycache__" | head -30',
  // Check the booking flow for how sessions end in the bot code
  'grep -rn "Update.*console_status\|UPDATE.*console_status\|UPDATE.*console_booking\|status.*Free\|status.*Done" /root/psvibe-sales-bot/bot/ --include="*.py" | grep -v ".bak" | head -20',
  // Check if any active bookings exist where end_time < NOW
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT id, console_id, end_time, status, NOW() as now_ts FROM console_booking WHERE end_time < NOW() AND status NOT IN ('Done', 'cancelled', 'rejected') LIMIT 10;" 2>&1`,
  // Check for any non-Free console_status records
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT * FROM console_status WHERE status != 'Free';" 2>&1`,
  // Check all distinct statuses more carefully (might be case issues)
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT status, COUNT(*) as cnt FROM console_booking GROUP BY status;" 2>&1`,
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
