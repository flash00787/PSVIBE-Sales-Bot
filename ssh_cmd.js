const { Client } = require('ssh2');
const fs = require('fs');

const cmd = process.argv[2];
if (!cmd) { console.log("Usage: node ssh_cmd.js '<command>'"); process.exit(1); }

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += 'STDERR:' + d.toString(); });
    stream.on('close', (code) => {
      console.log(out.trimEnd());
      conn.end();
      if (code !== 0) process.exitCode = code;
    });
  });
});
conn.on('error', (e) => { console.error('SSH error:', e); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
