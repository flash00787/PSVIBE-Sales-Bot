const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Read the full function to get exact text for the swap
  conn.exec("sed -n '1180,1218p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('=== SECTION 1180-1218 ===');
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
