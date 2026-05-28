#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '167.71.196.120';
const USER = 'root';
const KEY_PATH = path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa');

const command = process.argv.slice(2).join(' ');
if (!command) {
  console.error('Usage: node ssh_exec.js <command>');
  process.exit(1);
}

const conn = new Client();

conn.on('ready', () => {
  conn.exec(command, { pty: true }, (err, stream) => {
    if (err) {
      console.error('EXEC ERROR:', err.message);
      conn.end();
      process.exit(1);
    }
    let stdout = '';
    let stderr = '';
    stream.on('data', (data) => { stdout += data.toString(); });
    stream.stderr.on('data', (data) => { stderr += data.toString(); });
    stream.on('close', (code, signal) => {
      process.stdout.write(stdout);
      if (stderr) process.stderr.write(stderr);
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH CONNECTION ERROR:', err.message);
  process.exit(1);
});

conn.connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH),
  readyTimeout: 15000,
});
