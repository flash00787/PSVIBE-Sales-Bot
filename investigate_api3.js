const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'grep -n "@app" /root/psvibe_api_server/app.py | grep -i book | head -20',
  'wc -l /root/psvibe_api_server/app.py',
  'grep -rn "bookings" /root/psvibe_api_server/*.py | grep -i "def\|@app" | head -30',
  'grep -n "pending" /root/psvibe_api_server/app.py | head -20',
  'find /root/psvibe_api_server -name "*.py" | head -20',
  'grep -n "status=pending\|status.*pending.*filter" /root/psvibe_api_server/app.py | head -10',
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
