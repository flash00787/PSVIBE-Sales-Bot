#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const PORT = 22;
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const cmd = process.argv[2];
if (!cmd) {
  console.error('Usage: node vps.js "<command>"');
  process.exit(1);
}

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, { pty: false }, (err, stream) => {
    if (err) {
      console.error('Exec error:', err.message);
      conn.end();
      process.exit(1);
    }
    let stdout = '';
    let stderr = '';
    stream.on('data', (data) => { stdout += data.toString(); });
    stream.stderr.on('data', (data) => { stderr += data.toString(); });
    stream.on('close', (code) => {
      if (stdout) process.stdout.write(stdout);
      if (stderr) {
        // Skip common SSH noise
        if (!stderr.includes('Pseudo-terminal will not be allocated') &&
            !stderr.includes('mesg: ttyname failed')) {
          process.stderr.write(stderr);
        }
      }
      conn.end();
      process.exit(code || 0);
    });
  });
}).connect({
  host: HOST,
  port: PORT,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH),
  readyTimeout: 15000,
});
