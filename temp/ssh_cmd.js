const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec('python3 /root/coordination/fix_protocol.py --complete 2>&1', (err, stream) => {
    if (err) { console.error('ERR:', err.message); conn.end(); return; }
    stream.on('data', d => result += d);
    stream.stderr.on('data', d => result += d);
    stream.on('close', () => { console.log(result); conn.end(); });
  });
});
conn.on('error', e => console.error('CONN:', e.message));
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
