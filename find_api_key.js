const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Check EnvironmentFile in systemd service
  'grep EnvironmentFile /etc/systemd/system/psvibe-api.service 2>/dev/null',
  // Get API_KEY from /etc/psvibe/secrets.env
  'grep API_KEY /etc/psvibe/secrets.env 2>/dev/null | cut -d= -f2',
  // Get API_KEY from /root/psvibe_api_server/.env
  'grep API_KEY /root/psvibe_api_server/.env 2>/dev/null | cut -d= -f2',
  // Check API_KEY hardcoded in app.py
  'grep -n API_KEY /root/psvibe_api_server/app.py 2>/dev/null | head -5',
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
