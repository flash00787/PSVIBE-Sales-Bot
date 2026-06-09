const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();

conn.on('ready', () => {
  const commands = [
    'ls -la /root/Aung\\ Chan\\ Myint/monitoring/ 2>&1',
    'ls -la /root/Aung\\ Chan\\ Myint/ 2>&1 | head -20',
    // Run the check_alerts.sh script from the correct path
    'cd /root/Aung\\ Chan\\ Myint/monitoring && chmod +x check_alerts.sh 2>/dev/null; bash check_alerts.sh 2>&1 || echo "SCRIPT_EXIT:$?"',
  ];

  let idx = 0;
  runNext();

  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx];
    conn.exec(cmd, (err, stream) => {
      let out = '';
      if (err) { out = `EXEC_ERR: ${err.message}`; }
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => out += d.toString());
      stream.on('close', () => {
        console.log(`=== CMD ${idx} ===`);
        console.log(out.trim());
        console.log('');
        idx++;
        runNext();
      });
    });
  }
}).connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: KEY,
  readyTimeout: 15000
});
