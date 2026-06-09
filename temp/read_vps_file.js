const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  conn.exec('sed -n "1140,1280p" /root/psvibe-sales-bot/bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { console.error('STDERR:', data.toString()); });
    stream.on('close', (code, signal) => {
      console.log('EXIT:', code);
      console.log('=== FILE CONTENT ===');
      console.log(output);
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
