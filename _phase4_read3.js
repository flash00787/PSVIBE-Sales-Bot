#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// We'll run multiple commands sequentially through a single session
const commands = [
  // 1. Search for topup flow in members.py
  `grep -n "topup\|top.up\|TOPUP\|def.*step_\|def.*confirm" /root/psvibe-sales-bot/bot/handlers/members.py | head -30`,
  // 2. Search for booking flow functions  
  `grep -n "def.*book\|Booking\|booking_" /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -30`,
  // 3. Check config for staff chat
  `grep -rn "STAFF\|staff" /root/psvibe-sales-bot/bot/config*.py 2>/dev/null | head -10`,
  // 4. Check MySQL credentials
  `cat /root/psvibe-sales-bot/bot/config.py 2>/dev/null | head -40`,
  // 5. Check env file  
  `cat /root/psvibe-sales-bot/.env 2>/dev/null | head -30`,
  // 6. Check docker MySQL  
  `docker exec psvibe-mysql mysql -uroot -e "SHOW DATABASES;" 2>&1 | head -10`,
];

let idx = 0;

function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx}: ${cmd.substring(0,120)} ===`);
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
