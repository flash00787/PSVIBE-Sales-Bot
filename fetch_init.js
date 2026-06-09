const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const TARGETS = [
  { remote: '/root/staging/bot_src/bot/__init__.py', local: '/tmp/v2_bot_init.py' },
];
conn.on('ready', () => {
  let remaining = TARGETS.length;
  TARGETS.forEach(({ remote, local }) => {
    conn.sftp((err, sftp) => {
      if (err) { remaining--; if (remaining === 0) conn.end(); return; }
      sftp.fastGet(remote, local, (err) => {
        console.log(err ? `ERR ${remote}: ${err.message}` : `OK: ${remote}`);
        remaining--;
        if (remaining === 0) conn.end();
      });
    });
  });
});
conn.on('error', (err) => { console.error('Error:', err.message); process.exit(1); });
conn.connect({ host: '167.71.196.120', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 15000 });
