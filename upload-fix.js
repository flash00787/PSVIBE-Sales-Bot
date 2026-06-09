#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err.message); conn.end(); process.exit(1); }
    const fileContent = fs.readFileSync('/home/node/.openclaw/workspace/fix_app.py');
    const ws = sftp.createWriteStream('/tmp/fix_app.py');
    ws.on('close', () => {
      console.log('Uploaded fix script');
      conn.exec('python3 /tmp/fix_app.py', (err2, stream) => {
        let out = '';
        stream.on('data', (d) => out += d.toString());
        stream.stderr.on('data', (d) => out += d.toString());
        stream.on('close', (code) => {
          console.log('Fix exit:', code);
          console.log(out);
          // Validate
          conn.exec('cd /root/psvibe_api_server && /root/psvibe_api_server/venv/bin/python3 -c "import py_compile; py_compile.compile(\'app.py\', doraise=True); print(\'Syntax OK\')" 2>&1', (err3, stream2) => {
            let out2 = '';
            stream2.on('data', (d) => out2 += d.toString());
            stream2.stderr.on('data', (d) => out2 += d.toString());
            stream2.on('close', (code3) => { console.log('Validate:', code3, out2); conn.end(); });
          });
        });
      });
    });
    ws.end(fileContent);
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
