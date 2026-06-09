const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`grep -n 'worksheet\\|setting_sh\\|staff_sh\\|member_sh\\|games_sh\\|console_sh\\|booking_sh\\|receipt_sh\\|attendance_sh\\|salary_sh\\|bonus_sh\\|promo_sh\\|food_sh\\|\\.worksheet(' /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null | head -200`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/sheet_refs.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
