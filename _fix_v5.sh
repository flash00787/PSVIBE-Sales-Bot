#!/bin/bash
set -e

# Step 1: Write patch script to main VPS
node -e "
const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();
c.on('ready', () => {
  const script = [
    'sshpass -p Freedom2024#RevFlash scp -o StrictHostKeyChecking=no /tmp/fix_remote.sh root@38.60.254.31:/tmp/fix_remote.sh',
    'sshpass -p Freedom2024#RevFlash ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 bash /tmp/fix_remote.sh'
  ].join(' && ');
  c.exec(script, (e,s) => { let o=''; s.on('data',d=>o+=d); s.stderr.on('data',d=>o+='[E]'+d); s.on('close',()=>{console.log(o);c.end();process.exit(0);}); });
}).on('error', e => { console.error('ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
"

echo "DONE"
