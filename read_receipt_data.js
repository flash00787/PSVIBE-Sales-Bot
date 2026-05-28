const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

conn.on('ready', () => {
  const commands = `
    echo "=== save_receipt_json call context in sales.py ===";
    awk 'NR>=880 && NR<=930' /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py;
    echo "=== The full sales recording section around receipt ===";
    sed -n '850,910p' /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py;
    echo "=== Check main.py for env sourcing ===";
    cat /root/Sales-Tele-Bot_refactored/.env;
    echo "=== Check if pm2/supervisor is running ===";
    ps aux | grep -i "python\|bot\|main" | grep -v grep;
    echo "=== Process running on VPS ===";
    ps aux | head -5;
    echo "=== Python packages available ===";
    pip3 list 2>/dev/null | grep -i "fastapi\|uvicorn\|flask\|aiohttp\|httpx" || echo "NO web framework found";
  `;
  
  conn.exec(commands, (err, stream) => {
    if (err) { console.error(err.message); process.exit(1); }
    let output = '';
    stream.on('data', d => output += d.toString());
    stream.stderr.on('data', d => output += d.toString());
    stream.on('close', () => {
      console.log(output);
      conn.end();
    });
  });
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey,
});
