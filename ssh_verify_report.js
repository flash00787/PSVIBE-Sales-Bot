const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec('head -5 /tmp/audit_all_fixes.txt && echo "..." && tail -10 /tmp/audit_all_fixes.txt', { pty: false }, (err, stream) => {
    if (err) throw err;
    stream.on('data', (data) => { process.stdout.write(data.toString()); });
    stream.stderr.on('data', (data) => { process.stderr.write(data.toString()); });
    stream.on('close', () => { conn.end(); process.exit(0); });
  });
});
conn.on('error', (err) => { console.error(err.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: fs.readFileSync(KEY_PATH) });
