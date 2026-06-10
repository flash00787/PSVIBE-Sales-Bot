#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const HOST = '5.223.81.16';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function sshExec(cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, { timeout }, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let out = '', errOut = '';
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => errOut += d.toString());
        stream.on('close', code => { conn.end(); resolve({ stdout: out, stderr: errOut, code }); });
      });
    });
    conn.on('error', reject);
    conn.connect({ host: HOST, username: 'root', privateKey: KEY, readyTimeout: 15000 });
  });
}

(async () => {
  // Check quality gate status
  console.log('--- Quality Gate Status ---');
  let r = await sshExec('cat /root/coordination/quality_gate.json');
  console.log(r.stdout);

  // Check if auto_bug_fixer exists
  console.log('--- auto_bug_fixer.py ---');
  r = await sshExec('ls -la /root/coordination/auto_bug_fixer.py 2>&1');
  console.log(r.stdout);

  // Check pattern files
  console.log('--- Pattern Files ---');
  r = await sshExec('ls -la /root/coordination/KNOWN_BUG_PATTERNS.md /root/coordination/ERROR_PATTERNS.md 2>&1');
  console.log(r.stdout);
  
  // Check for ERROR_PATTERNS.md content
  r = await sshExec('head -5 /root/coordination/ERROR_PATTERNS.md 2>&1 || echo "NOT FOUND"');
  console.log('ERROR_PATTERNS.md:', r.stdout);
})().catch(e => console.error(e));
