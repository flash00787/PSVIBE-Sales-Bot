const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check MySQL schema for console_booking
  'mysql -u root psvibe_api -e "DESCRIBE console_booking" 2>/dev/null | cat',
  // Check bot logs for error or traceback 
  'journalctl -u psvibe-sale-bot -n 50 --no-pager 2>&1 | tail -30',
  // Check for any Python tracebacks in bot log
  'journalctl -u psvibe-sale-bot --since "1 hour ago" --no-pager 2>&1 | grep -i -A5 "error\|traceback\|exception" | tail -40',
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
