const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

conn.on('ready', () => {
  const commands = `
    echo "=== sales.py receipt-related code ===";
    grep -n "receipt\|RECEIPT\|save_receipt\|voucher_id" /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py | head -60;
    echo "=== _sale_bg function ===";
    awk 'BEGIN{c=0} /async def _sale_bg/,/^async def /{c++; if(c<300) print; else exit}' /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py;
    echo "=== save_receipt_json calls ===";
    grep -n "save_receipt_json" /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py;
    echo "=== app.py - check how it runs ===";
    head -100 /root/Sales-Tele-Bot_refactored/bot/app.py;
    echo "=== receipt dir contents ===";
    ls -la /root/Sales-Tele-Bot_refactored/bot/receipts/;
    echo "=== existing api_server or not ===";
    ls -la /root/Sales-Tele-Bot_refactored/api_server/ 2>/dev/null || echo "NO api_server dir yet";
    echo "=== Check if Caddy or nginx is installed ===";
    which caddy 2>/dev/null || echo "NO CADDY";
    which nginx 2>/dev/null || echo "NO NGINX";
    which python3 2>/dev/null;
    python3 --version 2>/dev/null;
    which uvicorn 2>/dev/null;
    echo "=== Check what's running port 8000 ===";
    ss -tlnp | grep 8000 || echo "NOTHING on 8000";
    echo "=== Check systemd services ===";
    systemctl list-units --type=service --state=running | grep -i "bot\|sales\|psvib" || echo "NO matching services";
    echo "=== main.py entry point ===";
    cat /root/Sales-Tele-Bot_refactored/main.py;
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
