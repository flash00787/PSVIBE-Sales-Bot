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

  // Test wallet_status command (already in allowed list)
  console.log('=== Test wallet_status via host-api ===');
  let r = await runCommand(client, `TOKEN=$(cat /opt/openclaw/nova/host-api-token.txt); curl -s -X POST http://127.0.0.1:7890 -H "Content-Type: application/json" -H "X-API-Token: $TOKEN" -d '{"command":"wallet_status"}' 2>&1`);
  console.log(r.stdout);

  // Test exec command format (to run nova-wallet)
  console.log('\n=== Test exec: nova-wallet status ===');
  r = await runCommand(client, `TOKEN=$(cat /opt/openclaw/nova/host-api-token.txt); curl -s -X POST http://127.0.0.1:7890 -H "Content-Type: application/json" -H "X-API-Token: $TOKEN" -d '{"command":"exec","args":["/usr/local/bin/nova-wallet","status"]}' 2>&1 | head -20`);
  console.log(r.stdout);

  // Now fix host-exec.sh to use correct format
  console.log('\n=== Update host-exec.sh ===');
  r = await runCommand(client, `cat > /opt/openclaw/nova/host-exec.sh << 'SCRIPTEOF'
#!/bin/bash
# Nova Host Exec Bridge
TOKEN=\$(cat /opt/openclaw/nova/host-api-token.txt 2>/dev/null)
# Build JSON args array from all arguments
ARGS_JSON="["
FIRST=true
for arg in "\$@"; do
  if [ "\$FIRST" = true ]; then
    ARGS_JSON="\$ARGS_JSON\\"\$arg\\""
    FIRST=false
  else
    ARGS_JSON="\$ARGS_JSON,\\"\$arg\\""
  fi
done
ARGS_JSON="\$ARGS_JSON]"
curl -s --connect-timeout 10 -X POST http://127.0.0.1:7890 \
    -H "Content-Type: application/json" \
    -H "X-API-Token: \$TOKEN" \
    -d "{\\"command\\":\\"exec\\",\\"args\\":\$ARGS_JSON}"
SCRIPTEOF
chmod +x /opt/openclaw/nova/host-exec.sh`);
  console.log('Updated: ' + (r.code === 0 ? 'OK' : r.stderr));

  // Verify the script
  r = await runCommand(client, 'cat /opt/openclaw/nova/host-exec.sh');
  console.log('\nNew script:');
  console.log(r.stdout);

  // Test the new host-exec.sh
  console.log('\n=== Test new host-exec.sh ===');
  r = await runCommand(client, '/opt/openclaw/nova/host-exec.sh /usr/local/bin/nova-wallet status 2>&1 | head -15');
  console.log(r.stdout);

  // Test from inside Nova container
  console.log('\n=== Test from inside Nova container ===');
  r = await runCommand(client, 'docker exec oc-nova bash /home/node/.openclaw/host-exec.sh /usr/local/bin/nova-wallet status 2>&1 | head -15');
  console.log(r.stdout);

  // Also test quick commands
  console.log('\n=== Test wallet_status from inside container ===');
  let tokenCmd = `TOKEN=$(cat /opt/openclaw/nova/host-api-token.txt)`;
  r = await runCommand(client, `docker exec oc-nova bash -c 'TOKEN=$(cat /home/node/.openclaw/host-api-token.txt); curl -s -X POST http://172.17.0.1:7890 -H "Content-Type: application/json" -H "X-API-Token: $TOKEN" -d "{\\"command\\":\\"wallet_status\\"}"' 2>&1`);
  console.log(r.stdout);

  client.end();
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
