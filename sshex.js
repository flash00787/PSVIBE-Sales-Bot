const { Client } = require('./node_modules/ssh2');
const fs = require('fs');

const cmd = process.argv[2];
if (!cmd) { console.error('Usage: node sshex.js <command>'); process.exit(1); }

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); process.exit(1); }
    let out = '', errOut = '';
    stream.on('close', (code) => {
      conn.end();
      process.stdout.write(out);
      if (errOut) process.stderr.write(errOut);
      process.exit(code || 0);
    }).on('data', (data) => { out += data.toString(); })
      .stderr.on('data', (data) => { errOut += data.toString(); });
  });
}).on('error', (e) => { console.error('SSH ERROR:', e.message); process.exit(2); })
  .connect({
    host: '5.223.81.16', port: 22, username: 'root',
    privateKey: fs.readFileSync('./.ssh/id_rsa'),
    readyTimeout: 15000,
  });
