#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const command = process.argv[2];
if (!command) { console.error('Usage: node vps_exec.js "<cmd>"'); process.exit(1); }

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  conn.exec(command, { pty: false }, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let stdout = '', stderr = '';
    stream.on('data', d => { stdout += d.toString(); });
    stream.stderr.on('data', d => { stderr += d.toString(); });
    stream.on('close', (code) => {
      if (stdout) process.stdout.write(stdout);
      if (stderr) process.stderr.write(stderr);
      conn.end();
      process.exit(code || 0);
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
