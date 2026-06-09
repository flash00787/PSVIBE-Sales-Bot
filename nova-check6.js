const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const HOST = '5.223.81.16';

function runCommand(client, cmd) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout: 15000 }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code });
      });
    });
  });
}

async function main() {
  const client = new Client();
  
  await new Promise((resolve, reject) => {
    client.on('ready', resolve);
    client.on('error', (err) => { reject(new Error('SSH connection failed: ' + err.message)); });
    client.connect({
      host: HOST, port: 22, username: 'root',
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
  
  console.log('✅ SSH connected\n');
  
  console.log('=== nova-wallet script ===');
  const r1 = await runCommand(client, 'cat /usr/local/bin/nova-wallet');
  console.log(r1.stdout);

  console.log('\n=== host-api-server.py (check if running) ===');
  const r2 = await runCommand(client, 'ps aux | grep host-api 2>&1; echo "---"; curl -s http://127.0.0.1:7890/health 2>&1 || echo "not running"');
  console.log(r2.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
