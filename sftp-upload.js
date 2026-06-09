#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err.message); conn.end(); process.exit(1); }
    const localPath = '/home/node/.openclaw/workspace/insert_endpoints.py';
    const remotePath = '/root/psvibe_api_server/insert_endpoints.py';
    sftp.fastPut(localPath, remotePath, (err2) => {
      if (err2) { console.error('Put error:', err2.message); conn.end(); process.exit(1); }
      console.log('Uploaded insert_endpoints.py');
      // Now run it
      conn.exec('cd /root/psvibe_api_server && python3 insert_endpoints.py', (err3, stream) => {
        if (err3) { console.error('Exec error:', err3.message); conn.end(); process.exit(1); }
        let out = '';
        stream.on('data', (d) => { out += d.toString(); });
        stream.stderr.on('data', (d) => { out += d.toString(); });
        stream.on('close', (code) => {
          console.log('Run exit:', code);
          console.log(out);
          conn.end();
        });
      });
    });
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
