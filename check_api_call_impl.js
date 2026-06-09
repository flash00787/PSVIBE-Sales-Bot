const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Show api_fetch_allowed_staff_ids
  'sed -n "250,270p" /root/psvibe-sale-bot/bot/api_client.py 2>/dev/null',
  // Show full _api_call
  'sed -n "30,80p" /root/psvibe-sale-bot/bot/api_client.py 2>/dev/null',
  // Check if API_BASE_URL is set correctly in .env
  'grep API_BASE_URL /root/psvibe-sale-bot/.env 2>/dev/null',
  // Check if there's an API_KEY in the bot's environment
  'cat /proc/$(systemctl show psvibe-sale-bot.service --property MainPID --value)/environ 2>/dev/null | tr "\\0" "\\n" | grep -i "api.*key\\|api_key"',
  // Check full recent logs for the sales bot
  'journalctl -u psvibe-sale-bot.service --since "30 min ago" --no-pager 2>/dev/null | grep -v "getUpdates\\|Background\\|HTTP Request" | tail -30',
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
