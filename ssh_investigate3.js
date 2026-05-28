const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  
  const commands = [
    // Get full tracebacks from the log
    'grep -B5 -A10 "telegram.error.Conflict" /root/Personal-Wallet-Tele-Bot-2/bot/wallet_bot.log 2>&1 | tail -80',
    // Check system memory
    'free -h 2>&1',
    // Check dmesg for OOM killer
    'dmesg -T 2>&1 | grep -i -E "oom|killed|memory" | tail -30',
    // Check if other bot instances are running
    'ps aux | grep python 2>&1',
    // Check the bot.lock file
    'cat /root/Personal-Wallet-Tele-Bot-2/bot/bot.lock 2>&1; ls -la /root/Personal-Wallet-Tele-Bot-2/bot/bot.lock 2>&1',
    // Check other service statuses
    'systemctl list-units --type=service --state=running | grep -i -E "wallet|tele|bot|psvibe" 2>&1',
    'systemctl status psvibe-wallet 2>&1 | head -20',
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n===== COMMAND ${idx}: ${cmd.slice(0, 80)}... =====`);
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
        console.log(output.substring(0, 3000) || '(no output)');
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
