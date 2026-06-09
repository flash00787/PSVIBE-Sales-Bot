const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('SSH connected');
  // Run multiple commands
  conn.exec('cat /root/Sales-Tele-Bot_refactored/bot/__init__.py', (err, stream) => {
    if (err) throw err;
    let output = '';
    stream.on('data', (d) => { output += d.toString(); });
    stream.stderr.on('data', (d) => { output += d.toString(); });
    stream.on('close', () => {
      console.log('=== bot/__init__.py ===');
      console.log(output);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('SSH error:', err); process.exit(1); });
conn.connect({
  host: '167.71.196.120', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
