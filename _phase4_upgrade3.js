#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Write the Python modification script to VPS
const pyScript = fs.readFileSync('/home/node/.openclaw/workspace/_upgrade3_receipt.py', 'utf8');

const cmd = 'cat > /tmp/upgrade3.py << \'ENDOFPYTHON\'\n' + pyScript + '\nENDOFPYTHON\n' +
  'echo "--- Running upgrade 3 ---"\n' +
  'cp /root/psvibe-sales-bot/bot/handlers/members.py /root/psvibe-sales-bot/bot/handlers/members.py.bak_kora_phase4\n' +
  'python3 /tmp/upgrade3.py\n' +
  'echo "--- Testing syntax ---"\n' +
  'python3 -c "import ast; ast.parse(open(\'/root/psvibe-sales-bot/bot/handlers/members.py\').read()); print(\'Syntax OK\')"\n';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log(out);
      conn.end();
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 60000 });
