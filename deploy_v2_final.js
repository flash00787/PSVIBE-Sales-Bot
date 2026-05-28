const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== PRE-DEPLOY BACKUP ==="',
    'BACKUP_FILE=/root/backups/predeploy5-$(date +%Y%m%d_%H%M%S).tar.gz',
    'tar czf $BACKUP_FILE -C /root Sales-Tele-Bot_refactored 2>/dev/null',
    'echo "Backup: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"',
    '',
    'echo "=== STAGING DEPLOY ==="',
    'rsync -a --delete /root/Sales-Tele-Bot_refactored/ /root/staging/bot_src/',
    'echo "Staging synced."',
    '',
    'echo "=== STAGING VERIFY ==="',
    'cd /root/staging/bot_src && python3 -c "from bot import main, keep_alive, ensure_sheet_headers; print(\'IMPORT OK\')" 2>&1 || echo "STAGING IMPORT NOTE: .env needed"',
    '',
    'echo "=== RUNNING SERVICE CHECK ==="',
    'systemctl status psvibe-bot-refactored --no-pager | head -5',
    'echo "Log error count: $(grep -ci ERROR /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo 0)"',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 20000});
