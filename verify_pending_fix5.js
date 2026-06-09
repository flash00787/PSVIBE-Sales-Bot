const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'cd /root/psvibe-sales-bot && git show e576321 --stat',
  'cd /root/psvibe-sales-bot && git show 2e8fb8a --stat',
  'cd /root/psvibe-sales-bot && git log --all --oneline --since="2026-06-02 11:00"',
  'cd /root/psvibe_api_server && grep -n bookings app.py 2>/dev/null | head -20 || echo no',
  'cd /root/psvibe-sales-bot && grep -n "_replit_get" bot/__init__.py | head -5',
  'cd /root/psvibe_api_server && grep -n "pending" app.py 2>/dev/null | head -20 || echo no'
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());
function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results)); return; }
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
