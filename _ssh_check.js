const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const keyPath = path.join(process.env.HOME || '/home/node', '.ssh', 'id_rsa');
const privateKey = fs.readFileSync(keyPath, 'utf8');

// First, SSH into main VPS
const mainClient = new Client();
mainClient.on('ready', () => {
  console.log('[MAIN] Connected to 5.223.81.16');
  
  // Then from main VPS, SSH into Yangon VPS
  mainClient.exec(
    `ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 '
      echo "=== SERVICE STATUS ==="
      systemctl status ibet789-bot 2>&1 | head -30
      echo ""
      echo "=== LOGS (last 50 lines) ==="
      journalctl -u ibet789-bot --no-pager -n 50 2>&1
      echo ""
      echo "=== .ENV FILE ==="
      cat /opt/ibet789-bot/.env 2>&1
      echo ""
      echo "=== PROCESS CHECK ==="
      ps aux | grep -E "node|chrome|puppeteer" | grep -v grep | head -10
      echo ""
      echo "=== BOT JS VERSION ==="
      head -5 /opt/ibet789-bot/bot.js
      echo ""
      echo "=== disk/free ==="
      df -h / | tail -1
      free -h | head -2
    '`,
    (err, stream) => {
      if (err) {
        console.error('[EXEC ERROR]', err.message);
        mainClient.end();
        process.exit(1);
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += '[STDERR] ' + data.toString(); });
      stream.on('close', (code) => {
        console.log(output);
        console.log(`\n[EXIT CODE] ${code}`);
        mainClient.end();
        process.exit(0);
      });
    }
  );
}).on('error', (err) => {
  console.error('[MAIN CONNECT ERROR]', err.message);
  process.exit(1);
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 10000,
});
