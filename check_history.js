const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check commit 2e8fb8a fully
  'cd /root/psvibe-sales-bot && git log --oneline -10',
  'cd /root/psvibe-sales-bot && git show 2e8fb8a --stat 2>/dev/null',
  'cd /root/psvibe-sales-bot && git show 2e8fb8a 2>/dev/null | head -100',
  // Look for any fix_pending related commits
  'cd /root/psvibe-sales-bot && git log --all --oneline --grep="pending\|fix_pending\|booking" | head -10',
  // Check admin menu - how does admin_bookings get called?
  'grep -n "admin_bookings\|cmd_admin_bookings\|pending" /root/psvibe-sales-bot/bot/handlers/admin.py | head -20',
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
