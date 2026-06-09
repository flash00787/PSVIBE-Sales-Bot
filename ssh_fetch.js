const { Client } = require('ssh2');
const fs = require('fs');

// Read these files entirely
const FILES = [
  '/root/psvibe-sales-bot/bot/__init__.py',
  '/root/psvibe-sales-bot/customer_bot/api.py',
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
  for (let i = 0; i < FILES.length; i++) {
    await runCmd(conn, 'cat ' + FILES[i], i);
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < FILES.length; i++) {
    console.log('\n=== FILE:', FILES[i], '===');
    console.log((results[i] || 'NO OUTPUT'));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
