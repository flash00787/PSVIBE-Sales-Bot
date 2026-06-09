const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  conn.exec('cat /root/psvibe-sale-bot/.env; echo "===SEPARATOR==="; cat /root/psvibe_api_server/config.py; echo "===SEPARATOR==="; ls /root/psvibe-sale-bot/customer_bot/.env 2>/dev/null && cat /root/psvibe-sale-bot/customer_bot/.env || echo "customer_bot .env not in sales-bot dir"; ls /root/psvibe_customer_bot/.env 2>/dev/null && cat /root/psvibe_customer_bot/.env || echo "customer_bot .env not in root dir"', (err, stream) => {
    if (err) { console.error('exec err:', err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[ERR]' + d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
