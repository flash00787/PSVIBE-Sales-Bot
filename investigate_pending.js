const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Find bookings GET endpoint in API
  'grep -n "app\\.get.*booking" /root/psvibe_api_server/app.py | head -20',
  // Find the actual function that returns bookings list
  'grep -n "def.*booking" /root/psvibe_api_server/app.py | head -20',
  // Direct grep for "@app.get" + "booking"
  'grep -n "@app.get" /root/psvibe_api_server/app.py | grep -i book | head -10',
  // Check all route decorators with booking in them
  'grep -n "@app\\.\(get\|post\|put\|patch\).*book" /root/psvibe_api_server/app.py | head -20',
  // Now look at admin_bookings.py current version (the full function)
  'python3 -c "import ast; print(ast.dump(ast.parse(open(\"/root/psvibe-sales-bot/bot/handlers/admin_bookings.py\").read()), indent=2))" 2>&1 | head -5 || cat /root/psvibe-sales-bot/bot/handlers/admin_bookings.py',
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
