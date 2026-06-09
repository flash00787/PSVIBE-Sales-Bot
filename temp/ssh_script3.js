const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('SSH: Connected');
  const cmd = `grep -in "pay" /root/psvibe-sales-bot/bot/handlers/sales.py | head -50`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('close', (code) => {
      console.log('CODE:', code);
      console.log('OUT:', out.substring(0, 3000));
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
