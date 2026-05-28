const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== V.2 STATUS CHECK ==="',
    'systemctl is-active psvibe-bot-refactored',
    'echo "---LOG---"',
    'tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log',
    'echo "---PID---"',
    'systemctl show -p MainPID psvibe-bot-refactored 2>/dev/null',
    'echo "---MEM---"',
    'ps aux | grep "python3" | grep -v grep | awk \'{print \$6/1024 " MB"}\'',
    'echo "---ERROR COUNT---"',
    'grep -ci "ERROR\\|Traceback\\|Error" /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo "0"',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
