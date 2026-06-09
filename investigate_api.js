const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Get all route decorators from API server
  'grep -n "@app\\." /root/psvibe_api_server/app.py | grep -i book | head -20',
  // Check if there's a generic bookings GET handler  
  'grep -n "bookings" /root/psvibe_api_server/app.py | head -40',
  // Check what handler matches "bookings?status=pending"  
  'grep -B3 -A5 "def.*booking" /root/psvibe_api_server/app.py | head -80',
  // Check bot logs for any errors
  'journalctl -u psvibe-sale-bot -n 30 --no-pager 2>&1 | grep -i -E "book|pending|error" | tail -15',
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
