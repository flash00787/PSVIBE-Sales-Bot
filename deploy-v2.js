#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const endpointsContent = fs.readFileSync('/home/node/.openclaw/workspace/new_game_endpoints.py', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err.message); conn.end(); process.exit(1); }

    // Upload endpoint file
    const ws = sftp.createWriteStream('/tmp/new_endpoints_raw.py');
    ws.on('close', () => {
      console.log('Uploaded endpoint file');

      // Upload the Python inserter script
      const inserterCode = `
with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# Remove any old new_game_endpoints import
content = content.replace('import new_game_endpoints\\n', '')
content = content.replace('import new_game_endpoints', '')

# Read the endpoint code to insert
with open('/tmp/new_endpoints_raw.py', 'r') as f:
    endpoints = f.read()

# Find where to insert
marker = 'import patch_routes'
idx = content.find(marker)
if idx == -1:
    print('ERROR: marker not found')
else:
    new_content = content[:idx] + endpoints + '\\n\\n' + content[idx:]
    with open('/root/psvibe_api_server/app.py', 'w') as f:
        f.write(new_content)
    print('OK: inserted ' + str(len(endpoints.split(chr(10)))) + ' lines of endpoints')
    print('Total lines: ' + str(new_content.count(chr(10))))
`.trim();

      const ws2 = sftp.createWriteStream('/tmp/insert_endpoints.py');
      ws2.on('close', () => {
        console.log('Uploaded inserter script');
        conn.exec('python3 /tmp/insert_endpoints.py', (err2, stream) => {
          let out = '';
          stream.on('data', (d) => out += d.toString());
          stream.stderr.on('data', (d) => out += d.toString());
          stream.on('close', (code) => {
            console.log('Insert exit:', code);
            console.log(out);
            conn.end();
          });
        });
      });
      ws2.end(Buffer.from(inserterCode, 'utf8'));
    });
    ws.end(Buffer.from(endpointsContent, 'utf8'));
  });
});
conn.on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY, readyTimeout: 15000 });
