#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Read around line 1300-1500 of members.py (topup confirm area)
  'sed -n "1300,1502p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read around line 1250-1350 (step before topup confirm)
  'sed -n "1250,1350p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Find MySQL password
  'cat /etc/psvibe/secrets.env 2>/dev/null | head -20',
  // Check console booking completion flow
  'grep -rn "booked\|booking_id\|console_id\|console_status\|end_time\|completed\|ended\|active\|Active" /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -30',
  // Check console.py for booking
  'grep -n "def.*book\|def.*end\|console_status\|booked\|available" /root/psvibe-sales-bot/bot/handlers/console.py | head -30',
];

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
    stream.on('close', () => { console.log(out.substring(0, 4000)); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
