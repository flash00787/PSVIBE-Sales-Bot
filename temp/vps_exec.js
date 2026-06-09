#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const command = process.argv[2];
if (!command) {
  console.error('Usage: vps_exec.js "<command>"');
  process.exit(1);
}

const conn = new Client();
conn.on('ready', () => {
  conn.exec(command, { timeout: 120000 }, (err, stream) => {
    if (err) {
      console.error('EXEC ERROR:', err.message);
      conn.end();
      process.exit(1);
    }
    let stdout = '';
    let stderr = '';
    stream.on('data', (data) => stdout += data.toString());
    stream.stderr.on('data', (data) => stderr += data.toString());
    stream.on('close', (code) => {
      process.stdout.write(stdout);
      if (stderr) process.stderr.write(stderr);
      conn.end();
      process.exit(code || 0);
    });
  });
});
conn.on('error', (err) => {
  console.error('SSH ERROR:', err.message);
  process.exit(1);
});
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 30000,
  keepaliveInterval: 10000,
});
