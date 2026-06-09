const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec('cat /root/psvibe-sales-bot/customer_bot/booking.py', (err, stream) => {
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.on('close', () => {
      fs.writeFileSync('/home/node/.openclaw/workspace/.tmp/vps_files/customer_booking.py', data);
      console.log(`Wrote customer_booking.py (${data.length} bytes)`);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 15000 });
