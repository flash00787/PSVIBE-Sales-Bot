const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  
  const commands = [
    'docker exec openclaw-openclaw-gateway-1 grep -i "embedding" /tmp/openclaw/openclaw-2026-05-26.log || true',
    'docker exec openclaw-openclaw-gateway-1 grep -i "memory" /tmp/openclaw/openclaw-2026-05-26.log | tail -n 50 || true',
    'docker exec openclaw-openclaw-gateway-1 grep -i "openai" /tmp/openclaw/openclaw-2026-05-26.log | grep -v "edit failed" || true'
  ];

  let idx = 0;
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n===== COMMAND: ${cmd} =====`);
    conn.exec(cmd, (err, stream) => {
      if (err) {
        console.log('EXEC ERROR:', err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        console.log(output || '(no output)');
        runNext();
      });
    });
  }
  runNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
