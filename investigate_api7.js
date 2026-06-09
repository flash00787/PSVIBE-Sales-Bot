const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Get bot's API_BASE_URL and API_KEY from env
  'grep -E "API_BASE_URL|API_KEY" /etc/psvibe/secrets.env 2>/dev/null | head -5 || grep -E "API_BASE_URL|API_KEY" /root/psvibe-sales-bot/.env 2>/dev/null | head -5',
  // Check env files
  'cat /etc/psvibe/secrets.env 2>/dev/null | grep -i api | head -5',
  // Get bot's service file for env vars
  'cat /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null | head -30',
  // Check ALL get routes in app.py (explicit route listing)
  'grep -c "@app.get" /root/psvibe_api_server/app.py',
  // Search for any handler that processes /api/bookings GET
  'grep -n "bookings" /root/psvibe_api_server/app.py',
  // Check lines around POST /api/bookings — maybe there's a GET too
  'grep -n "api.*booking" /root/psvibe_api_server/app.py | head -30',
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
