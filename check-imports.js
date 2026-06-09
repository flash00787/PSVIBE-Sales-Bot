const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('echo "=== V2 HANDLERS IMPORT CHECK ==="; grep -n "from \\._v1_compat\|from \\.handlers\|from \\.api\|from \\.ai\|from \\.booking\|import _v1_compat" /root/psvibe_sales_bot/customer_bot/handlers.py | head -20; echo "=== V2 API USED? ==="; grep -n "from \\._v1_compat\|import.*_v1_compat" /root/psvibe_sales_bot/customer_bot/api.py | head -5; echo "=== V2 AI USED? ==="; grep -n "from \\._v1_compat\|import.*_v1_compat" /root/psvibe_sales_bot/customer_bot/ai.py | head -5; echo "=== MAIN.PY FULL ==="; cat /root/psvibe_sales_bot/customer_bot/main.py; echo "=== WHAT DOES STAFF BOT MAIN IMPORT ==="; grep "import\|from" /root/psvibe_sales_bot/main.py | head -10', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
