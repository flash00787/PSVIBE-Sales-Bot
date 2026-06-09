const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  'cat /root/psvibe_api_server/app.py | grep -n "sheet\|Sheet\|GSheet\|gspread\|_use_mysql\|from_mysql" | head -40',
  'sed -n "920,1000p" /root/psvibe_api_server/app.py',
  'sed -n "1384,1450p" /root/psvibe_api_server/app.py',
  'grep -n "B30\|B29\|B31\|allowed_user\|ALLOWED_USER\|fetch_allowed_staff\|staff.*id" /root/psvibe_api_server/app.py | head -20',
  'sed -n "900,940p" /root/psvibe_api_server/app.py',
  'cat /root/psvibe_api_server/app.py | grep -n "# ═\|def _\|_use_mysql" | head -40',
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
    console.log((results[i] || 'NO OUTPUT').substring(0, 5000));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
