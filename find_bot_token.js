const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Get BOT_TOKEN from /etc/psvibe/secrets.env
  'grep BOT_TOKEN /etc/psvibe/secrets.env 2>/dev/null | cut -d= -f2',
  // Check systemd service file for BOT_TOKEN
  'grep BOT_TOKEN /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null | cut -d= -f2',
  // Check hardcoded in main.py
  'grep -n BOT_TOKEN /root/psvibe-sale-bot/main.py 2>/dev/null | head -5',
  // Check hardcoded in app.py
  'grep -n BOT_TOKEN /root/psvibe-sale-bot/bot/app.py 2>/dev/null | head -5',
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
