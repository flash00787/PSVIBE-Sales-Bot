const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const LOGDIR = '/root/Aung\\ Chan\\ Myint/monitoring';

const conn = new Client();

conn.on('ready', () => {
  const logFiles = ['health.log', 'resources.log', 'ratelimit.log', 'uptime.log'];
  let pending = logFiles.length;

  logFiles.forEach((file) => {
    conn.exec(`tail -3 ${LOGDIR}/${file} 2>&1`, (err, stream) => {
      let out = '';
      if (err) { out = `EXEC_ERR: ${err.message}`; }
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => out += d.toString());
      stream.on('close', () => {
        console.log(`=== ${file} (last 3 lines) ===`);
        console.log(out.trim());
        console.log('');
        pending--;
        if (pending === 0) conn.end();
      });
    });
  });
}).connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: KEY,
  readyTimeout: 15000
});
