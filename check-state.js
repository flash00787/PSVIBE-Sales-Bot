const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('cat /root/psvibe_sales_bot/customer_bot/_v1_compat.py 2>/dev/null || echo "NOT_FOUND"; echo "===V1_STATUS==="; ls -la /proc/226924/exe 2>/dev/null || echo "PID_226924_gone"; cat /proc/226924/cmdline 2>/dev/null | tr "\\0" " " || echo "no_cmdline"; echo; echo "===CUSTBOT_DIR==="; ls -la /root/psvibe_sales_bot/customer_bot/', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
