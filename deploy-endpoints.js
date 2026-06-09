#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const endpointsContent = fs.readFileSync('/home/node/.openclaw/workspace/new_game_endpoints.py', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  // Step 1: Upload new_game_endpoints.py via SFTP
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err.message); conn.end(); process.exit(1); }
    const ws = sftp.createWriteStream('/root/psvibe_api_server/new_game_endpoints.py');
    ws.on('close', () => {
      console.log('File uploaded');
      // Step 2: Add import line to app.py
      conn.exec("python3 -c \"\nwith open('/root/psvibe_api_server/app.py', 'r') as f:\n    content = f.read()\n# Add import before 'import patch_routes'\ncontent = content.replace('import patch_routes', 'import new_game_endpoints\\nimport patch_routes')\nwith open('/root/psvibe_api_server/app.py', 'w') as f:\n    f.write(content)\nprint('app.py updated')\n\"", (err2, stream) => {
        let out = '';
        stream.on('data', (d) => out += d.toString());
        stream.stderr.on('data', (d) => out += d.toString());
        stream.on('close', (code) => {
          console.log('Exit:', code);
          console.log(out);
          // Step 3: Validate
          conn.exec('cd /root/psvibe_api_server && python3 -c "import py_compile; py_compile.compile(\'app.py\', doraise=True); print(\'Syntax OK\')"', (err3, stream2) => {
            let out2 = '';
            stream2.on('data', (d) => out2 += d.toString());
            stream2.stderr.on('data', (d) => out2 += d.toString());
            stream2.on('close', (code2) => { console.log('Validate exit:', code2, out2); conn.end(); });
          });
        });
      });
    });
    ws.on('error', (e) => { console.error('Write error:', e.message); conn.end(); process.exit(1); });
    ws.end(Buffer.from(endpointsContent, 'utf8'));
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
