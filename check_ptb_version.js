const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('/root/Sales-Tele-Bot/.venv/bin/python3 -c "import telegram; print(telegram.__version__)" 2>&1', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log('PTB version:', o.trim()); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
