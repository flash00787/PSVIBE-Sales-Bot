const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  conn.exec('grep -n "^async def \\|^def " /root/staging/monolithic_ref/main.py | grep -i "console\\|game\\|ginst\\|con_mgmt"', (err, stream) => {
    if (err) throw err;
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', () => {
      console.log('=== V1 CONSOLE/GAME FUNCTIONS ===');
      console.log(output);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('SSH error:', err); process.exit(1); });

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
