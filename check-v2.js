const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('ls -la /root/psvibe_sales_bot/customer_bot/booking.py 2>/dev/null || echo "NO booking.py"; echo "===INIT==="; cat /root/psvibe_sales_bot/customer_bot/__init__.py; echo "===MAIN==="; head -30 /root/psvibe_sales_bot/customer_bot/main.py; echo "===SERVICE==="; systemctl status psvibe_sales_bot 2>/dev/null || echo "no systemd service"; echo "===PROC==="; ps aux | grep "python3.*psvibe" | grep -v grep', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
