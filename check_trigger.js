const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Search for "Pending" or "pending" in the bot handlers
  'grep -rn "pending\|Pending\|BTN.*BOOK\|booking.*btn\|Booking လုပ်" /root/psvibe-sales-bot/bot/ --include="*.py" | grep -iv "import\|logger\|pyc\|__pycache__" | head -30',
  // Check how pending_bookings is triggered - maybe via callback or text command
  'grep -rn "cmd_admin_bookings\|admin_bookings\|pending" /root/psvibe-sales-bot/bot/handlers/ --include="*.py" | grep "from\|import\|cmd_\|def \|BTN\|booking" | head -20',
  // Check the main menu or booking_flow for the pending bookings trigger
  'grep -rn "pending\|Pending" /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -15',
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
