const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

conn.on('ready', () => {
  console.log('SSH:CONNECTED');
  
  const cmd = `
echo "=== FULL FILE LIST ==="
find /root/psvibe-sales-bot -type f -name "*.py" | sort
echo "=== DIR STRUCTURE ==="
find /root/psvibe-sales-bot -type d | sort
`;
  
  conn.exec(cmd, (err, stream) => {
    if (err) { console.log('ERROR:', err.message); conn.end(); return; }
    let data = '';
    stream.on('data', d => data += d.toString());
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
    stream.on('close', (code) => {
      console.log(data);
      console.log('EXIT:', code);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('SSH_ERROR:', err.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
