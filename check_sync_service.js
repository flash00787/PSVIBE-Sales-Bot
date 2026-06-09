const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  'find /root/psvibe-sale-bot -name "sync_service.py" -o -name "db_client.py" 2>/dev/null',
  'ls -la /root/psvibe-sale-bot/bot/ 2>/dev/null | head -30',
  'grep -n "sync_service\\|db_client" /root/psvibe-sale-bot/main.py 2>/dev/null | head -10',
  'grep -n "sync_service\\|db_client" /root/psvibe-sale-bot/app.py 2>/dev/null | head -10',
  'grep -rn "sync_service\\|db_client" /root/Aung*Chan*/Sales-Tele-Bot_refactored/main.py 2>/dev/null | head -10',
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
