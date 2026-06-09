const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', async () => {
  console.log('SSH:CONNECTED');
  
  // Upload fixed script
  const content = fs.readFileSync('/home/node/.openclaw/workspace/arch_mapper.py');
  const b64 = content.toString('base64');
  
  await new Promise((resolve) => {
    conn.exec(`mkdir -p /root/coordination/findings && echo "${b64}" | base64 -d > /root/coordination/arch_mapper.py && echo "OK"`, (err, stream) => {
      let d = '';
      stream.on('data', dd => d += dd.toString());
      stream.on('close', () => { console.log('UPLOAD:', d.trim()); resolve(); });
    });
  });
  
  // Run just the dep-text test  
  console.log('\n--- Running dep-text ---');
  await new Promise((resolve) => {
    conn.exec('cd /root/coordination && python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text findings/arch_report.txt 2>&1', (err, stream) => {
      let d = '';
      stream.on('data', dd => { d += dd.toString(); process.stdout.write(dd.toString()); });
      stream.stderr.on('data', dd => { d += dd.toString(); process.stderr.write(dd.toString()); });
      stream.on('close', (c) => { console.log('\nEXIT:', c); resolve(); });
    });
  });
  
  conn.end();
});

conn.on('error', e => { console.error(e); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
