const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH Connected — attempting to install jsonwebtoken');

  const installCmd = 'cd /root/Sales-Tele-Bot/api_server/ && npm install jsonwebtoken';
  
  conn.exec(installCmd, { pty: false }, (err, stream) => {
    if (err) {
      console.error('SSH Exec Error:', err);
      conn.end();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      console.log('--- NPM INSTALL OUTPUT ---');
      console.log(output.trim() || '(No output)');
      console.log('-------------------------------');
      console.log(`Exit code: ${code}`);
      conn.end();
      console.log('SSH connection closed. Done!');
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
