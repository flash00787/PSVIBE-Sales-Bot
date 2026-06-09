const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Find _map_booking_row function
  'grep -n -A30 "def _map_booking_row" /root/psvibe_api_server/patch_routes.py',
  // Query pending bookings directly
  'curl -s "http://localhost:8000/api/bookings?status=pending&api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -m json.tool 2>/dev/null | head -80',
  // Check if there's also a GET booking by id with _map_booking_row
  'grep -n "_map_booking_row\|customerName\|timeSlot" /root/psvibe_api_server/patch_routes.py | head -20',
  // Check what patch_routes imports/exports  
  'head -30 /root/psvibe_api_server/patch_routes.py',
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
