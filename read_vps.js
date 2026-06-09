const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

conn.on('ready', () => {
  const commands = `
    echo "=== PATH MAPPING ===";
    cat /root/Sales-Tele-Bot_refactored/path_mapping.json;
    echo "=== COORDINATION ===";
    cat /root/Sales-Tele-Bot_refactored/COORDINATION.md;
    echo "=== save_receipt_json ===";
    grep -n "def save_receipt_json" /root/Sales-Tele-Bot_refactored/bot/sales.py;
    echo "=== get_receipt_url ===";
    grep -n "def get_receipt_url\|def _api_base\|def get_receipt_kb" /root/Sales-Tele-Bot_refactored/bot/__init__.py;
    echo "=== ALL receipt references in sales.py ===";
    grep -n "receipt\|RECEIPT" /root/Sales-Tele-Bot_refactored/bot/sales.py;
    echo "=== _sale_bg function ===";
    awk '/def _sale_bg/,/^def /' /root/Sales-Tele-Bot_refactored/bot/sales.py | head -200;
    echo "=== Full save_receipt_json function ===";
    awk '/def save_receipt_json/,/^def /' /root/Sales-Tele-Bot_refactored/bot/sales.py;
    echo "=== api_server dir ===";
    ls -la /root/Sales-Tele-Bot_refactored/api_server/ 2>/dev/null || echo "NO api_server dir";
    echo "=== env file /etc/environment ===";
    cat /etc/environment 2>/dev/null || echo "NO /etc/environment";
    echo "=== Caddy config ===";
    cat /etc/caddy/Caddyfile 2>/dev/null || echo "NO caddy";
    echo "=== nginx config ===";
    ls /etc/nginx/sites-enabled/ 2>/dev/null;
    cat /etc/nginx/sites-enabled/* 2>/dev/null || echo "NO nginx sites";
    echo "=== Existing receipts dir ===";
    ls -la /root/Sales-Tele-Bot_refactored/receipts/ 2>/dev/null || echo "NO receipts dir";
    echo "=== RECEIPT_DOMAIN env check ===";
    grep -r "RECEIPT_DOMAIN\|RECEIPT_SECRET" /root/Sales-Tele-Bot_refactored/ --include="*.py" --include="*.env" 2>/dev/null;
    echo "=== All py files in api_server ===";
    find /root/Sales-Tele-Bot_refactored/api_server/ -name "*.py" 2>/dev/null || echo "NO files";
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
