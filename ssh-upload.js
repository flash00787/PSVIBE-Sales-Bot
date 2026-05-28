const { Client } = require('ssh2');
const fs = require('fs');

const localPath = process.argv[2];
const remotePath = process.argv[3];
const chmod = process.argv[4];

if (!localPath || !remotePath) {
  console.error('Usage: node ssh-upload.js <local_path> <remote_path> [chmod_mode]');
  process.exit(1);
}

const content = fs.readFileSync(localPath);
const b64 = content.toString('base64');

const conn = new Client();
conn.on('ready', () => {
  let cmd = `base64 -d > ${remotePath}`;
  if (chmod) {
    cmd = `base64 -d > ${remotePath} && chmod ${chmod} ${remotePath}`;
  }
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('Exec error:', err.message); conn.end(); return; }
    let errOut = '';
    stream.stderr.on('data', (d) => errOut += d.toString());
    stream.on('close', (code) => {
      if (errOut) console.error('STDERR:', errOut.trim());
      if (code !== 0) {
        console.error('Exit code:', code);
        process.exit(code);
      } else {
        console.log('OK: uploaded', localPath, '->', remotePath);
      }
      conn.end();
    });
    stream.stdin.write(b64 + '\n');
    stream.stdin.end();
  });
}).on('error', (err) => { console.error('SSH error:', err.message); process.exit(1); }).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
