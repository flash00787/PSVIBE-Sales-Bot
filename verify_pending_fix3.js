const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Show the actual diff of the auto-commit (pending bookings fix candidate)
  'cd /root/psvibe-sales-bot && git show 3c094b5',
  // Show the earlier pending fix commits for context
  'cd /root/psvibe-sales-bot && git show 2be094d --stat',
  // Check the admin bookings handler for pending-related code
  'cd /root/psvibe-sales-bot && grep -n "pending\|Pending\|pending_" bot/handlers/admin_bookings.py 2>/dev/null || echo "No matches"',
  'cd /root/psvibe-sales-bot && grep -n "pending\|Pending" bot/handlers/booking_flow.py 2>/dev/null | head -15',
  // Check for any recent error patterns in journal for sales bot
  'journalctl -u psvibe-sale-bot --since "2026-06-02 11:00" --no-pager 2>&1 | tail -30'
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
