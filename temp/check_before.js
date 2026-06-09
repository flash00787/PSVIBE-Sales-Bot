const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Get the BTN_PAY_DONE section and review start
  conn.exec("sed -n '1180,1250p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('=== LINES 1180-1250 ===');
      console.log(out);
      console.log('=== END ===');
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
