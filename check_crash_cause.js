const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('cat /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null | grep -E "Traceback|Error|NameError|import|SyntaxError" | tail -5; echo "---"; ls -la /root/Sales-Tele-Bot_refactored/logs/bot.log', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      // Check the actual journal for the latest error
      c.exec('journalctl -u psvibe-bot-refactored -n 15 --no-pager 2>&1 | grep -v "Started\\|Stopped\\|Scheduled\\|Main process\\|result" | tail -10', (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => { console.log('Journal:\n' + o2); c.end(); });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
