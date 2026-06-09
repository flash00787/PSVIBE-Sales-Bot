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
  
  // Check docker-compose where Nova is defined
  console.log('=== VPS Docker Compose (nova section) ===');
  const r1 = await runCommand(client, 'cat /root/openclaw/docker-compose.yml');
  console.log(r1.stdout);
  
  console.log('\n=== Nova openclaw.json ===');
  const r2 = await runCommand(client, 'cat /opt/openclaw/nova/openclaw.json');
  console.log(r2.stdout);

  console.log('\n=== Nova yyo-personal-wallet dir contents ===');
  const r3 = await runCommand(client, 'ls -la /opt/openclaw/nova/yyo-personal-wallet/');
  console.log(r3.stdout);

  console.log('\n=== Nova YYO-Personal-Wallet symlink target ===');
  const r4 = await runCommand(client, 'ls -la /opt/openclaw/nova/YYO-Personal-Wallet 2>&1 && ls -la /root/YYO-Personal-Wallet/ 2>&1 | head -20');
  console.log(r4.stdout);

  console.log('\n=== Check if wallet bot dir is mounted in nova container ===');
  const r5 = await runCommand(client, "docker inspect oc-nova --format '{{json .Mounts}}' | python3 -m json.tool 2>/dev/null || docker inspect oc-nova --format '{{json .Mounts}}'");
  console.log(r5.stdout);
  
  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
