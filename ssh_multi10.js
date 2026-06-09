const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  'cat /root/psvibe_api_server/server.log | wc -l',
  'cat /root/psvibe_api_server/server.log | grep -c "GET\|POST\|PUT\|DELETE\|PATCH"',
  'cat /root/psvibe_api_server/server.log | grep -oP "\\d{2}:\\d{2}:\\d{2}" | sort | uniq -c | sort -rn | head -20',
  'cat /root/psvibe_api_server/server.log | grep "500" | tail -20',
  'cat /root/psvibe_api_server/server.log | wc -l; echo "---"; head -5 /root/psvibe_api_server/server.log; echo "---"; tail -5 /root/psvibe_api_server/server.log',
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
