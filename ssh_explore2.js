const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec('ls -la /root/psvibe_sales_bot/ && echo "===BACKUPS===" && ls -la /root/backups/', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { console.error('STDERR:', chunk.toString()); });
    stream.on('close', () => {
      console.log(data);
      conn.end();
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
