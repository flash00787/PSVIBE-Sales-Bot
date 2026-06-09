const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();

conn.on('ready', () => {
  conn.exec(`find /root/psvibe-sales-bot -name "*.py" -type f 2>/dev/null | sort`, (err, stream) => {
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.on('close', () => {
      console.log(data);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('Error:', err.message); process.exit(1); });
conn.connect({ host: HOST, username: USER, privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 15000 });
