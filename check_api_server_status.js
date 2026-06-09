const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

conn.on('ready', () => {
  conn.exec(`
    ls -la /root/Sales-Tele-Bot_refactored/api_server/ 2>/dev/null
    echo "---"
    find /root/Sales-Tele-Bot_refactored/api_server/ -type f 2>/dev/null || echo "EMPTY"
  `, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out);
      conn.end();
    });
  });
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey,
});
