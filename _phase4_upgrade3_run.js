#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const { execSync } = require('child_process');

const b64 = execSync('base64 -w0 /home/node/.openclaw/workspace/_upgrade3_receipt.py').toString().trim();

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Step 1: Backup + transfer + run upgrade3 script
const cmd = 
  'cp /root/psvibe-sales-bot/bot/handlers/members.py /root/psvibe-sales-bot/bot/handlers/members.py.bak_kora_phase4 && ' +
  'echo "' + b64 + '" | base64 -d > /tmp/upgrade3.py && ' +
  'python3 /tmp/upgrade3.py && ' +
  'echo "---SYNTAX CHECK---" && ' +
  'python3 -c "import ast; ast.parse(open(\'/root/psvibe-sales-bot/bot/handlers/members.py\').read()); print(\'Syntax OK\')"';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log(out);
      if (code) console.error('Exit code:', code);
      conn.end();
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 60000 });
