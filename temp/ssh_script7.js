const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('SSH: Connected');
  const cmd = `grep -rn "BTN_CONFIRM_SAVE\\|BTN_NO_MORE\\|BTN_PAY_DONE\\|BTN_ADD_PAY\\|NAV_ROW" /root/psvibe-sales-bot/bot/__init__.py 2>/dev/null; grep -rn "BTN_CONFIRM_SAVE\\|BTN_NO_MORE\\|BTN_PAY_DONE\\|BTN_ADD_PAY\\|NAV_ROW" /root/psvibe-sales-bot/bot/buttons.py 2>/dev/null; grep -rn "BTN_CONFIRM_SAVE" /root/psvibe-sales-bot/bot/ 2>/dev/null | head -10`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('close', (code) => {
      console.log('CODE:', code);
      console.log(out.substring(0, 3000));
      conn.end();
    });
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += 'STDERR:' + d; });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
