const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH CONNECTED');

  const commands = [
    "systemctl list-units --type=service --all | grep -i 'ps\|sales\|customer\|vibe\|bot' || echo 'NO SERVICES'",
    "systemctl list-unit-files | grep -i 'ps\|sales\|customer\|vibe\|bot' || echo 'NO UNIT FILES'",
    "ls -la /etc/systemd/system/*.service 2>/dev/null || echo 'NO SERVICE FILES'",
    "crontab -l 2>/dev/null || echo 'NO CRONTAB'",
    "cat /etc/systemd/system/*.service 2>/dev/null || echo 'NO SERVICE FILES'",
    "uptime",
    "free -m",
    "df -h",
    "du -sh /root/Sales-Tele-Bot/",
    "du -sh /root/Sales-Tele-Bot/.venv/ 2>/dev/null",
    "ps aux | grep python || echo 'NO PYTHON'",
    "ls -la /root/Sales-Tele-Bot/logs/",
    "git -C /root/Sales-Tele-Bot log --oneline -10 2>/dev/null || echo 'NO GIT'",
    "git -C /root/Sales-Tele-Bot status --short 2>/dev/null || echo 'NO GIT'",
    "python3 --version",
    "pip3 list 2>/dev/null | head -30",
    "cat /root/Sales-Tele-Bot/start.sh",
    "cat /root/Sales-Tele-Bot/update_bot.sh",
    "find /root/Sales-Tele-Bot -name '*.backup*' -o -name '*.bak.*' -o -name '*.backup.*' | wc -l",
    "ls -la /root/Sales-Tele-Bot/*.backup* /root/Sales-Tele-Bot/*.bak* 2>/dev/null | head -30",
  ];

  let idx = 0;
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log('\n=== #' + idx + ': ' + cmd.substring(0, 100) + ' ===');
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('err:', err); conn.end(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => {
        console.log(out.slice(0, 50000));
        runNext();
      });
    });
  }
  runNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  password: 'Freedom2024#RevFlash',
  readyTimeout: 15000,
});
