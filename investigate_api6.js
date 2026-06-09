const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Test live API on port 8000
  'curl -s "http://localhost:8000/api/bookings?status=pending" | head -100',
  // What _api_base() returns — check env vars
  'grep -n "REPLIT_DEV_DOMAIN\|API_HOST\|API_PORT\|api.*base\|_api_base" /root/psvibe-sales-bot/bot/__init__.py | head -15',
  // Get _api_base definition 
  'grep -n -A20 "def _api_base" /root/psvibe-sales-bot/bot/__init__.py',
  // Check what BROKEN backup has for bookings GET response fields
  'grep -A40 "get.*bookings.*status.*pending\|def.*api_bookings_list\|@app.get.*bookings" /root/psvibe_api_server/app.py.BROKEN_MULTI_AGENT | head -60',
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
