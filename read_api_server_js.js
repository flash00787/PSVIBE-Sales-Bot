const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH Connected — attempting to copy and read api_server.js');

  const sourcePath = '/root/Sales-Tele-Bot/api_server/api_server.js';
  const destPath = '/tmp/api_server.js';

  conn.exec(`cp ${sourcePath} ${destPath} && cat ${destPath}`, { pty: false }, (err, stream) => {
    if (err) {
      console.error('SSH Exec Error:', err);
      conn.end();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      console.log('--- REMOTE FILE CONTENT ---');
      console.log(output.trim() || '(No content)');
      console.log('-----------------------------');
      
      // Clean up the copied file
      conn.exec(`rm ${destPath}`, (err2, stream2) => {
        if (err2) console.error('Cleanup Error:', err2);
        conn.end();
        console.log('SSH connection closed. Done!');
      });
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
