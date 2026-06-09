const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'sed -n "920,1050p" /root/psvibe_api_server/app.py',
  'grep -n "mysql\|MySQL\|sql\|SQL" /root/psvibe_api_server/app.py | head -20',
  'grep -rn "SELECT.*booking\|booking.*SELECT" /root/psvibe_api_server/app.py | head -5',
  'curl -s "http://localhost:8080/api/bookings?status=pending&api_key=test" 2>&1 | head -50',
  'curl -s "http://localhost:8080/api/bookings?status=pending" -H "X-API-Key: test" 2>&1 | head -50',
  'systemctl status psvibe-api 2>&1 | head -5 || systemctl status psvibe-api-server 2>&1 | head -5',
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
