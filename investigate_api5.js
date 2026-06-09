const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Get _api_base function
  'grep -n "_api_base" /root/psvibe-sales-bot/bot/__init__.py | head -5',
  'sed -n "1940,2000p" /root/psvibe-sales-bot/bot/__init__.py',
  // What port does psvibe-api listen on?
  'cat /root/psvibe_api_server/config.py | grep -i port',
  'cat /etc/systemd/system/psvibe-api.service',
  // Check if the API server has any GET bookings endpoint anywhere else
  'grep -rn "@app.get.*book" /root/psvibe_api_server/ | head -10',
  'curl -s "http://localhost:8080/api/bookings?status=pending" 2>&1',
  // Try without api key
  'curl -s "http://localhost:8080/api/health" 2>&1 | head -5',
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
