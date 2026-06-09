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

  // Wait for container to be healthy
  console.log('=== Waiting for Nova to be healthy... ===');
  await new Promise(resolve => setTimeout(resolve, 10000));
  
  let r = await runCommand(client, 'docker ps --filter name=oc-nova --format "{{.Names}} | {{.Status}}"');
  console.log('Container: ' + r.stdout);

  // Check Nova logs to ensure it comes up properly
  console.log('\n=== Nova recent logs ===');
  r = await runCommand(client, 'docker logs oc-nova --tail 10 2>&1');
  console.log(r.stdout);

  // Test wallet bot read access
  console.log('\n=== Test: Nova reads wallet bot main.py ===');
  r = await runCommand(client, 'docker exec oc-nova cat /home/node/.openclaw/YYO-Personal-Wallet/bot/main.py 2>&1 | head -20');
  console.log(r.stdout);

  // Test: Check wallet bot status via host-exec
  console.log('\n=== Test: host-exec nova-wallet status ===');
  r = await runCommand(client, 'chmod +x /opt/openclaw/nova/host-exec.sh && /opt/openclaw/nova/host-exec.sh "nova-wallet status" 2>&1 | head -20');
  console.log(r.stdout);

  // Check if API keys are still in place
  console.log('\n=== Verify API keys still set ===');
  r = await runCommand(client, "docker inspect oc-nova --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'API_KEY|GATEWAY_TOKEN'");
  console.log(r.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
