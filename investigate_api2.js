const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Search for ALL route handlers with "book" in URL
  'grep -n "@app\\.\\(get\\|post\\|put\\|patch\\|delete\\).*\"' /root/psvibe_api_server/app.py | grep book | head -20',
  // Also check mysql_bookings.py
  'ls /root/psvibe_api_server/*.py | head -20',
  // Check if there's a mysql_bookings or db_bookings file
  'grep -rn "bookings" /root/psvibe_api_server/*.py | grep -i "def\|@app" | head -20',
  // Check if GET /api/bookings is handled by a catch-all or generic route
  'grep -n "status=pending\\|status ==.*pending\\|\"pending\"\\|'pending'" /root/psvibe_api_server/app.py | head -20',
  // Get line around 700-1200 of API app.py  
  'wc -l /root/psvibe_api_server/app.py',
  // Check for mysql_bookings module
  'find /root/psvibe_api_server -name "*.py" -exec grep -l "bookings.*get\|GET.*bookings" {} \\; 2>/dev/null | head -10',
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
