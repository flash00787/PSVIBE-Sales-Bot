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
  console.log('=== CONNECTED TO VPS ===\n');

  // Step 1: Docker container status
  console.log('=== STEP 1: DOCKER CONTAINER STATUS ===');
  let r = await runCommand('docker ps -a | grep -i nova');
  console.log(r.stdout || '(no nova containers found)');
  console.log('');

  // Docker inspect
  console.log('=== DOCKER INSPECT (oc-nova) ===');
  r = await runCommand('docker inspect oc-nova 2>&1 | head -100');
  console.log(r.stdout);
  console.log('');

  // Container logs
  console.log('=== CONTAINER LOGS (last 200 lines) ===');
  r = await runCommand('docker logs oc-nova --tail 200 2>&1');
  console.log(r.stdout);
  console.log('');

  // Container stats
  console.log('=== CONTAINER STATS ===');
  r = await runCommand('docker stats oc-nova --no-stream 2>&1');
  console.log(r.stdout);
  console.log('');

  // Step 2: Find Nova's files
  console.log('=== STEP 2: FIND NOVA FILES ===');
  r = await runCommand('find /root -maxdepth 5 -path "*nova*" -type f 2>/dev/null | head -30');
  console.log(r.stdout || '(none)');
  console.log('');

  // Find openclaw configs
  console.log('=== FIND OPENCLAW CONFIGS ===');
  r = await runCommand('find /root -maxdepth 5 -name "openclaw.json" -type f 2>/dev/null | head -10');
  console.log(r.stdout || '(none)');
  console.log('');

  // Find docker-compose files
  console.log('=== FIND DOCKER-COMPOSE FILES ===');
  r = await runCommand('find /root -maxdepth 4 -name "docker-compose*.yml" -type f 2>/dev/null | head -10');
  console.log(r.stdout || '(none)');
  console.log('');

  // Step 3: List openclaw configs directory
  console.log('=== FIND OPENCLAW DIRS ===');
  r = await runCommand('find /root -maxdepth 6 -type d -name "openclaw" 2>/dev/null | head -10');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check inside container for configs
  console.log('=== CONTAINER: /home/node/.openclaw/ ===');
  r = await runCommand('docker exec oc-nova ls -la /home/node/.openclaw/ 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== CONTAINER: openclaw.json config ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/openclaw.json 2>&1 | head -200');
  console.log(r.stdout);
  console.log('');

  console.log('=== CONTAINER: config.yaml ===');
  r = await runCommand('docker exec oc-nova cat /home/node/.openclaw/config.yaml 2>&1 | head -200');
  console.log(r.stdout);
  console.log('');

  // Step 4: Check gateway logs
  console.log('=== CONTAINER: LOGS DIR ===');
  r = await runCommand('docker exec oc-nova ls -laR /home/node/.openclaw/logs/ 2>&1');
  console.log(r.stdout);
  console.log('');

  console.log('=== CONTAINER: SESSIONS DIR ===');
  r = await runCommand('docker exec oc-nova ls -la /home/node/.openclaw/sessions/ 2>&1 | head -20');
  console.log(r.stdout);
  console.log('');

  console.log('=== CONTAINER: PROCESSES ===');
  r = await runCommand('docker exec oc-nova ps aux 2>&1');
  console.log(r.stdout);
  console.log('');

  // Step 5: Network
  console.log('=== HOST PORTS ===');
  r = await runCommand('ss -tlnp 2>/dev/null | head -30');
  console.log(r.stdout);
  console.log('');

  console.log('=== CONTAINER: TELEGRAM REACHABILITY ===');
  r = await runCommand('docker exec oc-nova curl -sI --connect-timeout 5 https://api.telegram.org 2>&1 | head -10');
  console.log(r.stdout);
  console.log('');

  // Step 6: Error files
  console.log('=== STEP 6: ERROR/CRASH FILES ===');
  r = await runCommand('find /root -maxdepth 6 \( -name "*crash*" -o -name "*error*" \) -type f 2>/dev/null | head -20');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check container's full home dir
  console.log('=== CONTAINER: /home/node/ FULL LISTING ===');
  r = await runCommand('docker exec oc-nova ls -laR /home/node/.openclaw/ 2>&1 | head -100');
  console.log(r.stdout);
  console.log('');

  // Check workspace
  console.log('=== CONTAINER: WORKSPACE ===');
  r = await runCommand('docker exec oc-nova ls -la /home/node/.openclaw/workspace/ 2>&1');
  console.log(r.stdout);
  console.log('');

  // Recent log entries
  console.log('=== CONTAINER: DOCKER LOGS (last 100) ===');
  r = await runCommand('docker logs oc-nova --tail 100 2>&1');
  console.log(r.stdout);
  console.log('');

  // Check for .processing files
  console.log('=== CHECK FOR .processing FILES ===');
  r = await runCommand('docker exec oc-nova find /home/node/.openclaw -name ".processing" -type f 2>&1');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check container uptime
  console.log('=== CONTAINER UPTIME ===');
  r = await runCommand('docker exec oc-nova uptime 2>&1');
  console.log(r.stdout);
  console.log('');

  // Check env vars (sanitized)
  console.log('=== CONTAINER ENV (telegram-related) ===');
  r = await runCommand("docker exec oc-nova env 2>&1 | grep -iE 'telegram|bot|token|channel|tg' | sed 's/=.*/=REDACTED/'");
  console.log(r.stdout || '(none)');
  console.log('');

  // Check if openclaw gateway is actually running
  console.log('=== CHECK OPENCLAW PROCESS ===');
  r = await runCommand("docker exec oc-nova ps aux 2>&1 | grep -i openclaw");
  console.log(r.stdout || '(no openclaw process?)');
  console.log('');

  // Check node_modules for openclaw
  console.log('=== CHECK OPENCLAW BINARY ===');
  r = await runCommand('docker exec oc-nova which openclaw 2>&1; docker exec oc-nova openclaw --version 2>&1');
  console.log(r.stdout);
  console.log('');

  // Check any .env files
  console.log('=== CONTAINER .ENV FILES ===');
  r = await runCommand('docker exec oc-nova find /home/node/.openclaw -name ".env" -type f 2>&1');
  console.log(r.stdout || '(none)');
  console.log('');

  // check for configs dir inside container
  console.log('=== CONTAINER CONFIGS ===');
  r = await runCommand('docker exec oc-nova find /home/node/.openclaw -name "*.json" -type f 2>&1 | head -30');
  console.log(r.stdout);
  console.log('');

  // Container image details
  console.log('=== CONTAINER IMAGE ===');
  r = await runCommand("docker inspect oc-nova --format='{{.Config.Image}} {{.Created}} {{.State.Status}} {{.State.StartedAt}}' 2>&1");
  console.log(r.stdout);
  console.log('');

  // Mount points
  console.log('=== CONTAINER MOUNTS ===');
  r = await runCommand("docker inspect oc-nova --format='{{json .Mounts}}' 2>&1 | python3 -m json.tool 2>/dev/null || docker inspect oc-nova --format='{{json .Mounts}}' 2>&1");
  console.log(r.stdout);
  console.log('');

  conn.end();
  console.log('\n=== AUDIT COMPLETE ===');
});

conn.on('error', (err) => {
  console.error('SSH CONNECTION ERROR:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
