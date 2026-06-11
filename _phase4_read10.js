#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const MPASS="PsVibe@2026_Rotated!";

const commands = [
  // Check for any "pending" status bookings
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT id, console_id, member_id, end_time, status FROM console_booking ORDER BY id DESC LIMIT 20;" 2>&1`,
  // Check booking via API
  'grep -rn "POST.*book\|PATCH.*book\|def.*book\|booking.*status" /root/psvibe_api_server/ --include="*.py" | grep -v ".pyc" | head -20',
  // Read how console status gets updated during booking
  'grep -rn "console_status\|console_booking" /root/psvibe_api_server/ --include="*.py" | grep -v ".pyc" | head -20',
  // Check recent console_status 
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT * FROM console_status ORDER BY last_updated DESC LIMIT 10;" 2>&1`,
  // Check what status bookings transition through
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT id, status, start_time, end_time FROM console_booking WHERE start_time IS NOT NULL ORDER BY id DESC LIMIT 15;" 2>&1`,
  // Check for shop name in settings
  `docker exec psvibe-mysql mysql -upsvibe_user -p'${MPASS}' psvibe_api -e "SELECT * FROM settings LIMIT 10;" 2>&1`,
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
