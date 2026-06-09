const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Insert test pending booking
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "INSERT INTO console_booking (console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name) VALUES (\'\', \'6296803251\', \'2026-06-03\', \'2026-06-03 18:00:00\', \'2026-06-03 19:00:00\', \'pending\', \'Test Customer\', \'Game: FIFA 23 | Phone: 09123456789\', \'6296803251\', 60, \'09123456789\', \'FIFA 23\')" 2>&1',
  // Query via API
  'curl -s "http://localhost:8000/api/bookings?status=pending&api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d,indent=2))" 2>&1',
  // Query single booking via API (get the new ID)
  'NEW_ID=$(mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -sN -e "SELECT MAX(id) FROM console_booking WHERE staff_name=\'Test Customer\'"); echo "New ID: $NEW_ID"; curl -s "http://localhost:8000/api/bookings/$NEW_ID?api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin),indent=2))" 2>&1',
  // Clean up test booking
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "DELETE FROM console_booking WHERE staff_name=\'Test Customer\'" 2>&1',
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());
function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results, null, 2)); return; }
  const cmd = commands[cmdIdx];
  const label = cmdIdx.toString();
  conn.exec(cmd, { pty: true }, (err, stream) => {
    if (err) { results[label] = { cmd, stdout: '', stderr: 'ERROR: ' + err.message }; cmdIdx++; runNext(); return; }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', () => { results[label] = { cmd, stdout, stderr }; cmdIdx++; runNext(); });
  });
}
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 10000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
