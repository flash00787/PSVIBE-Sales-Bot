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
  
  // Check symlink chain
  console.log('=== /root/YYO-Personal-Wallet - is it a symlink? ===');
  const r1 = await runCommand(client, 'ls -la /root/YYO-Personal-Wallet 2>&1 && echo "---" && ls -la /opt/yyo-personal-wallet 2>&1 | head -3');
  console.log(r1.stdout);

  console.log('\n=== nova.yml compose file ===');
  const r2 = await runCommand(client, 'cat /root/openclaw/nova.yml');
  console.log(r2.stdout);

  console.log('\n=== nova-wallet manager from inside container ===');
  const r3 = await runCommand(client, 'docker exec oc-nova ls -la /home/node/.openclaw/YYO-Personal-Wallet/ 2>&1 | head -15');
  console.log(r3.stdout);

  console.log('\n=== Test nova-wallet inside container ===');
  const r4 = await runCommand(client, 'docker exec oc-nova /usr/local/bin/nova-wallet 2>&1 || docker exec oc-nova ls -la /usr/local/bin/nova-wallet 2>&1');
  console.log(r4.stdout);

  console.log('\n=== Check wallet bot .env exists ===');
  const r5 = await runCommand(client, 'ls -la /opt/yyo-personal-wallet/bot/.env 2>&1 && echo "---" && docker exec oc-nova cat /home/node/.openclaw/YYO-Personal-Wallet/bot/.env 2>&1 | head -10');
  console.log(r5.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
