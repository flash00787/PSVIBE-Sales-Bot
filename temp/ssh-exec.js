const { Client } = require('ssh2');
const fs = require('fs');

const cmd = process.argv[2];
if (!cmd) {
  console.error('Usage: node ssh-exec.js "command"');
  process.exit(1);
}

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) throw err;
    let output = '';
    let errOutput = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { errOutput += data.toString(); });
    stream.on('close', (code) => {
      if (errOutput) process.stderr.write(errOutput);
      process.stdout.write(output);
      conn.end();
      process.exit(code);
    });
  });
});
conn.on('error', (err) => {
  console.error('SSH Error:', err.message);
  process.exit(1);
});
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
