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
  
  console.log('=== host-exec.sh ===');
  const r1 = await runCommand(client, 'cat /opt/openclaw/nova/host-exec.sh');
  console.log(r1.stdout);

  console.log('\n=== Check if nova-wallet exists on host ===');
  const r2 = await runCommand(client, 'ls -la /usr/local/bin/nova-wallet 2>&1; which nova-wallet 2>&1');
  console.log(r2.stdout);

  console.log('\n=== Fix symlink ownership ===');
  const r3 = await runCommand(client, 'chown -h 1000:1000 /opt/openclaw/nova/YYO-Personal-Wallet && ls -la /opt/openclaw/nova/YYO-Personal-Wallet');
  console.log(r3.stdout);

  console.log('\n=== Test internal access after chown ===');
  const r4 = await runCommand(client, 'docker exec oc-nova ls -la /home/node/.openclaw/YYO-Personal-Wallet/bot/ 2>&1 | head -15');
  console.log(r4.stdout);

  console.log('\n=== Check if /root/YYO-Personal-Wallet is inside-container-accessible ===');
  const r5 = await runCommand(client, 'docker exec oc-nova ls /root/ 2>&1');
  console.log(r5.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
