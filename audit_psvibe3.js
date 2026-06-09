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
    ['CADDY DOCKER CONFIG', 'docker exec root-caddy-1 cat /etc/caddy/Caddyfile 2>&1'],
    ['CADDY DOCKER LOGS', 'docker logs root-caddy-1 --tail 30 2>&1'],
    ['CADDY DOCKER INSPECT', 'docker inspect root-caddy-1 --format "{{json .Mounts}}" 2>&1 | python3 -m json.tool 2>/dev/null || docker inspect root-caddy-1 --format "{{json .Mounts}}" 2>&1'],
    ['DOCKER COMPOSE FILE', 'cat /root/docker-compose.yml 2>/dev/null; cat /root/compose.yaml 2>/dev/null; find /root -maxdepth 3 -name "docker-compose*" -o -name "compose.yaml" -o -name "compose.yml" 2>/dev/null'],
    ['TEST CURL FROM HOST TO CADDY', 'curl -sv http://localhost:80/ 2>&1 | head -30'],
    ['TEST CURL HTTPS FROM HOST', 'curl -skv https://localhost/ 2>&1 | head -40'],
    ['CLOUDFLARE CHECK', 'curl -sI --connect-timeout 5 https://ps-vibe.com/ 2>&1; echo "---"; curl -sI --connect-timeout 5 http://ps-vibe.com/ 2>&1'],
    ['API DIRECT CHECK', 'curl -s http://localhost:3000/ 2>&1; echo "---"; curl -s http://localhost:3000/health 2>&1'],
    ['DOCKER NETWORK', 'docker network ls; echo "---"; docker network inspect bridge --format "{{json .Containers}}" 2>&1 | head -50'],
    ['CADDY DOCKER ENV', 'docker inspect root-caddy-1 --format "{{json .Config.Env}}" 2>&1'],
  ];

  for (const [title, cmd] of checks) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`== ${title}`);
    console.log(`${'='.repeat(70)}`);
    try {
      const r = await sshExec(cmd, 20000);
      console.log(r.stdout || '(empty stdout)');
      if (r.stderr) console.log('STDERR:', r.stderr.substring(0, 500));
    } catch(e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
  console.log('\n=== DEEP AUDIT 2 COMPLETE ===');
}

main().catch(e => console.error('FATAL:', e));
