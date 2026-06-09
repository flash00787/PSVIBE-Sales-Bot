const { Client } = require('ssh2');
const fs = require('fs');

const commands = `
echo "=== BACKUPS IN /root/backups/ ==="
ls -laht /root/backups/ 2>/dev/null | head -30
echo "---BACKUP_SIZE---"
du -sh /root/backups/ 2>/dev/null
echo "=== STAGING ==="
ls -laR /root/staging/ 2>/dev/null | head -50
echo "---STAGING_SIZE---"
du -sh /root/staging/ 2>/dev/null
echo "=== ROOT .BAK FILES ==="
find /root -maxdepth 4 -name "*.bak*" -type f 2>/dev/null | grep -v "__pycache__" | head -20
echo "---BACKUP_EXTS---"
find /root -maxdepth 4 -name "*.backup*" -type f 2>/dev/null | head -10
echo "=== OLD BOT DIRECTORIES ==="
for d in /root/psvibe-sale-bot /root/psvibe-sales-bot /root/Sales-Tele-Bot; do
  echo "---DIR:$d---"
  ls -la "$d" 2>/dev/null && echo "EXISTS" || echo "GONE"
done
echo "=== OTHER PROJECTS ==="
echo "---DIR:/root/ACM-Personal-Wallet---"
ls -la /root/ACM-Personal-Wallet/ 2>/dev/null
echo "---DIR:/root/YYO-Personal-Wallet---"
ls -la /root/YYO-Personal-Wallet/ 2>/dev/null
echo "---DIR:/opt/construction-bot---"
ls -la /opt/construction-bot/ 2>/dev/null
echo "---DIR:/opt/yyo-personal-wallet---"
ls -la /opt/yyo-personal-wallet/ 2>/dev/null
echo "=== TRASH ==="
echo "---TRASH:psvibe-sales-bot---"
ls -la /root/psvibe-sales-bot/trash/ 2>/dev/null
echo "=== DOCKER STATUS ==="
docker ps --format "{{.Names}} {{.Status}} {{.Image}}" 2>/dev/null
echo "=== PROCESSES ==="
ps aux | grep -E "python|node" | grep -v grep | head -20
`;

const conn = new Client();
conn.on('ready', () => {
  conn.exec(commands, (err, stream) => {
    if (err) { console.log('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out || '(empty)'); conn.end(); });
  });
});
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
