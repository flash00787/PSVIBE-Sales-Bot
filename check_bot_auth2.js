const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Recent sales bot logs - look for Boss's ID (6296803251)
  'journalctl -u psvibe-sale-bot.service --since "1 hour ago" --no-pager 2>/dev/null | grep -i "629680\\|access\\|denied\\|allow\\|block" | tail -20',
  // Check the fetch_allowed_staff_ids function implementation
  'grep -A 15 "def fetch_allowed_staff_ids" /root/psvibe-sale-bot/bot/app.py 2>/dev/null',
  // Also check if it's imported from somewhere else
  'grep -rn "fetch_allowed_staff_ids" /root/psvibe-sale-bot/ 2>/dev/null | head -10',
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
