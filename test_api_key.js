const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Get the second API_KEY from secrets.env (the actual API key)
  'grep ^API_KEY /etc/psvibe/secrets.env 2>/dev/null',
  // Test fetch_allowed_staff_ids with it
  // First get the key, then test
  'API_KEY=$(grep ^API_KEY /etc/psvibe/secrets.env | tail -1 | cut -d= -f2) && curl -s "http://localhost:8000/api/fetch_allowed_staff_ids?api_key=$API_KEY"',
  // Also test health
  'curl -s http://localhost:8000/api/health',
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
