#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== All handler functions in V.2 ==='
for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do
  echo "--- $(basename $f) ---"
  grep -n "^async def\\|^def " "$f" | grep -o 'def [a-z_][a-z_]*' | sed 's/def //'
done | sort -u

echo ''
echo '=== Functions called by app.py ConversationHandler ==='
grep -oP 'CommandHandler\("\\w+", \\w+\\)|MessageHandler\\([^,]+,\\s*\\w+\\)|CallbackQueryHandler\\(\\w+' /root/Sales-Tele-Bot_refactored/bot/app.py | grep -oP ', \\w+' | sed 's/, //' | sort -u
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
