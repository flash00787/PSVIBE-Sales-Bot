const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  
  const commands = [
    'cat /root/Personal-Wallet-Tele-Bot/bot/.env 2>&1 | grep TOKEN',
    'cat /root/Personal-Wallet-Tele-Bot-2/bot/.env 2>&1 | grep TOKEN',
    'grep -c "Conflict" /root/Personal-Wallet-Tele-Bot-2/bot/wallet_bot.log 2>&1',
    'grep -c "Conflict" /root/Personal-Wallet-Tele-Bot/bot/wallet_bot.log 2>&1',
    'ls -la /root/Personal-Wallet-Tele-Bot-2/bot/venv/lib/python3.12/site-packages/telegram/ext/_updater.py 2>&1',
    'head -5 /root/Personal-Wallet-Tele-Bot-2/bot/venv/lib/python3.12/site-packages/telegram/ext/_updater.py 2>&1',
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n===== COMMAND ${idx}: ${cmd.slice(0, 100)}... =====`);
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
        console.log(output.substring(0, 2000) || '(no output)');
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
