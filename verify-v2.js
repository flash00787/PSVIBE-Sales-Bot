const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('cd /root/psvibe_sales_bot && /root/venv/bin/python3 -c "import sys; sys.path.insert(0, \".\"); from customer_bot import *; print(\"V2 import OK\")" 2>&1; echo "===CUST SERVICE==="; systemctl status psvibe_customer_bot --no-pager 2>&1 | head -20; echo "===CUST LOG==="; journalctl -u psvibe_customer_bot --no-pager -n 10 2>&1', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
