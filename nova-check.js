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
  const results = {};
  
  const client = new Client();
  
  // Connect
  await new Promise((resolve, reject) => {
    client.on('ready', resolve);
    client.on('error', (err) => { reject(new Error('SSH connection failed: ' + err.message)); });
    client.connect({
      host: HOST,
      port: 22,
      username: 'root',
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
  
  console.log('✅ SSH connected to ' + HOST);
  
  try {
    // Check 1: Nova container status
    const r1 = await runCommand(client, 'docker ps -a --filter name=oc-nova --format "{{.Names}} | {{.Status}} | {{.Ports}}"');
    results['Container Status'] = r1.stdout || 'NOT FOUND';
    console.log('1) Container:\n   ' + (r1.stdout || 'NOT FOUND'));
    
    // Check 2: Nova volume directory
    const r2 = await runCommand(client, 'ls -la /opt/openclaw/nova/ 2>&1 || echo "DIR_NOT_FOUND"');
    results['Host Directory'] = r2.stdout;
    console.log('2) Host dir /opt/openclaw/nova/:\n' + r2.stdout.split('\n').map(l => '   ' + l).join('\n'));
    
    // Check 3: YYO Wallet Bot
    const r3 = await runCommand(client, 'ls -la /opt/yyo-personal-wallet/ 2>&1 || echo "DIR_NOT_FOUND"');
    results['Wallet Bot Dir'] = r3.stdout;
    console.log('3) YYO Wallet Bot dir:\n' + r3.stdout.split('\n').map(l => '   ' + l).join('\n'));
    
    // Check 4: Wallet Bot service
    const r4 = await runCommand(client, 'systemctl status yyo-personal-wallet 2>&1 | head -20 || echo "NOT_FOUND"');
    results['Wallet Bot Service'] = r4.stdout;
    console.log('4) Wallet service:\n' + r4.stdout.split('\n').map(l => '   ' + l).join('\n'));
    
    // Check 5: Docker compose location
    const r5 = await runCommand(client, 'find /root -name docker-compose.yml -o -name docker-compose.yaml 2>/dev/null | head -5');
    results['Docker Compose Files'] = r5.stdout || 'NOT FOUND';
    console.log('5) Docker compose files:\n   ' + (r5.stdout || 'NOT FOUND'));
    
  } catch (e) {
    console.error('Error:', e.message);
  }
  
  client.end();
  
  // Write results for next steps
  fs.writeFileSync('/home/node/.openclaw/workspace/nova-check-results.json', JSON.stringify(results, null, 2));
  console.log('\n📝 Results saved to nova-check-results.json');
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
