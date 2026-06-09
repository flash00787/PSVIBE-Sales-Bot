const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'grep -rn "cmd_admin_bookings" /root/psvibe-sales-bot/bot/ 2>/dev/null',
  'grep -rn "pending" /root/psvibe-sales-bot/bot/handlers/booking_flow.py 2>/dev/null',
  'grep -rn "Customer Booking" /root/psvibe-sales-bot/bot/ 2>/dev/null',
  'grep -rn "BTN_CUST_BOOK\|BTN_BOOKINGS\|Booking" /root/psvibe-sales-bot/bot/constants.py 2>/dev/null',
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
