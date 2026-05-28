const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - restoring original file');
  
  const commands = [
    // Check for backup
    'ls -la /root/Personal-Wallet-Tele-Bot-2/bot/main.py.* /root/Personal-Wallet-Tele-Bot-2/bot/main.py.bak 2>&1',
    // Check git
    'cd /root/Personal-Wallet-Tele-Bot-2 && git status 2>&1 | head -5',
    // If git, restore
    'cd /root/Personal-Wallet-Tele-Bot-2 && git checkout bot/main.py 2>&1',
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n>>> ${cmd.slice(0, 80)}...`);
    conn.exec(cmd, { pty: false }, (err, stream) => {
      if (err) {
        console.log('EXEC ERROR:', err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        console.log(output.trim() || '(no output)');
        runNext();
      });
    });
  }

  runNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
