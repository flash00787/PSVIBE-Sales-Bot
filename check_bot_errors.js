const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Check recent errors in sales bot
  'journalctl -u psvibe-sale-bot.service --since "30 min ago" --no-pager 2>/dev/null | grep -i "error\\|exception\\|traceback\\|unauthorized\\|access\\|denied\\|forbidden" | tail -30',
  // Check customer bot errors
  'journalctl -u psvibe_customer_bot.service --since "30 min ago" --no-pager 2>/dev/null | grep -i "error\\|exception\\|traceback\\|unauthorized\\|access\\|denied\\|forbidden\\|ai\\|openai\\|gemini" | tail -30',
  // Check the current allowed IDs in the main.py source
  'grep -n "ALLOWED\\|allowed\\|authorized\\|access.*id\\|user.*id" /root/psvibe-sale-bot/main.py 2>/dev/null | head -20',
  // Check .env for settings
  'cat /root/psvibe-sale-bot/.env 2>/dev/null | grep -v "^#" | head -20',
  // Check customer_bot settings
  'grep -rn "ALLOWED\\|allowed\\|authorized\\|AI\\|ai\\|openai\\|gemini" /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null | head -20',
  // Check the recently running main.py for the function that checks allowed users
  'grep -n "def.*check\\|def.*auth\\|def.*allow" /root/psvibe-sale-bot/main.py 2>/dev/null | head -10',
  // Check if bot is actually responding
  'curl -s -X POST "https://api.telegram.org/bot$(grep BOT_TOKEN /root/psvibe-sale-bot/.env 2>/dev/null | cut -d= -f2)/getMe" 2>/dev/null | head -2',
];

conn.on('ready', () => {
  let results = [];
  let idx = 0;

  function runNext() {
    if (idx >= commands.length) {
      console.log(JSON.stringify(results, null, 2));
      conn.end();
      return;
    }
    const cmd = commands[idx];
    conn.exec(cmd, (err, stream) => {
      let stdout = '', stderr = '';
      if (err) {
        results.push({ cmd, error: err.message, stdout: '', stderr: '' });
        idx++; runNext();
        return;
      }
      stream.on('data', (d) => stdout += d.toString());
      stream.stderr.on('data', (d) => stderr += d.toString());
      stream.on('close', () => {
        results.push({ cmd, stdout: stdout.trim(), stderr: stderr.trim() });
        idx++; runNext();
      });
    });
  }
  runNext();
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
