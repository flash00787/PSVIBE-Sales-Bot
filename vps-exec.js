const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const cmd = process.argv[2];
if (!cmd) { console.error('Usage: node vps-exec.js <command>'); process.exit(1); }

const conn = new Client();
let output = '';
let stderr = '';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) throw err;
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { stderr += data.toString(); });
    stream.on('close', (code) => {
      process.stdout.write(output);
      if (stderr) process.stderr.write(stderr);
      conn.end();
      process.exit(code);
    });
  });
});

conn.on('error', (err) => {
  process.stderr.write('SSH ERROR: ' + err.message + '\n');
  process.exit(1);
});

conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY });
