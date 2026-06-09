const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Get admin.py booking-related sections
  'grep -n "book\|booking\|pending\|Admin" /root/psvibe-sales-bot/bot/handlers/admin.py | head -30',
  // Check what show_admin_menu looks like
  'grep -n -A30 "def show_admin_menu" /root/psvibe-sales-bot/bot/handlers/admin.py',
  // Check latest commit diff  
  'cd /root/psvibe-sales-bot && git diff HEAD~1 -- bot/handlers/admin_bookings.py',
  // Check commit 3c094b5 changes
  'cd /root/psvibe-sales-bot && git show 3c094b5 --stat',
  'cd /root/psvibe-sales-bot && git show 3c094b5 | head -80',
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
