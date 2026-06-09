const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Show the full admin_bookings.py to check the pending display logic
  'cd /root/psvibe-sales-bot && cat -n bot/handlers/admin_bookings.py | head -100',
  // Check if there was no dedicated pending bookings fix commit (search git reflog)
  'cd /root/psvibe-sales-bot && git reflog --oneline -10',
  // Look for commit referencing "pending_bookings" or "admin_bookings" today
  'cd /root/psvibe-sales-bot && git log --all --oneline --since="2026-06-02" | head -20',
  // Check the actual commit that the fix_pending_bookings agent should have made
  'cd /root/psvibe-sales-bot && git log --all --oneline --grep="fix.*pending\|pending.*fix\|fix_pending" -i -10',
  // See what the no-show button handler looks like
  'cd /root/psvibe-sales-bot && grep -n "def cb_" bot/handlers/admin_bookings.py | head -20'
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());

function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results)); return; }
  const cmd = commands[cmdIdx];
  const label = cmdIdx.toString();
  conn.exec(cmd, (err, stream) => {
    if (err) { results[label] = { cmd, stdout: '', stderr: `ERROR: ${err.message}` }; cmdIdx++; runNext(); return; }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', () => { results[label] = { cmd, stdout, stderr }; cmdIdx++; runNext(); });
  });
}

conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 10000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
