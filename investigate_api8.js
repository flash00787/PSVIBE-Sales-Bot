const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Direct API query with real key
  'curl -s "http://localhost:8000/api/bookings?status=pending&api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -m json.tool 2>/dev/null | head -60',
  // Also try without status filter
  'curl -s "http://localhost:8000/api/bookings?api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -m json.tool 2>/dev/null | head -60',
  // Get the BROKEN backup GET /api/bookings handler 
  'grep -n "api/bookings" /root/psvibe_api_server/app.py.BROKEN_MULTI_AGENT | head -10',
  'sed -n "2530,2700p" /root/psvibe_api_server/app.py.BROKEN_MULTI_AGENT',
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
