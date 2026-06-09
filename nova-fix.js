const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const HOST = '5.223.81.16';

function runCommand(client, cmd) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout: 30000 }, (err, stream) => {
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

  // STEP 1: Fix the symlink in Nova's workspace
  console.log('=== STEP 1: Fix symlink in Nova workspace ===');
  let r = await runCommand(client, 'rm -f /opt/openclaw/nova/YYO-Personal-Wallet');
  console.log('Removed old symlink: ' + r.stdout);
  
  r = await runCommand(client, 'ls -la /opt/openclaw/nova/YYO-Personal-Wallet 2>&1 || echo "removed"');
  console.log('Verify removed: ' + r.stdout);

  // STEP 2: Update nova.yml to add wallet bot bind mount
  console.log('\n=== STEP 2: Update nova.yml with wallet bot bind mount ===');
  const newNovaYml = `services:
  nova:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: oc-nova
    ports:
      - 3002:3000
    volumes:
      - /opt/openclaw/nova:/home/node/.openclaw
      - /root/YYO-Personal-Wallet:/home/node/.openclaw/YYO-Personal-Wallet:ro
    environment:
      - TZ=Asia/Yangon
      - OPENCLAW_GATEWAY_TOKEN=nova-gateway-token-2026
      - DEEPSEEK_API_KEY=sk-e1079b2bdeb54d76b8e04dad46e71513
      - GEMINI_API_KEY=AIzaSyAI6XE4niET2BTy8E40usnJJEq-zYwGNso
      - GOOGLE_API_KEY=AIzaSyAI6XE4niET2BTy8E40usnJJEq-zYwGNso
      - XAI_API_KEY=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
    labels:
      - agent=Nova
      - description=Nova - Ye Yint Oo agent
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: 3
`;
  
  // Write the new nova.yml
  r = await runCommand(client, `cat > /root/openclaw/nova.yml << 'NOVAEOF'
${newNovaYml}
NOVAEOF`);
  console.log('Wrote nova.yml: ' + (r.code === 0 ? 'OK' : 'ERROR: ' + r.stderr));

  // Verify the file
  r = await runCommand(client, 'cat /root/openclaw/nova.yml');
  console.log('\nNew nova.yml:');
  console.log(r.stdout);

  // STEP 3: Recreate Nova container
  console.log('\n=== STEP 3: Recreate Nova container ===');
  r = await runCommand(client, 'docker compose -f /root/openclaw/nova.yml up -d nova 2>&1');
  console.log('Docker compose up:');
  console.log(r.stdout);
  if (r.stderr) console.log('stderr:', r.stderr);

  // STEP 4: Wait a few seconds and verify
  console.log('\n=== STEP 4: Verify ===');
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  r = await runCommand(client, 'docker ps --filter name=oc-nova --format "{{.Names}} | {{.Status}}"');
  console.log('Container status: ' + r.stdout);

  // STEP 5: Test wallet bot access from inside Nova
  console.log('\n=== STEP 5: Test wallet bot access from inside container ===');
  r = await runCommand(client, 'docker exec oc-nova ls -la /home/node/.openclaw/YYO-Personal-Wallet/bot/ 2>&1 | head -15');
  console.log(r.stdout);

  r = await runCommand(client, 'docker exec oc-nova cat /home/node/.openclaw/YYO-Personal-Wallet/bot/.env 2>&1');
  console.log('\n.env file:');
  console.log(r.stdout);

  r = await runCommand(client, 'docker exec oc-nova cat /home/node/.openclaw/YYO-Personal-Wallet/NOVA_README.md 2>&1');
  console.log('\nNOVA_README.md:');
  console.log(r.stdout);

  client.end();
  console.log('\n✅ Done!');
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
