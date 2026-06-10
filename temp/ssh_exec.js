#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const cmd = process.argv.slice(2).join(' ');
if (!cmd) { console.log('Usage: node ssh_exec.js <command>'); process.exit(1); }

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, { timeout: 60000 }, (err, stream) => {
    if (err) { conn.end(); console.error('Exec error:', err); process.exit(1); }
    let out = '', errOut = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { errOut += d.toString(); });
    stream.on('close', (code) => {
      if (out) process.stdout.write(out);
      if (errOut) process.stderr.write(errOut);
      conn.end();
      process.exit(code);
    });
  });
});
conn.on('error', e => { console.error('SSH error:', e); process.exit(1); });
conn.connect({ host: HOST, username: USER, privateKey: KEY, readyTimeout: 15000 });
