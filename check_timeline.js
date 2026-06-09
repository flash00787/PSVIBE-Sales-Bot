const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check bot start time
  'systemctl status psvibe-sale-bot 2>&1 | head -10',
  // Check API start time  
  'systemctl status psvibe-api 2>&1 | head -10',
  // Check bot main.py PID and start time
  'ps aux | grep "main.py" | grep -v grep',
  // Last git commits vs service start times
  'cd /root/psvibe-sales-bot && git log --format="%H %ai %s" -5',
  // Check if admin_bookings.py was recently modified
  'stat /root/psvibe-sales-bot/bot/handlers/admin_bookings.py 2>&1',
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
