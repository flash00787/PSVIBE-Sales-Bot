const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Check V.2 log for similar NetworkError
  c.exec("grep -c 'NetworkError\\|AsyncLibraryNotFound' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null; grep 'NetworkError\\|AsyncLibraryNotFound' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | tail -3; echo '---'; grep 'NetworkError' /root/Sales-Tele-Bot/logs/bot.log 2>/dev/null | tail -3", (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
