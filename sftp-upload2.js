#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Read the Python script
const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/insert_endpoints.py', 'utf8');
const scriptBuf = Buffer.from(scriptContent, 'utf8');

const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err.message); conn.end(); process.exit(1); }
    const writeStream = sftp.createWriteStream('/root/psvibe_api_server/insert_endpoints.py');
    writeStream.on('close', () => {
      console.log('Script uploaded');
      // Make executable and run
      conn.exec('chmod +x /root/psvibe_api_server/insert_endpoints.py && cd /root/psvibe_api_server && python3 insert_endpoints.py', (err3, stream) => {
        let out = '';
        stream.on('data', (d) => out += d.toString());
        stream.stderr.on('data', (d) => out += d.toString());
        stream.on('close', (code) => {
          console.log('Exit:', code);
          console.log(out);
          conn.end();
        });
      });
    });
    writeStream.on('error', (e) => { console.error('Write error:', e.message); conn.end(); process.exit(1); });
    writeStream.end(scriptBuf);
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
