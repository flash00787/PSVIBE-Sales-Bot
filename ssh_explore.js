const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec('head -100 /root/psvibe_sales_bot/app.py && echo "===DIVIDER===" && head -100 /root/psvibe_sales_bot/handlers/members.py && echo "===DIVIDER===" && head -100 /root/psvibe_sales_bot/handlers/console.py', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { console.error('STDERR:', chunk.toString()); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log(data.substring(0, 15000));
      conn.end();
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
