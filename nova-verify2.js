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

  // Check host-api token
  console.log('=== Host API token ===');
  let r = await runCommand(client, 'cat /opt/openclaw/nova/host-api-token.txt');
  console.log('Token present: ' + (r.stdout ? 'YES (' + r.stdout.length + ' chars)' : 'NO'));

  // Test direct curl to host-api
  console.log('\n=== Direct curl test of host-api ===');
  r = await runCommand(client, `TOKEN=$(cat /opt/openclaw/nova/host-api-token.txt); curl -s -X POST http://127.0.0.1:7890 -H "Content-Type: application/json" -H "X-API-Token: $TOKEN" -d '{"cmd":"echo hello"}' 2>&1`);
  console.log(r.stdout);

  // Test nova-wallet from host directly
  console.log('\n=== nova-wallet status (host) ===');
  r = await runCommand(client, '/usr/local/bin/nova-wallet status 2>&1 | head -10');
  console.log(r.stdout);

  // Test nova-wallet via host-api
  console.log('\n=== nova-wallet via host-api ===');
  r = await runCommand(client, `TOKEN=$(cat /opt/openclaw/nova/host-api-token.txt); curl -s -X POST http://127.0.0.1:7890 -H "Content-Type: application/json" -H "X-API-Token: $TOKEN" -d '{"cmd":"nova-wallet status"}' 2>&1 | head -15`);
  console.log(r.stdout);

  // Check host-api-server for allowed commands
  console.log('\n=== host-api-server.py ===');
  r = await runCommand(client, 'cat /opt/openclaw/nova/host-api-server.py');
  console.log(r.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
