const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'sed -n "90,120p" /root/psvibe-sales-bot/bot/handlers/admin.py',
  // Also check the main menu handler that routes to admin
  'grep -n "BTN_STAFF_BOOK\|Customer Booking\|cmd_admin_bookings\|bookings" /root/psvibe-sales-bot/bot/handlers/main_menu.py 2>/dev/null',
  // Where is BTN_STAFF_BOOK used?
  'grep -rn "BTN_STAFF_BOOK" /root/psvibe-sales-bot/bot/ --include="*.py" 2>/dev/null',
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());
function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results, null, 2)); return; }
  const cmd = commands[cmdIdx];
  const label = cmdIdx.toString();
  conn.exec(cmd, (err, stream) => {
    if (err) { results[label] = { cmd, stdout: '', stderr: 'ERROR: ' + err.message }; cmdIdx++; runNext(); return; }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', () => { results[label] = { cmd, stdout, stderr }; cmdIdx++; runNext(); });
  });
}
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 10000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
