const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('SSH: Connected');
  // Check BTN_CONFIRM_SAVE and NAV_ROW definitions in bot/__init__.py or bot/app.py
  const cmd = `grep -n "BTN_CONFIRM_SAVE\|NAV_ROW\|BTN_NO_MORE\|BTN_PAY_DONE\|BTN_ADD_PAY" /root/psvibe-sales-bot/bot/app.py | head -20`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('close', (code) => {
      console.log('CODE:', code);
      console.log(out);
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
