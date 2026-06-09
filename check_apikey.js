const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Find _API_KEY definition
  'grep -n "_API_KEY" /root/psvibe-sales-bot/bot/__init__.py | head -10',
  // Get the _API_KEY assignment context
  'grep -n -B2 -A2 "_API_KEY" /root/psvibe-sales-bot/bot/__init__.py | head -20',
  // Check for any API_KEY env var loading
  'grep -n "API_KEY\|api_key" /root/psvibe-sales-bot/bot/__init__.py | head -15',
  // Check the beginning of __init__.py for globals
  'head -50 /root/psvibe-sales-bot/bot/__init__.py',
  // Check if _API_KEY is defined after imports
  'grep -n "^_API_KEY" /root/psvibe-sales-bot/bot/__init__.py',
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
