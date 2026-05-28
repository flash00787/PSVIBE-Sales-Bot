const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Check available backups ==="
ls -la /root/backups/ | grep Sales-Tele-Bot_refactored

echo ""
echo "=== Restoring from latest backup ==="
cd /root
rm -rf /root/Sales-Tele-Bot_refactored
BACKUP=\$(ls -t /root/backups/predeploy_Sales-Tele-Bot_refactored_*.tar.gz | head -1)
echo "Using backup: \$BACKUP"
tar -xzf "\$BACKUP"
echo "Done."

echo ""
echo "=== Verify restore ==="
ls -la /root/Sales-Tele-Bot_refactored/bot/handlers/ | head -5
ls -la /root/Sales-Tele-Bot_refactored/main.py
ls -la /root/Sales-Tele-Bot_refactored/.env

echo ""
echo "=== NOW do a SAFE deploy using rsync ==="
# Use rsync instead of rm+cp to preserve .env and avoid directory issues
rsync -av --delete --exclude='.env' --exclude='logs/*' --exclude='bot_status.log' --exclude='psvibe.db*' --exclude='__pycache__' --exclude='*.pyc' /root/staging/bot_src/ /root/Sales-Tele-Bot_refactored/ 2>&1

echo ""
echo "=== Re-verify files after rsync ==="
ls -la /root/Sales-Tele-Bot_refactored/bot/handlers/ | wc -l
echo "handler files:"
ls /root/Sales-Tele-Bot_refactored/bot/handlers/*.py 2>&1 | wc -l
ls -la /root/Sales-Tele-Bot_refactored/main.py
ls -la /root/Sales-Tele-Bot_refactored/.env
ls -la /root/Sales-Tele-Bot_refactored/keep_alive.py

echo ""
echo "=== Start service ==="
systemctl start psvibe-bot-refactored
sleep 10
systemctl is-active psvibe-bot-refactored && echo "SERVICE IS ACTIVE ✓" || echo "SERVICE FAILED ✗"
`;
  conn.exec(cmds, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); process.exit(0); });
  });
}).connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
