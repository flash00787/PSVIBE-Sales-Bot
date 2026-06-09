const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
    rsync -av /root/staging/bot_src/bot/handlers/main_menu.py /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py && \
    rsync -av /root/staging/bot_src/bot/handlers/commands.py /root/Sales-Tele-Bot_refactored/bot/handlers/commands.py && \
    rsync -av /root/staging/bot_src/bot/handlers/help.py /root/Sales-Tele-Bot_refactored/bot/handlers/help.py && \
    echo "=== RSYNC DONE ===" && \
    systemctl restart psvibe-bot-refactored.service && \
    echo "=== RESTART DONE ===" && \
    sleep 3 && \
    tail -20 /root/Sales-Tele-Bot_refactored/logs/bot.log
  `, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d);
    stream.stderr.on('data', d => out += d);
    stream.on('close', () => { console.log(out); conn.end(); process.exit(0); });
  });
}).connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
