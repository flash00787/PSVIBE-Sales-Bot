const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Get full _replit_get function
  'sed -n "1982,2040p" /root/psvibe-sales-bot/bot/__init__.py',
  // Also check _api_base/get config from the API server that handles GET /api/bookings
  'grep -n "bookings.*status\|def api_bookings\|@app.get.*bookings" /root/psvibe_api_server/app.py | head -20',
  // Maybe there's a middleware or patch_routes?
  'ls /root/psvibe_api_server/patch_routes* 2>/dev/null',
  'cat /root/psvibe_api_server/patch_routes.py 2>/dev/null | grep -A30 "api/bookings" | head -60',
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
