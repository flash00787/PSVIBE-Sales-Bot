#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const localFile = process.argv[2];
const remotePath = process.argv[3];

if (!localFile || !remotePath) {
  console.error('Usage: node scp_upload.js <local_file> <remote_path>');
  process.exit(1);
}

const content = fs.readFileSync(localFile);
const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error(err); conn.end(); process.exit(1); }
    const w = sftp.createWriteStream(remotePath);
    w.on('close', () => { conn.end(); process.exit(0); });
    w.on('error', (e) => { console.error(e); conn.end(); process.exit(1); });
    w.end(content);
  });
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
