const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  console.log('SSH CONNECTED');
  conn.exec('cat /root/agent_output/function_map.json', (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { console.error('STDERR:', chunk.toString()); });
    stream.on('close', (code) => {
      console.log('EXIT CODE:', code);
      console.log('DATA:\n', data);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('CONN ERROR:', err); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
