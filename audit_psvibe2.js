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
    ['DOCKER CONTAINERS ON 80/443', 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}" | head -20'],
    ['DOCKER PS ALL', 'docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"'],
    ['CADDY INSTALLED?', 'which caddy; dpkg -l | grep caddy; ls -la /etc/caddy/ 2>/dev/null; ls -la /usr/bin/caddy 2>/dev/null'],
    ['CADDY SYSTEMD', 'systemctl list-unit-files | grep caddy; ls -la /etc/systemd/system/caddy* 2>/dev/null; ls -la /lib/systemd/system/caddy* 2>/dev/null'],
    ['CHECK CURL FROM HOST', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ 2>&1; echo ""; curl -s -o /dev/null -w "%{http_code}" http://localhost:443/ 2>&1; echo ""; curl -sk https://localhost/ 2>&1 | head -5'],
    ['WHAT IS ON PORT 80/443?', 'docker inspect $(docker ps -q --filter "publish=80") --format "{{.Name}} {{.Config.Image}}" 2>/dev/null; echo "---"; docker inspect $(docker ps -q --filter "publish=443") --format "{{.Name}} {{.Config.Image}}" 2>/dev/null'],
    ['N8N DOCKER?', 'docker ps --filter "name=n8n" --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"'],
    ['PSVIBE-BOT STAGING', 'ls -la /root/Aung\\ Chan\\ Myint/Sales-Tele-Bot/ 2>/dev/null | head -20; echo "---"; ls -la /root/Aung\\ Chan\\ Myint/Sales-Tele-Bot/bot/ 2>/dev/null | head -20'],
    ['FIND PSVIBE-BOT DIRS', 'find /root -maxdepth 4 -type f -name "main.py" 2>/dev/null | grep -i psvibe; find /root -maxdepth 4 -type f -name "bot.py" 2>/dev/null | grep -i psvibe; ls /root/Aung\\ Chan\\ Myint/Sales-Tele-Bot_refactored/ 2>/dev/null | head -15'],
    ['SWAP CHECK', 'swapon --show; cat /proc/swaps'],
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
  console.log('\n=== DEEP AUDIT COMPLETE ===');
}

main().catch(e => console.error('FATAL:', e));
