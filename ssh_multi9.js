const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  "awk '/def _load_cfg|def _load_members|def _bg_cache|_cfg_cache|_members_cache|_BK_TTL|_CFG_TTL|_MEMBERS_TTL|def _get_cfg|def _get_member|def fetch_allowed_staff|ALLOWED_USER/' /root/psvibe-sales-bot/bot/__init__.py",
  "awk '/def _load_cfg/,/^def /' /root/psvibe-sales-bot/bot/__init__.py | head -40",
  "awk '/def _bg_cache_refresh/,/^def /' /root/psvibe-sales-bot/bot/__init__.py | head -50",
  "awk '/def fetch_allowed_staff_ids/,/^def /' /root/psvibe-sales-bot/bot/__init__.py | head -30",
  "awk '/auth_middleware|fetch_allowed|ALLOWED/' /root/psvibe-sales-bot/bot/app.py",
  "awk '/def _api_get/,/^def /' /root/psvibe-sales-bot/customer_bot/api.py",
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
  for (let i = 0; i < COMMANDS.length; i += 2) {
    const batch = [];
    for (let j = i; j < i+2 && j < COMMANDS.length; j++) batch.push(runCmd(conn, COMMANDS[j], j));
    await Promise.all(batch);
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < COMMANDS.length; i++) {
    console.log('\n===', i+1, '===');
    console.log((results[i] || 'NO OUTPUT'));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
