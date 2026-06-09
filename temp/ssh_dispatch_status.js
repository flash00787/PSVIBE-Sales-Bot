const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const keyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(keyPath, 'utf8');

const conn = new Client();
conn.on('ready', () => {
  conn.exec('python3 /root/coordination/dispatch_manager.py --status', (err, stream) => {
    if (err) {
      console.error('=== RESULT: ERROR ||| SSH exec failed: ' + err.message + ' ===');
      conn.end();
      process.exit(1);
      return;
    }
    let stdout = '';
    let stderr = '';
    stream.on('data', (data) => { stdout += data.toString(); });
    stream.stderr.on('data', (data) => { stderr += data.toString(); });
    stream.on('close', (code) => {
      const output = stdout + (stderr ? '\n--- STDERR ---\n' + stderr : '');
      console.log(output);
      if (code === 0) {
        console.log('=== RESULT: OK ===');
      } else {
        console.log('=== RESULT: ERROR ||| Exit code: ' + code + ' ===');
      }
      conn.end();
    });
  });
}).on('error', (err) => {
  console.error('=== RESULT: ERROR ||| SSH connection failed: ' + err.message + ' ===');
  process.exit(1);
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
