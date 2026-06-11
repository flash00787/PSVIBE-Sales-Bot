#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Read the rest of step_tu_confirm from where we left off (around line 1370-1420)
  'sed -n "1370,1420p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read booking_flow.py for console booking / session end  
  'grep -n "def \|console_status\|booked\|available\|end_time\|session_end" /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -40',
  // Check the console.py for booking-related code
  'grep -n "def \|console_status\|status\|booked\|available\|reserved\|end" /root/psvibe-sales-bot/bot/handlers/console.py | head -40',
  // Find MySQL password
  'grep -r "MYSQL_PASSWORD" /etc/psvibe/secrets.env /root/psvibe-sales-bot/.env 2>/dev/null',
  // Check DB tables
  'docker exec psvibe-mysql mysql -upsvibe_user -p"$(grep MYSQL_PASSWORD /etc/psvibe/secrets.env | cut -d= -f2)" psvibe_api -e "SHOW TABLES;" 2>&1',
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
