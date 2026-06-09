const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa').toString();

function runCommand(cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', () => resolve({ stdout: stdout.trim(), stderr: stderr.trim() }));
    });
  });
}

conn.on('ready', async () => {
  console.log('=== AUTH PROFILES ===');
  let r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/agents/main/agent/auth-profiles.json 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== AUTH STATE ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/agents/main/agent/auth-state.json 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== MODELS.JSON (key excerpt) ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/agents/main/agent/models.json 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== AGENT CONFIG ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/agent-config.yaml 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== WORKSPACE .ENV ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/workspace/.env 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== RECENT LOGS AFTER RESTART ===');
  r = await runCommand("docker logs oc-nova --tail 50 --since 30m 2>&1");
  console.log(r.stdout);
  console.log('');

  console.log('=== LATEST SESSION FILES ===');
  r = await runCommand('docker exec oc-nova ls -la /home/node/.openclaw/agents/main/sessions/ 2>&1 | tail -15');
  console.log(r.stdout);
  console.log('');

  console.log('=== DELIVERY QUEUE FAILED ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/delivery-queue/failed/a58dea7e-b200-4aab-98fd-a39c33910227.json 2>&1 | head -50');
  console.log(r.stdout);
  console.log('');

  console.log('=== TELEGRAM SPOOL ===');
  r = await runCommand('docker exec oc-nova ls -la /home/node/.openclaw/telegram/ingress-spool-default/ 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== CHECK GATEWAY TOKEN ENV ===');
  r = await runCommand("docker exec oc-nova env 2>&1 | grep -i openclaw | sed 's/=.*/=REDACTED/'");
  console.log(r.stdout);
  console.log('');

  console.log('=== DOCKER COMPOSE (nova section) ===');
  r = await runCommand('cat /root/openclaw/docker-compose.yml 2>&1 | grep -A 30 "nova"');
  console.log(r.stdout);
  console.log('');

  // Check if there are replies going through since restart
  console.log('=== RECENT TELEGRAM ACTIVITY ===');
  r = await runCommand("docker logs oc-nova --tail 500 2>&1 | grep -E 'sendMessage|Inbound|Embedded.*before reply|Embedded.*agent end' | tail -40");
  console.log(r.stdout);
  console.log('');

  conn.end();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
