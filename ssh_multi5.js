const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  'cat /root/psvibe-sales-bot/bot/__init__.py | tail -n +200 | head -300',
  'grep -n "def api_\|def cmd_\|def fetch_\|_cfg\|_load_members\|_bg_cache\|GSheet\|gspread\|_get_cfg" /root/psvibe-sales-bot/bot/__init__.py | head -50',
  'cat /root/psvibe-sales-bot/bot/api_client.py | tail -n +200',
  'grep -n "@app\\." /root/psvibe_api_server/app.py | head -80',
  'cat /root/psvibe_api_server/app.py | head -200',
  'cat /root/psvibe-sales-bot/bot/__init__.py | grep -n "_HAS_API\|api_client\|fallback\|GOOGLE_SHEET\|SHEET_\|gs_read\|gs_write" | head -30',
];

const results = [];

function runCmd(client, cmd, idx) {
  return new Promise((resolve) => {
    client.exec(cmd, (err, stream) => {
      if (err) { results[idx] = 'ERR:' + err.message; resolve(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => { results[idx] = out; resolve(); });
    });
  });
}

const conn = new Client();
conn.on('ready', async () => {
  console.log('Connected');
  for (let i = 0; i < COMMANDS.length; i += 2) {
    const batch = [];
    for (let j = i; j < i+2 && j < COMMANDS.length; j++) batch.push(runCmd(conn, COMMANDS[j], j));
    await Promise.all(batch);
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < COMMANDS.length; i++) {
    console.log('\n===', i+1, '===');
    console.log((results[i] || 'NO OUTPUT').substring(0, 6000));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
