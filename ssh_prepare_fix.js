const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - deploying fix');

  const commands = [
    // 1. Read the current main.py to apply precise edits
    'grep -n "telegram.error" /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1',
    'grep -n "async def error_handler" /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1',
    'grep -n "from telegram" /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1 | head -5',
    'grep -n "while True:" /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1',
    'grep -n "time.sleep" /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1',
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n>>> ${cmd.slice(0, 100)}...`);
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
