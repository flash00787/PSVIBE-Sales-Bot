const { Client } = require('ssh2');
const fs = require('fs');
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec('wc -l /root/psvibe-sales-bot/bot/handlers/*.py | sort -rn | head -10', (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let d = '';
    stream.on('data', dd => d += dd.toString());
    stream.on('close', () => { console.log(d); conn.end(); });
  });
});
conn.on('error', e => { console.error(e); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
