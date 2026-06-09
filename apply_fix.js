const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check if coordination scripts exist
  'ls /root/coordination/fix_protocol.py /root/coordination/verify_agent.py /root/coordination/auto_doc_updater.py 2>&1',
  // Run fix_protocol --start
  'python3 /root/coordination/fix_protocol.py --start /root/psvibe-sales-bot/bot/handlers/admin_bookings.py 2>&1',
  // Restart the bot
  'systemctl restart psvibe-sale-bot 2>&1',
  // Check status
  'sleep 3 && systemctl status psvibe-sale-bot 2>&1 | head -8',
  // Check logs
  'journalctl -u psvibe-sale-bot -n 20 --no-pager 2>&1 | tail -10',
  // Run fix_protocol --complete
  'python3 /root/coordination/fix_protocol.py --complete 2>&1',
  // Verify
  'python3 /root/coordination/verify_agent.py verify --agent fix-pending-bookings 2>&1',
  // Auto-doc
  'python3 /root/coordination/auto_doc_updater.py --summary "Fixed pending bookings display bug: changed direct dict access to safe .get() with defaults in admin_bookings.py (commits e576321 and 2e8fb8a). API returns correct fields via patch_routes.py _map_booking_row. Bot restarted to pick up latest code." 2>&1',
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
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
