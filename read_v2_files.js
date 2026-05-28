const { Client } = require('ssh2');
const fs = require('fs');

const files = [
  '/root/staging/bot_src/bot/handlers/console.py',
  '/root/staging/bot_src/bot/handlers/console_mgmt.py',
  '/root/staging/bot_src/bot/handlers/games.py',
  '/root/staging/bot_src/bot/handlers/ginst.py'
];

let completed = 0;
const results = {};

files.forEach((file, idx) => {
  const conn = new Client();
  conn.on('ready', () => {
    conn.exec(`cat ${file}`, (err, stream) => {
      if (err) { results[file] = `ERROR: ${err}`; checkDone(); return; }
      let output = '';
      stream.on('data', (d) => { output += d.toString(); });
      stream.stderr.on('data', (d) => { output += d.toString(); });
      stream.on('close', () => {
        results[file] = output;
        checkDone();
      });
    });
  });
  conn.on('error', (err) => { results[file] = `ERROR: ${err.message}`; checkDone(); });
  conn.connect({
    host: '167.71.196.120',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
  });
});

function checkDone() {
  completed++;
  if (completed === files.length) {
    files.forEach(f => {
      console.log(`\n===== ${f} =====`);
      console.log(results[f] || '(empty)');
    });
  }
}
