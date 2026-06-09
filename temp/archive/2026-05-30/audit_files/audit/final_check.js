const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`grep -rn 'save_attendance\|create_booking\|end_booking\|cancel_booking' /root/psvibe_api_server/ 2>/dev/null | head -30 && echo "===" && grep -rn 'save_attendance\|create_booking\|end_booking\|cancel_booking' /root/psvibe-sale-bot/api/ 2>/dev/null | head -30 && echo "===" && ls /root/psvibe_api_server/*.py /root/psvibe_api_server/routes/*.py 2>/dev/null`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
