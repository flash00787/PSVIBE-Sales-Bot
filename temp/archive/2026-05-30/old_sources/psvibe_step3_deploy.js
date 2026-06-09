const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.error('Connected. Running deploy script...');

  conn.exec('/root/staging/scripts/deploy.sh /root/staging/bot_src /root/Sales-Tele-Bot_refactored 2>&1', { pty: true }, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err.message); conn.end(); process.exit(1); return; }
    let out = '';
    stream.on('data', d => { out += d; process.stderr.write(d); });
    stream.on('close', (code, signal) => {
      console.error('\n--- Deploy finished with code:', code, 'signal:', signal, '---');
      console.log('===DEPLOY_OUTPUT_START===');
      console.log(out);
      console.log('===DEPLOY_OUTPUT_END===');
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', e => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
