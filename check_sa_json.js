const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec("ls -la /root/Sales-Tele-Bot_refactored/service_account.json 2>/dev/null; cat /root/Sales-Tele-Bot_refactored/service_account.json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print('client_email:', d.get('client_email','?')); print('private_key_id:', d.get('private_key_id','?')[:10]+'...'); print('keys:', list(d.keys()))\"", (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
