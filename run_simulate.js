const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const scpContent = fs.readFileSync('/home/node/.openclaw/workspace/simulate_replit.py').toString('base64');

const commands = [
  // Upload the test script
  `echo "${scpContent}" | base64 -d > /tmp/simulate_replit.py`,
  // Insert test booking
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "INSERT INTO console_booking (console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name) VALUES (\'\', \'6296803251\', \'2026-06-03\', \'2026-06-03 18:00:00\', \'2026-06-03 19:00:00\', \'pending\', \'Test Customer\', \'Game: FIFA 23 | Phone: 09123456789\', \'6296803251\', 60, \'09123456789\', \'FIFA 23\')" 2>&1',
  // Run the simulation
  'python3 /tmp/simulate_replit.py 2>&1',
  // Clean up
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "DELETE FROM console_booking WHERE staff_name=\'Test Customer\'" 2>&1',
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
