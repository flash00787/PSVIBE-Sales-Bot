const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // Get ConversationHandler blocks and BTN_* definitions
  conn.exec(`cd /root/psvibe-sale-bot && echo "===CONVERSATION_HANDLERS===" && grep -n -A 50 "ConvHandler\|ConversationHandler" bot/handlers/*.py | head -400 && echo "===BTN_CONSTANTS===" && grep -rn "BTN_" bot/bot.py bot/config.py 2>/dev/null | head -200 && echo "===MAIN_CONV===" && grep -rn "conv_handler\|add_handler\|Application.builder\|ConversationHandler" bot/main.py 2>/dev/null | head -50`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let data = '';
    stream.on('data', chunk => data += chunk.toString());
    stream.on('close', () => {
      // Parse and extract ConversationHandler entries
      const parts = data.split('===CONVERSATION_HANDLERS===');
      if (parts.length > 1) {
        const rest = parts[1].split('===BTN_CONSTANTS===');
        fs.writeFileSync('/home/node/.openclaw/workspace/audit/conv_handlers.txt', rest[0]);
        if (rest.length > 1) {
          const rest2 = rest[1].split('===MAIN_CONV===');
          fs.writeFileSync('/home/node/.openclaw/workspace/audit/btn_constants.txt', rest2[0]);
          if (rest2.length > 1) {
            fs.writeFileSync('/home/node/.openclaw/workspace/audit/main_conv.txt', rest2[1]);
          }
        }
      }
      console.log('Done. Files written.');
      conn.end();
      process.exit(0);
    });
  });
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
