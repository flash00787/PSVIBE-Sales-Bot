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
    ['SYSTEM RESOURCES', 'echo "--- DISK ---"; df -h; echo "--- MEMORY ---"; free -h; echo "--- UPTIME ---"; uptime'],
    ['TOP PROCESSES', 'top -bn1 | head -20'],
    ['RUNNING SERVICES', 'systemctl list-units --type=service --state=running | grep -iE "psvibe|ps-vibe|caddy|nginx|n8n|cron|ssh"'],
    ['ALL PSVIBE SERVICE FILES', 'ls -la /etc/systemd/system/ | grep -iE "psvibe|ps-vibe|n8n|caddy"'],
    ['PSVIBE-API SERVICE FILE', 'cat /etc/systemd/system/psvibe-api.service'],
    ['PSVIBE-BOT SERVICE FILE', 'cat /etc/systemd/system/psvibe-bot.service 2>/dev/null; echo "EXIT:$?"'],
    ['PSVIBE-API STATUS', 'systemctl status psvibe-api --no-pager -l'],
    ['PSVIBE-API LOGS', 'journalctl -u psvibe-api --no-pager -n 20'],
    ['CADDY CONFIG', 'cat /etc/caddy/Caddyfile 2>/dev/null; echo "--- CADDY STATUS ---"; systemctl status caddy --no-pager -l 2>/dev/null | head -20'],
    ['CADDY LOGS', 'journalctl -u caddy --no-pager -n 20'],
    ['LISTENING PORTS', 'ss -tlnp'],
    ['FIREWALL UFW', 'ufw status verbose 2>/dev/null || echo "UFW not installed"'],
    ['FIREWALL IPTABLES', 'iptables -L -n --line-numbers 2>/dev/null | head -40 || echo "iptables not available"'],
    ['N8N CHECK', 'systemctl is-active n8n 2>/dev/null; systemctl status n8n --no-pager -l 2>/dev/null | head -15; ss -tln | grep -E "5678|1880" || echo "n8n not on common ports"; ps aux | grep -i n8n | grep -v grep || echo "n8n process not found"'],
    ['DEPLOY TARGET DIRS', 'ls -la /root/psvibe/ 2>/dev/null || echo "/root/psvibe not found"; ls -la /root/staging/ 2>/dev/null || echo "/root/staging not found"; ls -la /opt/psvibe/ 2>/dev/null || echo "/opt/psvibe not found"; find / -maxdepth 3 -type d -iname "*psvibe*" 2>/dev/null'],
    ['ENV FILES PERMISSIONS', 'find /root /opt /home -name ".env" -o -name "*.env" 2>/dev/null | while read f; do ls -la "$f"; done'],
    ['CURL API CHECK', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null || echo "port 3000 unreachable"; echo ""; curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health 2>/dev/null || echo "health endpoint unreachable"'],
    ['CURL HTTPS CHECK', 'curl -s -o /dev/null -w "%{http_code}" https://ps-vibe.com/ 2>/dev/null || echo "HTTPS unreachable"; echo ""; curl -s -o /dev/null -w "%{http_code}" https://ps-vibe.com/api/ 2>/dev/null || echo "API unreachable"'],
    ['CURL HTTP->HTTPS REDIRECT', 'curl -sI -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}" http://ps-vibe.com/ 2>/dev/null || echo "HTTP redirect check failed"'],
    ['PSVIBE-BOT LOGS', 'journalctl -u psvibe-bot --no-pager -n 10 2>/dev/null || echo "No psvibe-bot logs yet"'],
    ['SSL CERT CHECK', 'curl -sIv https://ps-vibe.com/ 2>&1 | head -30'],
    ['CADDY LOGS ERRORS', 'journalctl -u caddy --no-pager -n 50 | grep -iE "error|fail|warn" || echo "No obvious errors"'],
    ['DISK INODES', 'df -i'],
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

  console.log('\n\n=== AUDIT COMPLETE ===');
}

main().catch(e => console.error('FATAL:', e));
