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
  
  // How was Nova deployed?
  console.log('=== Nova container inspect (labels, env) ===');
  const r1 = await runCommand(client, "docker inspect oc-nova --format '{{json .Config.Labels}}' | python3 -m json.tool 2>/dev/null");
  console.log(r1.stdout);
  
  console.log('\n=== Nova env vars (API keys check) ===');
  const r2 = await runCommand(client, "docker inspect oc-nova --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'API_KEY|GATEWAY_TOKEN' || echo 'NO_API_KEYS'");
  console.log(r2.stdout);

  console.log('\n=== Check if wallet bot accessible from inside Nova ===');
  const r3 = await runCommand(client, "docker exec oc-nova ls -la /opt/yyo-personal-wallet/ 2>&1 | head -5");
  console.log(r3.stdout);

  console.log('\n=== Check Nova workspace wallet dir ===');
  const r4 = await runCommand(client, "docker exec oc-nova ls -la /home/node/.openclaw/yyo-personal-wallet/ 2>&1 | head -10");
  console.log(r4.stdout);

  console.log('\n=== Nova logs (last 15 lines) ===');
  const r5 = await runCommand(client, "docker logs oc-nova --tail 15 2>&1");
  console.log(r5.stdout);

  console.log('\n=== Find which compose launched Nova ===');
  const r6 = await runCommand(client, "grep -rl 'oc-nova\\|nova:' /root/ --include='*.yml' --include='*.yaml' 2>/dev/null | head -5");
  console.log(r6.stdout);

  console.log('\n=== Check NOVA_README.md ===');
  const r7 = await runCommand(client, "cat /opt/yyo-personal-wallet/NOVA_README.md");
  console.log(r7.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
