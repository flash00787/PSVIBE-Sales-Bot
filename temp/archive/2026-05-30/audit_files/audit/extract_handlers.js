const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`cd /root/psvibe-sale-bot && grep -rn "def cmd_staff_kpi\\|def cmd_payroll[^_]\\|def cmd_setattend[^_]\\|def cmd_cancel_booking\\|def cmd_finance[^_]\\|def cmd_stocktoday\\|def cmd_staff_kpi_cmd\\|def cmd_kpi_cmd\\|def cmd_payroll_cmd\\|def cmd_setattend_cmd\\|def cmd_admin\\b" bot/handlers/ bot/__init__.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let data = '';
    stream.on('data', chunk => data += chunk.toString());
    stream.on('close', () => {
      console.log(data || 'NO OUTPUT');
      conn.end();
      process.exit(0);
    });
  });
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
