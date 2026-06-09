const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('SSH: Connected');
  const cmd = `grep -n "^async def\|^def " /root/psvibe-sales-bot/bot/handlers/sales.py | grep -i "pay\|confirm\|review\|amount\|method"`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('close', (code) => {
      console.log('CODE:', code);
      console.log('OUT:', out);
      conn.end();
    });
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += 'STDERR:' + d; });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
