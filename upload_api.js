const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const baseDir = '/home/node/.openclaw/workspace/psvibe_api';
const files = [
  'config.py',
  'sheets_client.py',
  'models.py',
  'app.py',
  'requirements.txt',
  'Dockerfile',
];

// Build commands
let cmds = ['mkdir -p /root/psvibe_api_server'];

for (const f of files) {
  const content = fs.readFileSync(path.join(baseDir, f));
  const b64 = content.toString('base64');
  cmds.push(`echo '${b64}' | base64 -d > /root/psvibe_api_server/${f}`);
}
// Copy SA key
cmds.push('cp /root/psvibe_sales_bot/service_account.json /root/psvibe_api_server/');
// Verify
cmds.push('ls -la /root/psvibe_api_server/');

const fullCmd = cmds.join(' && ');

conn.on('ready', () => {
  console.log('SSH CONNECTED, uploading...');
  conn.exec(fullCmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let data = ''; let stderrData = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { stderrData += chunk.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      if (stderrData) console.error('STDERR:', stderrData);
      console.log(data);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('CONN ERROR:', err); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
