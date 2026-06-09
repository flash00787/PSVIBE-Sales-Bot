const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // MySQL via Docker or with proper creds
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "SHOW COLUMNS FROM console_booking" 2>&1',
  // Check if there ARE any pending bookings (case insensitive)
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "SELECT id, status, staff_name, phone, game_name FROM console_booking WHERE LOWER(status)=\'pending\' LIMIT 5" 2>&1',
  // Check total bookings
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "SELECT COUNT(*), status FROM console_booking GROUP BY status" 2>&1',
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
