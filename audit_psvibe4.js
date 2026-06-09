const { Client } = require('ssh2');
const fs = require('fs');

function sshExec(command, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let result = '';
    let err = '';
    const timer = setTimeout(() => { conn.end(); reject(new Error('Timeout: ' + command.substring(0,80))); }, timeout);
    conn.on('ready', () => {
      conn.exec(command, (e, stream) => {
        if (e) { clearTimeout(timer); conn.end(); return reject(e); }
        stream.on('data', d => result += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', () => {
          clearTimeout(timer);
          conn.end();
          resolve({ stdout: result, stderr: err });
        });
      });
    });
    conn.on('error', e => { clearTimeout(timer); reject(e); });
    conn.connect({ 
      host: '5.223.81.16', 
      port: 22, 
      username: 'root', 
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') 
    });
  });
}

async function main() {
  const checks = [
    ['ROOT COMPOSE FILE', 'cat /root/docker-compose.yml 2>/dev/null || cat /root/compose.yaml 2>/dev/null'],
    ['N8N COMPOSE', 'cat /root/Aung\\ Chan\\ Myint/docker-compose.yml 2>/dev/null'],
    ['CADDY NETWORK', 'docker inspect root-caddy-1 --format "{{json .NetworkSettings.Networks}}" 2>&1'],
    ['N8N NETWORK', 'docker inspect root-n8n-1 --format "{{json .NetworkSettings.Networks}}" 2>&1'],
    ['TEST CURL WITH HOST HEADER', 'curl -s -H "Host: ps-vibe.com" http://localhost:80/ 2>&1 | head -5'],
    ['HOST.DOCKER.INTERNAL CHECK', 'docker exec root-caddy-1 ping -c1 -W1 host.docker.internal 2>&1 || echo "ping failed"'],
    ['CHECK CADDY EXTRA HOSTS', 'docker inspect root-caddy-1 --format "{{json .HostConfig.ExtraHosts}}" 2>&1'],
    ['CERT FILES IN CADDY', 'docker exec root-caddy-1 ls -la /data/caddy/certificates/ 2>&1; echo "---"; docker exec root-caddy-1 ls -laR /data/caddy/ 2>&1 | head -50'],
    ['ROOT CADDYFILE', 'cat /root/Caddyfile 2>/dev/null'],
    ['PSVIBE REFACTORED BOT', 'ls /root/Aung\\ Chan\\ Myint/Sales-Tele-Bot_refactored/bot/ 2>/dev/null | head -10; echo "---"; cat /root/Aung\\ Chan\\ Myint/Sales-Tele-Bot_refactored/bot/app.py 2>/dev/null | head -30'],
  ];

  for (const [title, cmd] of checks) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`== ${title}`);
    console.log(`${'='.repeat(70)}`);
    try {
      const r = await sshExec(cmd, 15000);
      console.log(r.stdout || '(empty stdout)');
      if (r.stderr) console.log('STDERR:', r.stderr.substring(0, 500));
    } catch(e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
  console.log('\n=== FINAL CHECK COMPLETE ===');
}

main().catch(e => console.error('FATAL:', e));
